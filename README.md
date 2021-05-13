# certbot-dns-desec

![main branch CI test status](https://github.com/desec-io/certbot-dns-desec/workflows/Tests/badge.svg?branch=main)
[![pypi badge](https://img.shields.io/pypi/v/certbot-dns-desec.svg)](https://pypi.org/project/certbot-dns-desec/)

⚠ This plugin is under development, API and CLI might change! ⚠

[deSEC](https://desec.io/) DNS Authenticator plugin for [Certbot](https://certbot.eff.org/)

This plugin automates the process of completing a ``dns-01`` challenge by
creating, and subsequently removing, TXT records using the deSEC DNS API.

## Configuration of deSEC

Log in at [deSEC](https://desec.io/) and create the domain you would like to use and a token for DNS management.

## Installation

This certbot plugin can be installed using `pip`:

    python3 -m pip install certbot-dns-desec


## Command Line Interface

To start using DNS authentication with deSEC, pass the following arguments on
certbot's command line:

1. ``--authenticator dns-desec`` Selects the authenticator plugin.
1. ``--dns-desec-credentials <file>`` Specifies the file holding the deSEC API credentials (required, see below).
1. ``--dns-desec-propagation-seconds`` Waiting time for DNS to propagate before asking the ACME server to verify the
    DNS record (default 5).


## deSEC API Credentials

An example ``credentials.ini`` file:

    dns_desec_token = token

Additionally, the URL of the deSEC API can be specified using the `dns_desec_endpoint` configuration option.
`https://desec.io/api/v1/` is the default.

The path to this file can be provided interactively or using the
``--dns-desec-credentials`` command-line argument. Certbot
records the path to this file for use during renewal, but does not store the
file's contents.

**CAUTION:** You should protect these API token as you would the
password to your deSEC account. Users who can read this file can use these
credentials to issue API calls on your behalf. Users who can cause
Certbot to run using these credentials can complete a ``dns-01`` challenge to
acquire new certificates or revoke existing certificates for associated
domains, even if those domains aren't being managed by this server.

Certbot will emit a warning if it detects that the credentials file can be
accessed by other users on your system. The warning reads "Unsafe permissions
on credentials configuration file", followed by the path to the credentials
file. This warning will be emitted each time Certbot uses the credentials file,
including for renewal, and cannot be silenced except by addressing the issue
(e.g., by using a command like ``chmod 600`` to restrict access to the file).


## Example Usage

To acquire a single certificate for both ``example.com`` and ``*.example.com``:

    certbot certonly \
         --authenticator dns-desec \
         --dns-desec-credentials /etc/letsencrypt/.secrets/domain.tld.ini \
         --server https://acme-v02.api.letsencrypt.org/directory \
         --agree-tos \
         --rsa-key-size 4096 \
         -d 'example.com' \
         -d '*.example.com'


## Development and Testing

To test this, install the virtual environment (venv) for this repository and activate it.
Register a domain `$DOMAIN` with desec.io, and obtain a DNS management token `$TOKEN`. Then run

    python3 -m pip install .
    TOKEN=token-you-obtained-from-desec-io
    DOMAIN=domain-you-registered-at-desec-io
    EMAIL=youremail@example.com
    echo "dns_desec_token = $TOKEN" > desec-secret.ini
    chmod 600 desec-secret.ini
    certbot \
        --config-dir tmp/certbot/config \
        --logs-dir tmp/certbot/logs \
        --work-dir tmp/certbot/work \
        --test-cert \
        -d $DOMAIN -d "*.$DOMAIN" \
        --authenticator dns-desec \
        --dns-desec-credentials desec-secret.ini \
        --non-interactive --agree-tos \
        --email $EMAIL \
        certonly


## Maintenance: Prepare New Release

1. Make sure tests are okay (see GitHub actions)
1. Commit all changes
1. Clean up `dist/` folder
1. Set up new release version: `RELEASE=x.y.z`
1. Update version to `x.y.z` in `setup.py`
1. Commit with message "Release Version vx.y.z": `git commit -p -m "Release Version v$RELEASE"`
1. Tag commit using `git tag -as v$RELEASE -m "Release Version v$RELEASE"`
1. Push
    1. branch: `git push`
    1. tag: `git push origin v$RELEASE`
1. Set environment variables `GITHUB_TOKEN` to a GitHub token, `TWINE_USERNAME` and `TWINE_PASSWORD` to PyPi
    credentials.
1. Publish using `python3 -m publish desec-io certbot-dns-desec`
