#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dynamic DNS Updater

Simple script that checks to see if the public URL has changed, and if it has,
POSTs to a given URL.

Uses https://api.ipify.org to check public IP.

Updates DNS for domain-dns.com; no idea if it works for other DNS hosts.
"""

import logging
from logging import debug, error, info, warning
from os import getenv
from pathlib import Path
import random
import sys
from time import sleep

import requests

DEFAULT_CACHE_FILE = ".public_ip.txt"
DEFAULT_DDNS_UPDATE_URL = "http://domain-dns.com/ip.cgi"
__version__ = "1.1.0"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
)


def read_public_ip(cache_file=None):
    ip = requests.get("https://api.ipify.org").text
    info("public ip address of %s" % ip)
    if cache_file is None:
        cache_file = getenv("DDNS_CACHE_FILE", DEFAULT_CACHE_FILE)
        cache_file = (Path.cwd() / cache_file).resolve()
    if cache_file:
        cache_file.write_text(ip)
    return ip


def read_cached_public_ip(cache_file=None):
    if cache_file is None:
        cache_file = getenv("DDNS_CACHE_FILE", DEFAULT_CACHE_FILE)
        cache_file = (Path.cwd() / cache_file).resolve()

    if cache_file.exists():
        ip = cache_file.read_text()
        info("cached ip address of %s" % ip)
        return ip
    else:
        info("no cached ip address")
        return None


def update_public_ip(base_url=None, domain_name=None, key=None, ip=None):
    if base_url is None:
        base_url = getenv("DDNS_UPDATE_URL")
    if base_url is None:
        warning("No base url provided. Set 'DDNS_UPDATE_URL' environmental variable")
        sys.exit(1)

    if domain_name is None:
        domain_name = getenv("DDNS_DOMAIN_NAME")
    if domain_name is None:
        warning(
            "No domain name provided. Set 'DDNS_DOMAIN_NAME' environmental variable."
        )
        sys.exit(1)

    if key is None:
        key = getenv("DDNS_KEY")
    if key is None:
        warning("No API key provided. Set 'DDNS_KEY' environmental variable.")
        sys.exit(1)

    payload = {
        "host": domain_name,
        "key": key,
    }
    # if IP isn't provided, the ip address this is called from will be used
    # automatically on the backend
    if ip is not None:
        payload["ip"] = ip

    r = requests.get(base_url, params=payload)

    if r.status_code == requests.codes.ok:
        info("Successfully updated public ip address for %s!" % domain_name)
        return
    else:
        warning("Unsuccessful in updating public ip address for %s" % domain_name)
        warning("Return code %s" % r.status_code)
        return


def check_config():
    debug("Configuration is:")
    cache_file = getenv("DDNS_CACHE_FILE")
    if cache_file:
        debug(f"DDNS_CACHE_FILE={cache_file}")
    else:
        debug(f"DDNS_CACHE_FILE not set, using default: {DEFAULT_CACHE_FILE}")

    update_url = getenv("DDNS_UPDATE_URL")
    if update_url:
        debug(f"DDNS_UPDATE_URL={update_url}")
    else:
        debug(f"DDNS_UPDATE_URL not set, using default: {DEFAULT_DDNS_UPDATE_URL}")

    domain_name = getenv("DDNS_DOMAIN_NAME")
    if domain_name:
        debug(f"DDNS_DOMAIN_NAME={domain_name}")
    else:
        error("No domain name provided. Set 'DDNS_DOMAIN_NAME' environmental variable.")

    api_key = getenv("DDNS_KEY")
    if api_key:
        debug(f"DDNS_KEY set!")
    else:
        error("No API key provided. Set 'DDNS_KEY' environmental variable.")


def main_loop(endless=False, cache_file=None, sleep_sec=5 * 60):
    info("DDNS updater, version %s" % __version__)

    check_config()

    if cache_file is None:
        cache_file = getenv("DDNS_CACHE_FILE", DEFAULT_CACHE_FILE)
    cache_file = (Path.cwd() / cache_file).resolve()
    info("Using cache file: %s" % cache_file)

    while True:
        former_ip = read_cached_public_ip(cache_file=cache_file)
        public_ip = read_public_ip(cache_file=cache_file)

        if public_ip != former_ip:
            update_public_ip()
        else:
            info("Public IP unchanged, not updating...")

        if endless is False:
            info("Exiting program...")
            break

        sleep_time = random.randrange(sleep_sec * 0.9, sleep_sec * 1.1)
        info("Sleeping for %s seconds" % sleep_time)
        sleep(sleep_time)


if __name__ == "__main__":
    main_loop(endless=True)
