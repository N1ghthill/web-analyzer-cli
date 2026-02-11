"""URL validation helpers to reduce SSRF risk for public web checks."""

from __future__ import annotations

import ipaddress
import socket
from typing import List, Optional, Union
from urllib.parse import urlparse

from .analyzer import normalize_url

BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "metadata.google.internal",
    "metadata",
}

BLOCKED_IPV4_STRINGS = {
    "0.0.0.0",
    "127.0.0.1",
    "169.254.169.254",  # cloud metadata services
}


IPAddress = Union[ipaddress.IPv4Address, ipaddress.IPv6Address]


def _is_blocked_ip(ip: IPAddress) -> bool:
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def _resolve_host_ips(hostname: str) -> List[IPAddress]:
    try:
        records = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return []

    ips: List[IPAddress] = []

    for record in records:
        raw_ip = record[4][0]
        try:
            ips.append(ipaddress.ip_address(raw_ip))
        except ValueError:
            continue

    return ips


def _validate_host(hostname: str) -> None:
    host = hostname.strip().lower()

    if not host:
        raise ValueError("URL host is required")

    if host in BLOCKED_HOSTNAMES:
        raise ValueError("Local/internal hosts are not allowed")

    if host.endswith(".local"):
        raise ValueError("Local network domains are not allowed")

    if host in BLOCKED_IPV4_STRINGS:
        raise ValueError("Blocked host")

    parsed_ip: Optional[IPAddress] = None
    try:
        parsed_ip = ipaddress.ip_address(host)
    except ValueError:
        parsed_ip = None

    if parsed_ip:
        if _is_blocked_ip(parsed_ip):
            raise ValueError("Private/internal IP addresses are not allowed")
        return

    resolved_ips = _resolve_host_ips(host)
    if not resolved_ips:
        raise ValueError("Could not resolve host")

    for ip in resolved_ips:
        if _is_blocked_ip(ip):
            raise ValueError("Host resolves to private/internal IP")


def validate_public_url(raw_url: str) -> str:
    """Validate URL and ensure it targets a public web host."""
    url = normalize_url(raw_url)
    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only http and https URLs are allowed")

    if parsed.username or parsed.password:
        raise ValueError("URLs with embedded credentials are not allowed")

    if not parsed.hostname:
        raise ValueError("Invalid URL")

    _validate_host(parsed.hostname)
    return url
