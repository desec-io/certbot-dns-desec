"""DNS Authenticator for deSEC."""
import json
import logging

import requests
import zope.interface
from certbot import errors
from certbot import interfaces
from certbot.plugins import dns_common

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@zope.interface.implementer(interfaces.IAuthenticator)
@zope.interface.provider(interfaces.IPluginFactory)
class Authenticator(dns_common.DNSAuthenticator):
    """DNS Authenticator for deSEC

    This Authenticator uses the deSEC REST API to fulfill a dns-01 challenge.
    """

    description = "Obtain certificates using a DNS TXT record (if you are using deSEC.io for DNS)."
    ttl = 3600
    DEFAULT_ENDPOINT = "https://desec.io/api/v1/"

    def __init__(self, *args, **kwargs):
        super(Authenticator, self).__init__(*args, **kwargs)
        self.credentials = None

    @classmethod
    def add_parser_arguments(cls, add):  # pylint: disable=arguments-differ
        super(Authenticator, cls).add_parser_arguments(
            add, default_propagation_seconds=5  # TODO
        )
        add("credentials", help="deSEC credentials INI file.")

    def more_info(self):  # pylint: disable=missing-docstring,no-self-use
        return (
            "This plugin configures a DNS TXT record to respond to a dns-01 challenge using "
            "the deSEC Remote REST API."
        )

    def _setup_credentials(self):
        self.credentials = self._configure_credentials(
            "credentials",
            "deSEC credentials INI file",
            {
                # "endpoint": "URL of the deSEC API.", # TODO add documentation for this
                "token": "Access token for deSEC API.",
            },
        )

    def _perform(self, domain, validation_name, validation):
        logger.debug(f"Authenticator._perform: {domain}, {validation_name}, {validation}")
        subname = validation_name.split(domain)[0].rstrip('.')  # TODO code duplication
        records = self._get_desec_client().get_txt_rrset(domain, subname)
        self._get_desec_client().set_txt_rrset(domain, subname, list(records | {f'"{validation}"'}), self.ttl)

    def _cleanup(self, domain, validation_name, validation):
        logger.debug(f"Authenticator._cleanup: {domain}, {validation_name}, {validation}")
        subname = validation_name.split(domain)[0].rstrip('.')
        records = self._get_desec_client().get_txt_rrset(domain, subname)
        self._get_desec_client().set_txt_rrset(domain, subname, list(records - {f'"{validation}"'}), self.ttl)

    def _get_desec_client(self):
        return _DesecConfigClient(
            self.credentials.conf("endpoint") or self.DEFAULT_ENDPOINT,
            self.credentials.conf("token"),
        )


class _DesecConfigClient(object):
    """
    Encapsulates all communication with the deSEC REST API.
    """

    def __init__(self, endpoint, token):
        logger.debug("creating _DesecConfigClient")
        self.endpoint = endpoint
        self.token = token
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Token {token}"
        self.session.headers["Content-Type"] = "application/json"

    def get_txt_rrset(self, domain, subname):
        response = self.session.get(
            url=f"{self.endpoint}/domains/{domain}/rrsets/{subname}/TXT",
        )

        if response.status_code == 404:
            return set()

        self._check_response_status(response, domain)
        return set(self._response_json(response).get('records', set()))

    def set_txt_rrset(self, domain, subname, rrset, ttl):
        response = self.session.put(
            url=f"{self.endpoint}/domains/{domain}/rrsets/",
            data=json.dumps([
                {"subname": subname, "type": "TXT", "ttl": ttl, "records": rrset},
            ]),
        )
        return self._check_response_status(response, domain)

    def _check_response_status(self, response, domain):
        if 200 <= response.status_code <= 299:
            return
        elif response.status_code in [401, 403]:
            raise errors.PluginError(f"Could not authenticate against deSEC API: {response.content}")
        elif response.status_code == 404:
            raise errors.PluginError(f"Could not find domain '{domain}': {response.content}")
        elif response.status_code == 429:
            raise errors.PluginError(f"deSEC throttled your request. Please run certbot for various domains at "
                                     f"different times. {response.content}")
        elif response.status_code >= 500:
            raise errors.PluginError(f"deSEC API server error (status {response.status_code}): {response.content}")
        else:
            raise errors.PluginError(f"Unknown error when talking to deSEC (status {response.status_code}: "
                                     f"Request was on '{response.request.url}' with payload {response.request.body}. "
                                     f"Response was '{response.content}'.")

    def _response_json(self, response):
        try:
            return response.json()
        except json.JSONDecodeError:
            raise errors.PluginError(f"deSEC API sent non-JSON response (status {response.status_code}): "
                                     f"{response.content}")
