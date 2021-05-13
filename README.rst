certbot-dns-desec
=================

deSEC_ DNS Authenticator plugin for Certbot

This plugin automates the process of completing a ``dns-01`` challenge by
creating, and subsequently removing, TXT records using the deSEC DNS API.

Configuration of deSEC
----------------------

Log in at deSEC_ and create the domain you would like to use and a token for DNS management.

.. _deSEC: https://desec.io/
.. _certbot: https://certbot.eff.org/

Installation
------------

::

    pip install certbot-dns-desec


Named Arguments
---------------

To start using DNS authentication for deSEC, pass the following arguments on
certbot's command line:

============================================================= ==============================================
``--authenticator dns-desec``                                 select the authenticator plugin (Required)

``--dns-desec-credentials``                                   deSEC API token
                                                              INI file. (Required)

``--dns-desec-propagation-seconds``                           | waiting time for DNS to propagate before asking
                                                              | the ACME server to verify the DNS record.
                                                              | (Default: 5, Recommended: >= 600)  # TODO
============================================================= ==============================================

(Note that the verbose and seemingly redundant ``certbot-dns-desec:`` prefix
is currently imposed by certbot for external plugins.)


Credentials
-----------

An example ``credentials.ini`` file:

.. code-block:: ini

   certbot_dns_desec:dns_desec_token    = token
   certbot_dns_desec:dns_desec_endpoint = https://localhost:8080/remote/json.php

The path to this file can be provided interactively or using the
``--certbot-dns-desec:dns-desec-credentials`` command-line argument. Certbot
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


Examples
--------

To acquire a single certificate for both ``example.com`` and
``*.example.com``, waiting 900 seconds for DNS propagation:  # TODO waiting time

.. code-block:: bash

   certbot certonly \
     --authenticator certbot-dns-desec:dns-desec \
     --certbot-dns-desec:dns-desec-credentials /etc/letsencrypt/.secrets/domain.tld.ini \
     --certbot-dns-desec:dns-desec-propagation-seconds 900 \
     --server https://acme-v02.api.letsencrypt.org/directory \
     --agree-tos \
     --rsa-key-size 4096 \
     -d 'example.com' \
     -d '*.example.com'


Docker
------

In order to create a docker container with a certbot-dns-desec installation,
create an empty directory with the following ``Dockerfile``:

.. code-block:: docker

    FROM certbot/certbot
    RUN pip install certbot-dns-desec

Proceed to build the image::

    docker build -t certbot/dns-desec .

Once that's finished, the application can be run as follows::

    docker run --rm \
       -v /var/lib/letsencrypt:/var/lib/letsencrypt \
       -v /etc/letsencrypt:/etc/letsencrypt \
       --cap-drop=all \
       certbot/dns-desec certonly \
       --authenticator dns-desec \
       --dns-desec-propagation-seconds 900 \
       --dns-desec-credentials \
           /etc/letsencrypt/.secrets/domain.tld.ini \
       --no-self-upgrade \
       --keep-until-expiring --non-interactive --expand \
       --server https://acme-v02.api.letsencrypt.org/directory \
       -d example.com -d '*.example.com'

It is suggested to secure the folder as follows::
chown root:root /etc/letsencrypt/.secrets
chmod 600 /etc/letsencrypt/.secrets

Development and Testing
-----------------------

To test this, install the virtual environment (venv) for this repository. Register a domain `$DOMAIN` with desec.io.
# TODO token, desec-secrets.ini
Inside the venv, run::

    python3 -m pip install .
    TOKEN=...
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


Maintainer: Prepare New Release
-------------------------------

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
1. Publish using `python3 -m publish nils-wisiol certbot-dns-desec`
