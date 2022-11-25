"""DNS Authenticator for deSEC."""
import json
import logging
import time

import requests
from certbot import interfaces
try:
    # needed for compatibility with older certbots, see #13
    import zope.interface
    zope_interface_implementer = zope.interface.implementer
    zope_interface_provider = zope.interface.provider
    i_authenticator = interfaces.IAuthenticator
    i_plugin_factory = interfaces.IPluginFactory
except ImportError:
    def get_noop_dec(*args):
        def noop_dec(obj):
            return obj
        return noop_dec
    zope_interface_implementer = zope_interface_provider = get_noop_dec
    i_authenticator = i_plugin_factory = None

from certbot import errors
from certbot.plugins import dns_common

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@zope_interface_implementer(i_authenticator)  # needed for compatibility with older certbots, see #13
@zope_interface_provider(i_plugin_factory)  # needed for compatibility with older certbots, see #13
class Authenticator(dns_common.DNSAuthenticator):
    """DNS Authenticator for deSEC

    This Authenticator uses the deSEC REST API to fulfill a dns-01 challenge.
    """

    description = "Obtain certificates using a DNS TXT record (if you are using deSEC.io for DNS)."
    DEFAULT_ENDPOINT = "https://desec.io/api/v1"

    def __init__(self, *args, **kwargs):
        super(Authenticator, self).__init__(*args, **kwargs)
        self.credentials = None

    @classmethod
    def add_parser_arguments(cls, add):  # pylint: disable=arguments-differ
        super(Authenticator, cls).add_parser_arguments(
            add, default_propagation_seconds=80  # TODO decrease after deSEC fixed their NOTIFY problem
        )
        add("credentials", help="deSEC credentials INI file.")

    def more_info(self):  # pylint: disable=missing-docstring,no-self-use
        return (
            "This plugin configures a DNS TXT record to respond to a dns-01 challenge using "
            "the deSEC Remote REST API."
        )

    def _setup_credentials(self):
        self.credentials = self._configure_credentials(
            key="credentials",
            label="deSEC credentials INI file",
            required_variables={
                "token": "Access token for deSEC API.",
            },
        )

    def _desec_work(self, domain, validation_name, validation, set_operator):
        client = self._get_desec_client()
        zone = client.get_authoritative_zone(validation_name)
        subname = validation_name.rsplit(zone['name'], 1)[0].rstrip('.')
        records = client.get_txt_rrset(zone, subname)
        logger.debug(f"Current TXT records: {records}")
        records = set_operator(records, {f'"{validation}"'})
        logger.debug(f"Setting TXT records: {records}")
        client.set_txt_rrset(zone, subname, records)

    def _perform(self, domain, validation_name, validation):
        logger.debug(f"Authenticator._perform: {domain}, {validation_name}, {validation}")
        self._desec_work(domain, validation_name, validation, set.union)

    def _cleanup(self, domain, validation_name, validation):
        logger.debug(f"Authenticator._cleanup: {domain}, {validation_name}, {validation}")
        self._desec_work(domain, validation_name, validation, set.difference)

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
        self.endpoint = endpoint.rstrip('/')
        self.token = token
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Token {token}"
        self.session.headers["Content-Type"] = "application/json"

    @staticmethod
    def desec_request(method, **kwargs):
        for _ in range(3):
            response: requests.Response = method(**kwargs)
            if response.status_code == 429 and 'Retry-After' in response.headers:
                try:
                    cooldown = int(response.headers['Retry-After'])
                except ValueError:
                    return response
                logger.debug(f"deSEC API limit reached. Retrying request after {cooldown}s.")
                time.sleep(cooldown)
            else:
                return response
        return response

    def desec_get(self, **kwargs):
        return self.desec_request(self.session.get, **kwargs)

    def desec_put(self, **kwargs):
        return self.desec_request(self.session.put, **kwargs)

    def get_authoritative_zone(self, qname):
        response = self.desec_get(url=f"{self.endpoint}/domains/?owns_qname={qname}")
        self._check_response_status(response)
        data = self._response_json(response)
        try:
            return data[0]
        except IndexError:
            raise errors.PluginError(f"Could not find suitable domain in your account (did you create it?): {qname}")

    def get_txt_rrset(self, zone, subname):
        domain = zone['name']
        response = self.desec_get(
            url=f"{self.endpoint}/domains/{domain}/rrsets/{subname}/TXT/",
        )

        if response.status_code == 404:
            return set()

        self._check_response_status(response, domain=domain)
        return set(self._response_json(response).get('records', set()))

    def set_txt_rrset(self, zone, subname, records: set):
        domain = zone['name']
        response = self.desec_put(
            url=f"{self.endpoint}/domains/{domain}/rrsets/",
            data=json.dumps([
                {"subname": subname, "type": "TXT", "ttl": zone['minimum_ttl'], "records": list(records)},
            ]),
        )
        return self._check_response_status(response, domain=domain)

    def _check_response_status(self, response, **kwargs):
        if 200 <= response.status_code <= 299:
            return
        elif response.status_code in [401, 403]:
            raise errors.PluginError(f"Could not authenticate against deSEC API: {response.content}")
        elif response.status_code == 404:
            raise errors.PluginError(f"Not found ({kwargs}): {response.content}")
        elif response.status_code == 429:
            raise errors.PluginError(f"deSEC throttled your request even after we waited the prescribed cool-down "
                                     f"time. Did you use the API in parallel? {response.content}")
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
