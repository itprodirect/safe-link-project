"""URL canonicalization pipeline for evasion-resistant analysis.

Two-phase analysis:
  Phase 1 (structural): checks run on the RAW URL string.
  Phase 2 (semantic):   the URL is normalized, then checks run on the canonical form.

Normalization steps (in order):
  1. Iterative percent-decode (max 5 rounds)
  2. Lowercase scheme and host
  3. Remove default ports (:80 for http, :443 for https)
  4. Resolve hostname (integer/octal/hex/abbreviated IP, localhost, IPv6-mapped IPv4)
  5. Strip trailing dots from hostname
  6. Normalize path (collapse //, resolve /../, remove /./)
  7. Sort query params (for dedup only)

Cross-platform: does NOT use socket.inet_aton (platform-dependent octal behavior).
"""

from __future__ import annotations

import re
from ipaddress import IPv4Address, IPv6Address
from urllib.parse import ParseResult, quote, unquote, urlencode, urlparse

from lsh.core.models import NormalizedURL

_MAX_DECODE_ROUNDS = 5
_DEFAULT_PORTS = {"http": 80, "https": 443}
LOCALHOST_ALIASES = frozenset(
    {
        "localhost",
        "localhost.localdomain",
        "localhost4",
        "localhost6",
        "ip6-localhost",
        "ip6-loopback",
    }
)


# ---------------------------------------------------------------------------
# IP parsing (no socket.inet_aton — deterministic cross-platform)
# ---------------------------------------------------------------------------


def _parse_octet(s: str) -> int | None:
    """Parse a single dotted-quad component respecting 0x (hex) and 0 (octal) prefixes."""
    if not s:
        return None
    try:
        if s.lower().startswith("0x"):
            return int(s, 16)
        if s.startswith("0") and len(s) > 1 and all(c in "01234567" for c in s[1:]):
            return int(s, 8)
        return int(s, 10)
    except ValueError:
        return None


def parse_host_to_ipv4(host: str) -> tuple[IPv4Address | None, list[str]]:
    """Attempt to interpret a hostname as an IPv4 address in any encoding.

    Returns (canonical_ipv4, normalization_notes) or (None, []) if not an IP.

    Handles: standard dotted-decimal, integer form, octal dotted, hex dotted,
    mixed notation, and abbreviated forms (BSD inet_aton behavior).
    """
    notes: list[str] = []
    host = host.strip().strip("[]")
    if not host:
        return None, []

    # --- Case 1: Pure integer (no dots) ---
    if host.isdigit():
        value = int(host)
        if 0 <= value <= 0xFFFFFFFF:
            ip = IPv4Address(value)
            notes.append(f"integer_ip:{host}->{ip}")
            return ip, notes
        return None, []

    # --- Case 2: Hex integer without dots (0x7f000001) ---
    if host.lower().startswith("0x") and "." not in host:
        try:
            value = int(host, 16)
            if 0 <= value <= 0xFFFFFFFF:
                ip = IPv4Address(value)
                notes.append(f"hex_integer_ip:{host}->{ip}")
                return ip, notes
            return None, []
        except ValueError:
            return None, []

    # --- Case 3: Dotted notation (1-4 parts) ---
    parts = host.split(".")
    # Filter trailing empty from "host." (trailing dot)
    if parts and parts[-1] == "":
        parts = parts[:-1]
    if not (1 <= len(parts) <= 4):
        return None, []

    octets: list[int] = []
    notation_types: set[str] = set()
    for part in parts:
        parsed_value = _parse_octet(part)
        if parsed_value is None or parsed_value < 0:
            return None, []  # Not a numeric IP
        octets.append(parsed_value)
        if part.lower().startswith("0x"):
            notation_types.add("hex")
        elif part.startswith("0") and len(part) > 1:
            notation_types.add("octal")
        else:
            notation_types.add("decimal")

    # Expand abbreviated forms per BSD inet_aton:
    #   4 parts: a.b.c.d        each 0-255
    #   3 parts: a.b.c          c can be 0-65535
    #   2 parts: a.b            b can be 0-16777215
    #   1 part:  a              (handled as integer above)
    packed: int
    if len(octets) == 4:
        if any(o > 255 for o in octets):
            return None, []
        packed = (octets[0] << 24) | (octets[1] << 16) | (octets[2] << 8) | octets[3]
    elif len(octets) == 3:
        if octets[0] > 255 or octets[1] > 255 or octets[2] > 65535:
            return None, []
        packed = (octets[0] << 24) | (octets[1] << 16) | octets[2]
    elif len(octets) == 2:
        if octets[0] > 255 or octets[1] > 16777215:
            return None, []
        packed = (octets[0] << 24) | octets[1]
    else:
        packed = octets[0]

    if not (0 <= packed <= 0xFFFFFFFF):
        return None, []

    ip = IPv4Address(packed)
    canonical = str(ip)

    # Detect mixed notation
    if len(notation_types) > 1:
        notes.append(f"mixed_notation:{host}->{canonical}")
    elif "octal" in notation_types:
        notes.append(f"octal_ip:{host}->{canonical}")
    elif "hex" in notation_types:
        notes.append(f"hex_ip:{host}->{canonical}")

    # Detect abbreviated form
    if len(octets) < 4:
        notes.append(f"abbreviated_ip:{host}->{canonical}")

    # If the host differs from canonical but no special notation was flagged,
    # it might still be non-standard
    if not notes and host != canonical:
        notes.append(f"ip_normalized:{host}->{canonical}")

    return ip, notes


