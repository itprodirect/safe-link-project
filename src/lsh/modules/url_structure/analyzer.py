"""URL structure detector for common non-Unicode phishing tricks."""

from __future__ import annotations

import re
from urllib.parse import parse_qsl

from lsh.core.allowlist import should_suppress_for_allowlist
from lsh.core.context import url_context_for_input
from lsh.core.models import AnalysisInput, Confidence, Evidence, Finding, ModuleInterface, Severity
from lsh.core.normalizer import iterative_percent_decode
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
        return "0.2.0"

    def analyze(self, input: AnalysisInput) -> list[Finding]:
        if input.input_type != "url":
            return []

        url_context = url_context_for_input(input)
        if url_context is None or url_context.hostname is None:
            return []
        parsed = url_context.raw_parsed
        hostname = url_context.hostname
        if should_suppress_for_allowlist(input, hostname, category_prefix="URL"):
            return []

        registrable = url_context.registrable_domain or registrable_domain(hostname)
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
                risk_delta=55,
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

        # --- URL004: Fragment deception ---
        fragment = parsed.fragment
        if fragment:
            fragment_finding = self._check_fragment_deception(
                fragment, hostname, cumulative_risk
            )
            if fragment_finding is not None:
                findings.append(fragment_finding)
                cumulative_risk = fragment_finding.risk_score

        # --- URL005: Excessive / suspicious percent-encoding ---
        _decoded_url, decode_rounds = iterative_percent_decode(input.content)
        encoding_signals: list[str] = []

        if decode_rounds >= 2:
            encoding_signals.append(f"double-encoding ({decode_rounds} rounds)")
        if re.search(r"%[0-9a-fA-F]{2}", parsed.netloc or ""):
            encoding_signals.append("encoded hostname")
        if re.search(r"%2[eE]%2[eE]|%2[eE]\.|\.%2[eE]", input.content):
            encoding_signals.append("encoded path traversal")

        if encoding_signals:
            risk_delta = 15 + 5 * len(encoding_signals)
            add_finding(
                code="URL005_EXCESSIVE_ENCODING",
                risk_delta=risk_delta,
                confidence=Confidence.MEDIUM,
                title="URL uses suspicious percent-encoding",
                explanation=(
                    f"Encoding signals detected: {', '.join(encoding_signals)}. "
                    "Legitimate URLs rarely encode hostnames, use path traversal, "
                    "or require multiple decode rounds."
                ),
                family_explanation=(
                    "This link is scrambled in a way that normal websites "
                    "don't use. It may be trying to hide something."
                ),
                extra_evidence=[
                    Evidence(label="Decode Rounds", value=str(decode_rounds)),
                    Evidence(label="Signals", value=", ".join(encoding_signals)),
                ],
                recommendations=[
                    "Avoid links that appear excessively encoded.",
                    "Verify the destination through a trusted channel.",
                ],
            )

        return findings

    def _check_fragment_deception(
        self,
        fragment: str,
        hostname: str,
        cumulative_risk: int,
    ) -> Finding | None:
        """Detect fragments designed to make the URL look like a different destination."""
        # Check for @ in fragment mimicking userinfo of a "real" domain
        if "@" in fragment:
            pseudo_domain = fragment.split("@", 1)[1].split("/")[0].split("?")[0]
            pseudo_tokens = _tokens(pseudo_domain)
            brand_matches = sorted(pseudo_tokens & KNOWN_BRAND_TOKENS)
            if brand_matches:
                risk = min(100, cumulative_risk + 30)
                return Finding(
                    module=self.name,
                    category="URL004_FRAGMENT_DECEPTION",
                    severity=Severity.INFO,
                    confidence=Confidence.MEDIUM,
                    risk_score=risk,
                    title="Fragment mimics a trusted domain with '@'",
                    explanation=(
                        f"The URL fragment contains '@{pseudo_domain}', which may "
                        "trick users into thinking this links to a trusted site. "
                        "Browsers ignore the fragment for navigation."
                    ),
                    family_explanation=(
                        "The end of this link makes it look like it goes to a "
                        f"trusted site ({', '.join(brand_matches)}), but that part "
                        "is just decoration — the real destination is different."
                    ),
                    evidence=[
                        Evidence(label="Hostname", value=hostname),
                        Evidence(label="Fragment", value=fragment),
                        Evidence(label="Pseudo Domain", value=pseudo_domain),
                        Evidence(label="Brand Matches", value=", ".join(brand_matches)),
                    ],
                    recommendations=[
                        "Ignore everything after '#' in a URL.",
                        "Verify the real host before the '#' sign.",
                    ],
                )

        # Check for fragment that looks like a full URL
        if fragment.startswith("http://") or fragment.startswith("https://"):
            risk = min(100, cumulative_risk + 25)
            return Finding(
                module=self.name,
                category="URL004_FRAGMENT_DECEPTION",
                severity=Severity.INFO,
                confidence=Confidence.MEDIUM,
                risk_score=risk,
                title="Fragment contains a full URL",
                explanation=(
                    "The URL fragment contains a full URL, likely an attempt to "
                    "disguise the real destination. Browsers ignore everything "
                    "after '#' for navigation."
                ),
                family_explanation=(
                    "This link has another web address hidden after a '#' sign. "
                    "That hidden part is just for show — the real destination is different."
                ),
                evidence=[
                    Evidence(label="Hostname", value=hostname),
                    Evidence(label="Fragment URL", value=fragment),
                ],
                recommendations=[
                    "Ignore everything after '#' in a URL.",
                    "Verify the real host before the '#' sign.",
                ],
            )

        return None
