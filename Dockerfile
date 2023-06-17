ARG FROM_IMAGE=certbot/certbot:amd64-v2.6.0

#Base
FROM ${FROM_IMAGE}

# Install the DNS plugin
COPY . /app
WORKDIR /app
RUN set -ex && \
    pip install -r requirements.txt && \
    pip install .

RUN rm -rf /app

#RUN pip install certbot-dns-desec
