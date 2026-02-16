"""IP literal detector for URL hostnames."""

from __future__ import annotations

from lsh.core.models import AnalysisInput, Confidence, Evidence, Finding, ModuleInterface, Severity
from lsh.core.url_tools import IPAddress, extract_hostname, parse_ip_literal


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
    """Classify IP literal hostnames as private/internal or public."""

    @property
    def name(self) -> str:
        return "net_ip"

    @property
    def version(self) -> str:
        return "0.1.0"

    def analyze(self, input: AnalysisInput) -> list[Finding]:
        if input.input_type != "url":
            return []

        hostname = extract_hostname(input.content)
        if hostname is None:
            return []

        parsed_ip = parse_ip_literal(hostname)
        if parsed_ip is None:
            return []

        if _is_private_scope(parsed_ip):
            return [
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
            ]

        return [
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
                    "This link uses a raw internet address number, not a normal website name."
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
        ]
