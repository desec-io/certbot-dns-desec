ARG  FROM_IMAGE=certbot/certbot:arm32v6-v2.1.1
#Base
FROM ${FROM_IMAGE}

# Install the DNS plugin
RUN pip install certbot-dns-desec==1.2.1
