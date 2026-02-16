"""Redirect chain detector with strict opt-in network behavior."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin

import requests  # type: ignore[import-untyped]

from lsh.core.models import AnalysisInput, Confidence, Evidence, Finding, ModuleInterface, Severity
from lsh.core.url_tools import extract_hostname, parse_url_like, registrable_domain

_REDIRECT_STATUSES = {301, 302, 303, 307, 308}
_DEFAULT_MAX_HOPS = 5
_DEFAULT_TIMEOUT_SECONDS = 3.0
_MAX_HOPS_HARD_CAP = 15
_USER_AGENT = "LinkSafetyHub/0.1 (+https://github.com/itprodirect/safe-link-project)"


def _network_enabled(input: AnalysisInput) -> bool:
    raw = input.metadata.get("network_enabled", False)
    return bool(raw)


def _max_hops(input: AnalysisInput) -> int:
    raw = input.metadata.get("network_max_hops", _DEFAULT_MAX_HOPS)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return _DEFAULT_MAX_HOPS
    return min(max(value, 1), _MAX_HOPS_HARD_CAP)


def _timeout_seconds(input: AnalysisInput) -> float:
    raw = input.metadata.get("network_timeout", _DEFAULT_TIMEOUT_SECONDS)
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return _DEFAULT_TIMEOUT_SECONDS
    return max(value, 0.1)


def _network_start_url(input: AnalysisInput) -> str | None:
    parsed = parse_url_like(input.content)
    if parsed.hostname is None or parsed.scheme not in {"http", "https"}:
        return None
    return input.content


@dataclass(slots=True)
class _RedirectTrace:
    chain: list[str]
    max_hops_reached: bool = False
    timeout: bool = False
    request_error: str | None = None
    non_http_target: str | None = None
    loop_target: str | None = None


class RedirectChainDetector(ModuleInterface):
    """Analyze redirect behavior using explicit opt-in network calls."""

    @property
    def name(self) -> str:
        return "redirect"

    @property
    def version(self) -> str:
        return "0.1.0"

    def analyze(self, input: AnalysisInput) -> list[Finding]:
        if input.input_type != "url":
            return []
        if not _network_enabled(input):
            return []

        start_url = _network_start_url(input)
        if start_url is None:
            return [
                Finding(
                    module=self.name,
                    category="RED000_NETWORK_URL_REQUIRED",
                    severity=Severity.INFO,
                    confidence=Confidence.HIGH,
                    risk_score=10,
                    title="Network redirect checks require an explicit http(s) URL",
                    explanation=(
                        "Redirect analysis was requested, but the input is not a full http(s) URL. "
                        "Offline checks still ran."
                    ),
                    family_explanation=(
                        "To test redirects, use a full web link that starts with http:// or https://."
                    ),
                    evidence=[Evidence(label="Input", value=input.content)],
                    recommendations=[
                        "Retry with a full URL format, for example https://example.com.",
                    ],
                )
            ]

        trace = self._trace_redirects(
            start_url=start_url,
            max_hops=_max_hops(input),
            timeout_seconds=_timeout_seconds(input),
        )
        return self._build_findings(trace)

    def _trace_redirects(
        self,
        *,
        start_url: str,
        max_hops: int,
        timeout_seconds: float,
    ) -> _RedirectTrace:
        chain = [start_url]
        seen = {start_url}
        current_url = start_url
        trace = _RedirectTrace(chain=chain)

        session = requests.Session()
        try:
            for _ in range(max_hops):
                try:
                    response = session.head(
                        current_url,
                        allow_redirects=False,
                        timeout=timeout_seconds,
                        headers={"User-Agent": _USER_AGENT},
                    )
                except requests.Timeout:
                    trace.timeout = True
                    break
                except requests.RequestException as exc:
                    trace.request_error = str(exc)
                    break

                location = response.headers.get("Location")
                if response.status_code not in _REDIRECT_STATUSES or not location:
                    break

                next_url = urljoin(current_url, location)
                parsed_next = parse_url_like(next_url)
                if parsed_next.hostname is None or parsed_next.scheme not in {"http", "https"}:
                    trace.non_http_target = next_url
                    break

                if next_url in seen:
                    trace.loop_target = next_url
                    trace.chain.append(next_url)
                    break

                trace.chain.append(next_url)
                seen.add(next_url)
                current_url = next_url
            else:
                trace.max_hops_reached = True
        finally:
            session.close()

        return trace

    def _build_findings(self, trace: _RedirectTrace) -> list[Finding]:
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
                        Evidence(label="Redirect Hops", value=str(max(len(trace.chain) - 1, 0))),
                        Evidence(label="Chain", value=" -> ".join(trace.chain)),
                        Evidence(label="Risk Delta", value=f"+{risk_delta}"),
                        Evidence(label="Cumulative Risk", value=str(cumulative_risk)),
                        *extra_evidence,
                    ],
                    recommendations=recommendations,
                )
            )

        if len(trace.chain) >= 2:
            add_finding(
                code="RED001_REDIRECT_CHAIN_PRESENT",
                risk_delta=15,
                confidence=Confidence.LOW,
                title="URL redirects before reaching a final destination",
                explanation=(
                    "This URL redirects through one or more intermediate locations. "
                    "Redirect chains are common but can obscure the real destination."
                ),
                family_explanation=(
                    "This link bounces through another address before it finishes loading."
                ),
                extra_evidence=[
                    Evidence(label="Start URL", value=trace.chain[0]),
                    Evidence(label="Final URL", value=trace.chain[-1]),
                ],
                recommendations=[
                    "Check the final destination before signing in or entering payment details.",
                ],
            )

            registrable_path: list[str] = []
            for url in trace.chain:
                hostname = extract_hostname(url)
                if hostname is None:
                    continue
                registrable_path.append(registrable_domain(hostname))
            unique_registrable_domains = {domain for domain in registrable_path if domain}
            if len(unique_registrable_domains) >= 2:
                add_finding(
                    code="RED002_CROSS_DOMAIN_REDIRECT",
                    risk_delta=25,
                    confidence=Confidence.MEDIUM,
                    title="Redirect chain changes registrable domain",
                    explanation=(
                        "The redirect chain moves across different registrable domains. "
                        "Cross-domain jumps increase destination uncertainty."
                    ),
                    family_explanation=(
                        "This link starts on one site name and ends on a different site name."
                    ),
                    extra_evidence=[
                        Evidence(
                            label="Domain Path",
                            value=" -> ".join(registrable_path),
                        )
                    ],
                    recommendations=[
                        "Verify that the final site name is expected and trusted.",
                    ],
                )

        if trace.max_hops_reached:
            add_finding(
                code="RED003_MAX_HOPS_REACHED",
                risk_delta=35,
                confidence=Confidence.HIGH,
                title="Redirect hop safety limit reached",
                explanation=(
                    "Redirect analysis hit the configured maximum hop limit before completion."
                ),
                family_explanation=(
                    "This link redirected too many times to analyze safely."
                ),
                extra_evidence=[],
                recommendations=[
                    "Do not proceed unless you can verify the final destination independently.",
                ],
            )

        if trace.loop_target is not None:
            add_finding(
                code="RED004_REDIRECT_LOOP_DETECTED",
                risk_delta=30,
                confidence=Confidence.HIGH,
                title="Redirect loop detected",
                explanation=(
                    "The redirect chain revisited a previously seen URL, indicating a loop."
                ),
                family_explanation=(
                    "This link appears to loop between addresses instead of resolving normally."
                ),
                extra_evidence=[Evidence(label="Loop Target", value=trace.loop_target)],
                recommendations=[
                    "Avoid links that loop; open the destination directly from a trusted source.",
                ],
            )

        if trace.timeout:
            add_finding(
                code="RED005_REQUEST_TIMEOUT",
                risk_delta=30,
                confidence=Confidence.MEDIUM,
                title="Redirect check timed out",
                explanation=(
                    "Network redirect analysis timed out before completion."
                ),
                family_explanation=(
                    "This link took too long to resolve, so checks are incomplete."
                ),
                extra_evidence=[],
                recommendations=[
                    "Treat unresolved links cautiously and verify before opening.",
                ],
            )

        if trace.request_error is not None:
            add_finding(
                code="RED006_REQUEST_ERROR",
                risk_delta=20,
                confidence=Confidence.LOW,
                title="Redirect check encountered a network error",
                explanation=(
                    "A network error interrupted redirect analysis."
                ),
                family_explanation=(
                    "The redirect check could not finish because of a network error."
                ),
                extra_evidence=[Evidence(label="Error", value=trace.request_error[:180])],
                recommendations=[
                    "Retry later or verify the destination through a trusted source.",
                ],
            )

        if trace.non_http_target is not None:
            add_finding(
                code="RED007_NON_HTTP_REDIRECT_TARGET",
                risk_delta=30,
                confidence=Confidence.MEDIUM,
                title="Redirect target is not http(s)",
                explanation=(
                    "A redirect attempted to move to a non-http(s) target."
                ),
                family_explanation=(
                    "This link tried to redirect to a non-standard destination."
                ),
                extra_evidence=[Evidence(label="Redirect Target", value=trace.non_http_target)],
                recommendations=[
                    "Avoid redirects to non-standard destinations unless explicitly expected.",
                ],
            )

        return findings
