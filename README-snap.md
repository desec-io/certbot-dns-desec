# Selfmade certbot-dns-desec  snap

The Certbot snap supports the x86_64, ARMv7, and ARMv8 architectures. The Certbot team strongly recommend that most users should install Certbot through the snap.

That is the reason why building support for snap was added.

## Building

Install Ubuntu Desktop 20.04.5 LTS (Focal Fossa) on bare metal or in a virtual machine then...

```shell
sudo apt update
sudo apt full-upgrade
sudo apt -f install
sudo systemctl reboot
sudo snap install snapcraft --classic
git clone https://github.com/desec-io/certbot-dns-desec.git
cd certbot-dns-desec/
snapcraft --debug
```

After some time and if nothing went wrong the result will be certbot-dns-desec_1.2.0_amd64.snap.

## Installation

On a Debian GNU/Linux 11 (Server) you will be able to install your own snap like this:

```shell
sudo snap install certbot-dns-desec_1.2.0_amd64.snap --dangerous --devmode
sudo snap set certbot trust-plugin-with-root=ok
sudo snap connect certbot:plugin certbot-dns-desec
sudo snap connect certbot-dns-desec:certbot-metadata certbot:certbot-metadata
certbot plugins
```

If you see desec in the output the installation was successful.

## Usage

Read the  ![README](https://github.com/desec-io/certbot-dns-desec/blob/main/README.md#request-certificate).

# Official snap package

After some testing it would be a good idea to provide an official snap package via ![Build from GitHub](https://snapcraft.io/docs/build-from-github) in the future!?