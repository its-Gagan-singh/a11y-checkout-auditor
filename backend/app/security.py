"""Basic SSRF protection: refuse to audit localhost / private-network addresses
unless ALLOW_PRIVATE_URLS=1 (useful only for local development)."""
import ipaddress
import os
import socket
from urllib.parse import urlparse


def is_public_url(url: str) -> bool:
    if os.getenv("ALLOW_PRIVATE_URLS") == "1":
        return True
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return False
    try:
        infos = socket.getaddrinfo(parsed.hostname, None)
    except socket.gaierror:
        return False
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            return False
    return True
