from setuptools import setup
from setuptools import find_packages

version = "0.2.2"

install_requires = [
    "acme>=0.29.0",
    "certbot>=0.34.0",
    "setuptools",
    "requests",
    "mock",
    "requests-mock",
]

# read the contents of your README file
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md")) as f:
    long_description = f.read()

setup(
    name="certbot-dns-desec",
    version=version,
    description="deSEC DNS Authenticator plugin for Certbot",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/desec-io/certbot-dns-desec",
    author="Nils Wisiol",
    author_email="nils@desec.io",
    license="Apache License 2.0",
    python_requires=">=3.7",
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    entry_points={
        "certbot.plugins": [
            "dns-desec = certbot_dns_desec.dns_desec:Authenticator"
        ]
    },
    test_suite="certbot_dns_desec",
)
