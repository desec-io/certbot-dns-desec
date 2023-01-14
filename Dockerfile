ARG  FROM_IMAGE=certbot/certbot:amd64-v2.1.1

#Base
FROM ${FROM_IMAGE}

# Install the DNS plugin
RUN pip install certbot-dns-desec
