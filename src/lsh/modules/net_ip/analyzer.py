"""IP literal detector for URL hostnames.

Detects standard IP literals (NET001/NET002) and obfuscated encodings
(NET003 integer/octal/hex/abbreviated, NET004 localhost aliases,
NET005 IPv6-mapped IPv4, NET006 mixed notation).
"""

from __future__ import annotations

from lsh.core.allowlist import should_suppress_finding_for_allowlist
from lsh.core.context import url_context_for_input
from lsh.core.models import AnalysisInput, Confidence, Evidence, Finding, ModuleInterface, Severity
from lsh.core.normalizer import (
    LOCALHOST_ALIASES,
    is_private_or_loopback,
    parse_host_to_ipv4,
    resolve_ipv6_mapped_v4,
)
from lsh.core.url_tools import IPAddress, normalize_hostname, parse_ip_literal


def _is_private_scope(address: IPAddress) -> bool:
    """Return True for private/internal-style addresses."""
    return (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_reserved
        or address.is_unspecified
    )


class NetIPDetector(ModuleInterface):
    """Classify IP literal hostnames as private/internal or public.

    Also detects obfuscated IP encodings, localhost aliases, IPv6-mapped IPv4,
    and mixed notation.
    """

    @property
    def name(self) -> str:
        return "net_ip"

    @property
    def version(self) -> str:
        return "0.2.0"

    @property
    def supported_input_types(self) -> frozenset[str]:
        return frozenset({"url"})

    def analyze(self, input: AnalysisInput) -> list[Finding]:
        if input.input_type != "url":
            return []

        url_context = url_context_for_input(input)
        if url_context is None or url_context.hostname is None:
            return []
        hostname = url_context.hostname

        findings: list[Finding] = []

        def add_finding(candidate: Finding) -> None:
            if should_suppress_finding_for_allowlist(
                input,
                hostname,
                module_name=self.name,
                category_prefix="NET",
                finding_code=candidate.category,
            ):
                return
            findings.append(candidate)

        # --- Check for localhost aliases (NET004) ---
        normalized_host = normalize_hostname(hostname)
        if normalized_host in LOCALHOST_ALIASES:
            add_finding(
                Finding(
                    module=self.name,
                    category="NET004_LOCALHOST_ALIAS",
                    severity=Severity.LOW,
                    confidence=Confidence.HIGH,
                    risk_score=30,
                    title="URL points to a localhost alias",
                    explanation=(
                        f"The hostname '{normalized_host}' is a well-known alias for "
                        "the local machine (127.0.0.1). This could be used for SSRF "
                        "or local service exploitation."
                    ),
                    family_explanation=(
                        "This link points to your own computer, not a real website. "
                        "It should not appear in links shared online."
                    ),
                    evidence=[
                        Evidence(label="Hostname", value=normalized_host),
                        Evidence(label="Resolves To", value="127.0.0.1"),
                    ],
                    recommendations=[
                        "Do not follow localhost links from external sources.",
                        "For public websites, expect a normal domain name.",
                    ],
                )
            )
            return findings

        # --- Check for IPv6-mapped IPv4 (NET005) ---
        mapped_v4 = url_context.ipv6_mapped_ipv4
        if mapped_v4 is None:
            mapped_v4, _v6_notes = resolve_ipv6_mapped_v4(normalized_host)
        if mapped_v4 is not None:
            add_finding(
                Finding(
                    module=self.name,
                    category="NET005_IPV6_MAPPED_V4",
                    severity=Severity.LOW,
                    confidence=Confidence.HIGH,
                    risk_score=35,
                    title="URL uses IPv6-mapped IPv4 address",
                    explanation=(
                        f"The hostname wraps an IPv4 address ({mapped_v4}) inside "
                        "IPv6 notation (::ffff:...). This obscures the real destination."
                    ),
                    family_explanation=(
                        "This link uses a technical trick to hide the real address. "
                        "Normal websites don't do this."
                    ),
                    evidence=[
                        Evidence(label="Original Host", value=normalized_host),
                        Evidence(label="Mapped IPv4", value=str(mapped_v4)),
                        Evidence(label="Is Private", value=str(is_private_or_loopback(mapped_v4))),
                    ],
                    recommendations=[
                        "Treat IPv6-wrapped addresses with extra caution.",
                        "Use trusted bookmarks for sensitive logins.",
                    ],
                )
            )
            if is_private_or_loopback(mapped_v4):
                add_finding(
                    Finding(
                        module=self.name,
                        category="NET001_PRIVATE_IP_LITERAL",
                        severity=Severity.INFO,
                        confidence=Confidence.HIGH,
                        risk_score=30,
                        title="Mapped IPv4 address is private/local",
                        explanation=(
                            f"The underlying IPv4 address {mapped_v4} is in "
                            "private/loopback space."
                        ),
                        family_explanation=(
                            "The hidden address points to a local/internal network, "
                            "not a real website."
                        ),
                        evidence=[
                            Evidence(label="IPv4", value=str(mapped_v4)),
                            Evidence(label="Scope", value="private/local"),
                        ],
                        recommendations=[
                            "Only continue if you expected an internal network link.",
                        ],
                    )
                )
            return findings

        # --- Check standard IP literal (existing NET001/NET002) ---
        parsed_ip = url_context.ip_literal or parse_ip_literal(hostname)
        if parsed_ip is not None:
            if _is_private_scope(parsed_ip):
                add_finding(
                    Finding(
                        module=self.name,
                        category="NET001_PRIVATE_IP_LITERAL",
                        severity=Severity.INFO,
                        confidence=Confidence.LOW,
                        risk_score=20,
                        title="URL uses a private or local IP address",
                        explanation=(
                            "The hostname is an IP literal in private/internal space "
                            "(or loopback/link-local/reserved range)."
                        ),
                        family_explanation=(
                            "This link points to a local/internal address "
                            "instead of a normal website name."
                        ),
                        evidence=[
                            Evidence(label="Hostname", value=hostname),
                            Evidence(label="IP Version", value=str(parsed_ip.version)),
                            Evidence(label="Scope", value="private/local"),
                        ],
                        recommendations=[
                            "Only continue if you expected an internal network link.",
                            "For public websites, prefer links that use a normal domain name.",
                        ],
                    )
                )
            else:
                add_finding(
                    Finding(
                        module=self.name,
                        category="NET002_PUBLIC_IP_LITERAL",
                        severity=Severity.INFO,
                        confidence=Confidence.MEDIUM,
                        risk_score=25,
                        title="URL uses a public IP address instead of a domain",
                        explanation=(
                            "The hostname is a public IP literal. "
                            "Phishing links often use raw IPs to avoid recognizable domains."
                        ),
                        family_explanation=(
                            "This link uses a raw internet address number, "
                            "not a normal website name."
                        ),
                        evidence=[
                            Evidence(label="Hostname", value=hostname),
                            Evidence(label="IP Version", value=str(parsed_ip.version)),
                            Evidence(label="Scope", value="public"),
                        ],
                        recommendations=[
                            "Treat raw-IP links with extra caution.",
                            "Use trusted bookmarks for logins and payments.",
                        ],
                    )
                )
            return findings

        # --- Check for obfuscated IP (NET003) via normalizer ---
        ipv4 = url_context.obfuscated_ipv4
        ip_notes = list(url_context.obfuscated_ipv4_notes)
        if ipv4 is None:
            ipv4, ip_notes = parse_host_to_ipv4(normalized_host)
        if ipv4 is not None:
            canonical = str(ipv4)
            # Detect mixed notation (NET006)
            has_mixed = any("mixed_notation" in n for n in ip_notes)
            if has_mixed:
                add_finding(
                    Finding(
                        module=self.name,
                        category="NET006_MIXED_NOTATION",
                        severity=Severity.LOW,
                        confidence=Confidence.HIGH,
                        risk_score=40,
                        title="IP address uses mixed hex/octal/decimal notation",
                        explanation=(
                            f"The hostname '{normalized_host}' mixes different number "
                            f"bases (hex/octal/decimal) to represent {canonical}. "
                            "This is a deliberate obfuscation technique."
                        ),
                        family_explanation=(
                            "This link uses a tricky mix of number formats to hide "
                            "the real address. Normal websites never do this."
                        ),
                        evidence=[
                            Evidence(label="Original Host", value=normalized_host),
                            Evidence(label="Canonical IP", value=canonical),
                            Evidence(label="Technique", value="mixed notation"),
                        ],
                        recommendations=[
                            "Do not trust links that use unusual number formats.",
                            "Verify the destination through a trusted channel.",
                        ],
                    )
                )

            # Main obfuscated IP finding (NET003)
            add_finding(
                Finding(
                    module=self.name,
                    category="NET003_OBFUSCATED_IP",
                    severity=Severity.LOW,
                    confidence=Confidence.HIGH,
                    risk_score=45,
                    title="URL uses an obfuscated IP address",
                    explanation=(
                        f"The hostname '{normalized_host}' encodes IP address "
                        f"{canonical} using non-standard notation "
                        "(integer, octal, hex, or abbreviated form). "
                        "No legitimate website uses this."
                    ),
                    family_explanation=(
                        "This link hides its real address using a number trick. "
                        "Real websites use normal names like 'google.com'."
                    ),
                    evidence=[
                        Evidence(label="Original Host", value=normalized_host),
                        Evidence(label="Canonical IP", value=canonical),
                        Evidence(
                            label="Is Private",
                            value=str(is_private_or_loopback(ipv4)),
                        ),
                    ],
                    recommendations=[
                        "Do not click links that encode IP addresses in unusual ways.",
                        "Use trusted bookmarks for sensitive logins.",
                    ],
                )
            )

            # If the decoded IP is private, also flag NET001
            if is_private_or_loopback(ipv4):
                add_finding(
                    Finding(
                        module=self.name,
                        category="NET001_PRIVATE_IP_LITERAL",
                        severity=Severity.INFO,
                        confidence=Confidence.HIGH,
                        risk_score=30,
                        title="Obfuscated IP resolves to private/local address",
                        explanation=(
                            f"The decoded IP {canonical} is in private/loopback space."
                        ),
                        family_explanation=(
                            "The hidden address points to a local/internal network, "
                            "not a real website."
                        ),
                        evidence=[
                            Evidence(label="IPv4", value=canonical),
                            Evidence(label="Scope", value="private/local"),
                        ],
                        recommendations=[
                            "Only continue if you expected an internal network link.",
                        ],
                    )
                )

        return findings