def resolve_ipv6_mapped_v4(host: str) -> tuple[IPv4Address | None, list[str]]:
    """Detect and extract IPv4 from IPv6-mapped addresses (::ffff:x.x.x.x)."""
    stripped = host.strip().strip("[]")
    if not stripped:
        return None, []

    try:
        v6 = IPv6Address(stripped)
    except ValueError:
        return None, []

    if v6.ipv4_mapped is not None:
        return v6.ipv4_mapped, [f"ipv6_mapped_v4:{stripped}->{v6.ipv4_mapped}"]

    return None, []


def is_private_or_loopback(ip: IPv4Address) -> bool:
    """Check if IP falls in RFC 1918, loopback, link-local, or other reserved ranges."""
    return bool(
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
    )


# ---------------------------------------------------------------------------
# Percent-decode
# ---------------------------------------------------------------------------


def iterative_percent_decode(value: str, max_rounds: int = _MAX_DECODE_ROUNDS) -> tuple[str, int]:
    """Decode percent-encoded characters iteratively until stable.

    Returns (decoded_value, rounds_used).
    """
    current = value
    for i in range(1, max_rounds + 1):
        decoded = unquote(current)
        if decoded == current:
            return current, i - 1
        current = decoded
    return current, max_rounds


# ---------------------------------------------------------------------------
# Path normalization
# ---------------------------------------------------------------------------


def normalize_path(path: str) -> str:
    """Collapse //, resolve /../, remove /./ in URL paths."""
    if not path:
        return "/"

    # Collapse repeated slashes
    path = re.sub(r"/+", "/", path)

    # Resolve . and ..
    segments = path.split("/")
    resolved: list[str] = []
    for segment in segments:
        if segment == ".":
            continue
        if segment == "..":
            if resolved and resolved[-1] != "":
                resolved.pop()
        else:
            resolved.append(segment)

    result = "/".join(resolved)
    if not result.startswith("/"):
        result = "/" + result
    return result


# ---------------------------------------------------------------------------
# Main normalization pipeline
# ---------------------------------------------------------------------------


def normalize_url(raw: str) -> NormalizedURL:
    """Canonicalize a URL through the full normalization pipeline.

    Returns a NormalizedURL with original, canonical form, and normalization notes.
    """
    notes: list[str] = []

    if not raw or not raw.strip():
        return NormalizedURL(original=raw, canonical=raw)

    # Step 1: Iterative percent-decode
    decoded, rounds = iterative_percent_decode(raw)
    if rounds > 0:
        notes.append(f"percent_decoded_rounds:{rounds}")
    if rounds >= _MAX_DECODE_ROUNDS:
        notes.append("excessive_encoding")

    # Parse URL
    parsed = urlparse(decoded)

    # If no scheme, try prepending http:// for better parsing
    if not parsed.scheme and not decoded.startswith("//"):
        decoded_with_scheme = "http://" + decoded
        parsed = urlparse(decoded_with_scheme)
        notes.append("scheme_added:http")
    elif not parsed.scheme and decoded.startswith("//"):
        decoded_with_scheme = "http:" + decoded
        parsed = urlparse(decoded_with_scheme)
        notes.append("scheme_added:http")

    # Step 2: Lowercase scheme and host
    scheme = parsed.scheme.lower() if parsed.scheme else "http"
    hostname_raw = parsed.hostname or ""
    hostname = hostname_raw.lower()
    original_host = hostname

    # Step 3: Remove default ports
    port = parsed.port
    if port is not None and _DEFAULT_PORTS.get(scheme) == port:
        port = None
        notes.append(f"default_port_removed:{parsed.port}")

    # Step 4: Resolve hostname
    canonical_host = hostname
    ip_notes: list[str] = []

    # 4a-4c: Integer/Octal/Hex/Abbreviated IP
    ipv4, ip_notes = parse_host_to_ipv4(hostname)
    if ipv4 is not None:
        canonical_host = str(ipv4)
        notes.extend(ip_notes)
    else:
        # 4d: Localhost aliases
        if hostname in LOCALHOST_ALIASES:
            canonical_host = "127.0.0.1"
            notes.append(f"localhost_alias:{hostname}")
        else:
            # 4e: IPv6-mapped IPv4
            mapped_v4, v6_notes = resolve_ipv6_mapped_v4(hostname)
            if mapped_v4 is not None:
                canonical_host = str(mapped_v4)
                notes.extend(v6_notes)

    # Step 5: Strip trailing dots
    if canonical_host.endswith("."):
        canonical_host = canonical_host.rstrip(".")
        notes.append("trailing_dot_removed")

    # Step 6: Normalize path
    path = normalize_path(parsed.path)

    # Step 7: Sort query params (for dedup consistency)
    query = parsed.query
    if query:
        try:
            from urllib.parse import parse_qsl
            params = parse_qsl(query, keep_blank_values=True)
            sorted_params = sorted(params)
            query = urlencode(sorted_params, quote_via=quote)
        except Exception:
            pass  # Keep original query if parsing fails

    # Reassemble canonical URL
    netloc = canonical_host
    if port is not None:
        netloc = f"{canonical_host}:{port}"

    # Preserve userinfo if present (important for URL001 detection)
    userinfo = ""
    if parsed.username is not None:
        userinfo = parsed.username
        if parsed.password is not None:
            userinfo += f":{parsed.password}"
        netloc = f"{userinfo}@{netloc}"

    canonical = ParseResult(
        scheme=scheme,
        netloc=netloc,
        path=path,
        params=parsed.params,
        query=query,
        fragment=parsed.fragment,
    ).geturl()

    return NormalizedURL(
        original=raw,
        canonical=canonical,
        original_host=original_host,
        canonical_host=canonical_host,
        normalization_notes=notes,
    )
