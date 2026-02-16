"""URL structure detector for common non-Unicode phishing tricks."""

from __future__ import annotations

import re
from urllib.parse import parse_qsl

from lsh.core.allowlist import should_suppress_for_allowlist
from lsh.core.models import AnalysisInput, Confidence, Evidence, Finding, ModuleInterface, Severity
from lsh.core.rules import DECEPTIVE_PREFIX_HINTS, KNOWN_BRAND_TOKENS, NESTED_URL_PARAM_KEYS
from lsh.core.url_tools import normalize_hostname, parse_url_like, registrable_domain

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_PATTERN.findall(text.lower()))


def _parse_nested_url_value(value: str) -> tuple[str, str] | None:
    parsed = parse_url_like(value)
    hostname = parsed.hostname
    if hostname is None:
        return None

    if parsed.scheme not in {"http", "https"} and not value.startswith("//"):
        return None

    normalized_host = normalize_hostname(hostname)
    return normalized_host, registrable_domain(normalized_host)


class URLStructureDetector(ModuleInterface):
    """Detect deceptive URL structure patterns in netloc/query components."""

    @property
    def name(self) -> str:
        return "url_structure"

    @property
    def version(self) -> str:
        return "0.1.0"

    def analyze(self, input: AnalysisInput) -> list[Finding]:
        if input.input_type != "url":
            return []

        parsed = parse_url_like(input.content)
        raw_hostname = parsed.hostname
        if raw_hostname is None:
            return []

        hostname = normalize_hostname(raw_hostname)
        if should_suppress_for_allowlist(input, hostname, category_prefix="URL"):
            return []

        registrable = registrable_domain(hostname)
        host_labels = [label for label in hostname.split(".") if label]
        registrable_labels = [label for label in registrable.split(".") if label]

        findings: list[Finding] = []
        cumulative_risk = 0

        def add_finding(
            *,
            code: str,
            risk_delta: int,
            confidence: Confidence,
            title: str,
            explanation: str,
            family_explanation: str,
            extra_evidence: list[Evidence],
            recommendations: list[str],
        ) -> None:
            nonlocal cumulative_risk
            cumulative_risk = min(100, cumulative_risk + risk_delta)
            findings.append(
                Finding(
                    module=self.name,
                    category=code,
                    severity=Severity.INFO,
                    confidence=confidence,
                    risk_score=cumulative_risk,
                    title=title,
                    explanation=explanation,
                    family_explanation=family_explanation,
                    evidence=[
                        Evidence(label="Hostname", value=hostname),
                        Evidence(label="Registrable Domain", value=registrable),
                        Evidence(label="Risk Delta", value=f"+{risk_delta}"),
                        Evidence(label="Cumulative Risk", value=str(cumulative_risk)),
                        *extra_evidence,
                    ],
                    recommendations=recommendations,
                )
            )

        if parsed.username is not None or parsed.password is not None:
            displayed_target = parsed.netloc.rsplit("@", maxsplit=1)[0]
            add_finding(
                code="URL001_USERINFO_PRESENT",
                risk_delta=40,
                confidence=Confidence.HIGH,
                title="URL contains hidden userinfo before '@'",
                explanation=(
                    "The URL contains userinfo (`user:pass@host`) before the actual host. "
                    "Attackers use this to make links look like trusted domains."
                ),
                family_explanation=(
                    "This link hides extra text before '@'. The real destination is after '@'."
                ),
                extra_evidence=[
                    Evidence(label="Displayed Before @", value=displayed_target),
                    Evidence(label="True Host", value=hostname),
                ],
                recommendations=[
                    "Ignore text before '@' and verify the real host after it.",
                    "Avoid signing in through links that contain '@' in the domain section.",
                ],
            )

        if len(host_labels) > len(registrable_labels):
            prefix_labels = host_labels[: len(host_labels) - len(registrable_labels)]
            prefix_tokens = set().union(*(_tokens(label) for label in prefix_labels))
            brand_tokens = sorted(prefix_tokens & KNOWN_BRAND_TOKENS)
            registrable_tokens = _tokens(registrable_labels[0]) if registrable_labels else set()
            unmatched_brands = [token for token in brand_tokens if token not in registrable_tokens]

            if unmatched_brands:
                risk_delta = 30
                if prefix_tokens & DECEPTIVE_PREFIX_HINTS:
                    risk_delta += 5

                add_finding(
                    code="URL002_DECEPTIVE_SUBDOMAIN",
                    risk_delta=risk_delta,
                    confidence=Confidence.MEDIUM,
                    title="Subdomain includes trusted-looking brand tokens",
                    explanation=(
                        "The host prefix contains brand-like tokens, but the registrable domain "
                        "is different. This is a common deceptive-subdomain pattern."
                    ),
                    family_explanation=(
                        "The beginning of this web address looks trusted, but the real site name "
                        "at the end is different."
                    ),
                    extra_evidence=[
                        Evidence(label="Prefix Labels", value=".".join(prefix_labels)),
                        Evidence(label="Brand-like Tokens", value=", ".join(unmatched_brands)),
                    ],
                    recommendations=[
                        "Focus on the final site name before the top-level domain.",
                        "Use trusted bookmarks for brand logins and payments.",
                    ],
                )

        best_nested_signal: tuple[int, str, str, str, str] | None = None
        for key, value in parse_qsl(parsed.query, keep_blank_values=False):
            nested = _parse_nested_url_value(value)
            if nested is None:
                continue

            nested_host, nested_registrable = nested
            risk_delta = 20 if key.lower() in NESTED_URL_PARAM_KEYS else 15
            if nested_registrable != registrable:
                risk_delta += 10

            candidate = (risk_delta, key, value, nested_host, nested_registrable)
            if best_nested_signal is None or candidate[0] > best_nested_signal[0]:
                best_nested_signal = candidate

        if best_nested_signal is not None:
            risk_delta, key, value, nested_host, nested_registrable = best_nested_signal
            confidence = (
                Confidence.MEDIUM if nested_registrable != registrable else Confidence.LOW
            )
            add_finding(
                code="URL003_NESTED_URL_PARAMETER",
                risk_delta=risk_delta,
                confidence=confidence,
                title="Query parameter contains another full URL",
                explanation=(
                    "The URL query includes a nested destination URL, which can indicate "
                    "redirect-style link wrapping or open-redirect abuse."
                ),
                family_explanation=(
                    "This link contains another link hidden inside it, which can be used to "
                    "bounce you to a different site."
                ),
                extra_evidence=[
                    Evidence(label="Parameter", value=key),
                    Evidence(label="Nested URL", value=value),
                    Evidence(label="Nested Host", value=nested_host),
                    Evidence(label="Nested Registrable Domain", value=nested_registrable),
                ],
                recommendations=[
                    "Check where the nested link points before continuing.",
                    "For sensitive actions, open the destination site directly.",
                ],
            )

        return findings
