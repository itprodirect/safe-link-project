"""Shared URL parsing helpers for offline URL analysis modules."""

from __future__ import annotations

import ipaddress
from urllib.parse import ParseResult, urlparse

from lsh.core.rules import COMMON_MULTI_PART_SUFFIXES

IPAddress = ipaddress.IPv4Address | ipaddress.IPv6Address


def parse_url_like(raw: str) -> ParseResult:
    """Parse URL-like input and support bare hostnames as fallback."""
    parsed = urlparse(raw)
    if parsed.hostname is None:
        prefixed = raw if raw.startswith("//") else f"//{raw}"
        parsed = urlparse(prefixed)
    return parsed


def normalize_hostname(hostname: str) -> str:
    """Normalize hostnames for comparisons."""
    return hostname.strip().rstrip(".").lower()


def extract_hostname(raw: str) -> str | None:
    """Extract normalized hostname from URL-like input."""
    hostname = parse_url_like(raw).hostname
    if hostname is None:
        return None
    normalized = normalize_hostname(hostname)
    return normalized or None


def parse_ip_literal(hostname: str) -> IPAddress | None:
    """Return parsed IP address when hostname is an IP literal."""
    try:
        return ipaddress.ip_address(normalize_hostname(hostname))
    except ValueError:
        return None


def is_ip_literal(hostname: str) -> bool:
    """Return True when hostname is an IPv4/IPv6 literal."""
    return parse_ip_literal(hostname) is not None


def registrable_domain(hostname: str) -> str:
    """Best-effort registrable-domain extraction using offline heuristics."""
    host = normalize_hostname(hostname)
    labels = [label for label in host.split(".") if label]
    if len(labels) <= 2:
        return host

    suffix = ".".join(labels[-2:])
    if suffix in COMMON_MULTI_PART_SUFFIXES and len(labels) >= 3:
        return ".".join(labels[-3:])
    return ".".join(labels[-2:])


def registrable_labels(hostname: str) -> list[str]:
    """Split registrable domain into labels."""
    return [label for label in registrable_domain(hostname).split(".") if label]

