"""Email authentication header analyzer (SPF/DKIM/DMARC)."""

from __future__ import annotations

import re
from email import policy
from email.parser import HeaderParser

from lsh.core.models import AnalysisInput, Confidence, Evidence, Finding, ModuleInterface, Severity

_AUTH_RESULT_PATTERN = re.compile(r"\b(spf|dkim|dmarc)=([a-z0-9_-]+)", re.IGNORECASE)
_RECEIVED_SPF_PATTERN = re.compile(r"^\s*([a-z0-9_-]+)", re.IGNORECASE)

_FAIL_STATUSES = frozenset({"fail", "permerror", "temperror", "policy"})
_WEAK_STATUSES = frozenset({"none", "neutral", "softfail"})
_PASS_ALIASES = {"bestguesspass": "pass"}
_STATUS_RANK = {
    "pass": 0,
    "none": 1,
    "neutral": 1,
    "softfail": 1,
    "temperror": 2,
    "permerror": 2,
    "policy": 2,
    "fail": 2,
}


def _normalize_status(status: str) -> str:
    normalized = status.strip().lower()
    return _PASS_ALIASES.get(normalized, normalized)


def _pick_worst_status(current: str | None, candidate: str) -> str:
    normalized = _normalize_status(candidate)
    if current is None:
        return normalized

    current_rank = _STATUS_RANK.get(current, 1)
    candidate_rank = _STATUS_RANK.get(normalized, 1)
    if candidate_rank >= current_rank:
        return normalized
    return current


def _is_fail(status: str) -> bool:
    return status in _FAIL_STATUSES


def _is_weak_or_missing(status: str) -> bool:
    return status == "missing" or status in _WEAK_STATUSES


def _statuses_from_auth_results_header(header_value: str) -> dict[str, str | None]:
    """Extract per-protocol statuses from one Authentication-Results header."""
    statuses: dict[str, str | None] = {"spf": None, "dkim": None, "dmarc": None}
    for match in _AUTH_RESULT_PATTERN.finditer(header_value):
        protocol = match.group(1).lower()
        raw_status = match.group(2).lower()
        statuses[protocol] = _pick_worst_status(statuses[protocol], raw_status)
    return statuses


def _first_received_spf_status(received_spf_values: list[str]) -> str | None:
    """Return SPF status from the first parseable Received-SPF header."""
    for header_value in received_spf_values:
        spf_match = _RECEIVED_SPF_PATTERN.search(header_value)
        if spf_match is None:
            continue
        return _normalize_status(spf_match.group(1).lower())
    return None


def _nearest_auth_statuses(
    auth_results_values: list[str],
    received_spf_values: list[str],
) -> dict[str, str]:
    """Select statuses from nearest auth headers to reduce multi-hop false positives."""
    selected: dict[str, str | None] = {"spf": None, "dkim": None, "dmarc": None}
    for header_value in auth_results_values:
        parsed_statuses = _statuses_from_auth_results_header(header_value)
        for protocol, status in parsed_statuses.items():
            if selected[protocol] is None and status is not None:
                selected[protocol] = status
        if all(status is not None for status in selected.values()):
            break

    if selected["spf"] is None:
        selected["spf"] = _first_received_spf_status(received_spf_values)

    return {
        "spf": selected["spf"] or "missing",
        "dkim": selected["dkim"] or "missing",
        "dmarc": selected["dmarc"] or "missing",
    }


class EmailAuthDetector(ModuleInterface):
    """Analyze email headers for SPF, DKIM, and DMARC trust signals."""

    @property
    def name(self) -> str:
        return "email_auth"

    @property
    def version(self) -> str:
        return "0.1.0"

    def analyze(self, input: AnalysisInput) -> list[Finding]:
        if input.input_type not in {"email_headers", "email_file"}:
            return []

        raw_headers = input.content.strip()
        if not raw_headers:
            return [
                Finding(
                    module=self.name,
                    category="EML000_EMPTY_INPUT",
                    severity=Severity.INFO,
                    confidence=Confidence.HIGH,
                    risk_score=10,
                    title="No email headers were provided",
                    explanation=(
                        "Email authentication checks require raw message headers."
                    ),
                    family_explanation=(
                        "No email header text was provided, so authentication checks could not run."
                    ),
                    evidence=[],
                    recommendations=[
                        "Paste raw email headers or provide a header file.",
                    ],
                )
            ]

        parser = HeaderParser(policy=policy.default)
        message = parser.parsestr(raw_headers, headersonly=True)

        auth_results_values = [
            str(value) for value in message.get_all("Authentication-Results", [])
        ]
        received_spf_values = [str(value) for value in message.get_all("Received-SPF", [])]

        if not auth_results_values and not received_spf_values:
            return [
                Finding(
                    module=self.name,
                    category="EML001_NO_AUTH_HEADERS",
                    severity=Severity.INFO,
                    confidence=Confidence.LOW,
                    risk_score=20,
                    title="No authentication result headers found",
                    explanation=(
                        "Headers do not include Authentication-Results or Received-SPF fields, "
                        "so SPF/DKIM/DMARC evaluation is incomplete."
                    ),
                    family_explanation=(
                        "This email did not include standard authentication results, "
                        "so trust checks are limited."
                    ),
                    evidence=[
                        Evidence(label="Authentication-Results Count", value="0"),
                        Evidence(label="Received-SPF Count", value="0"),
                    ],
                    recommendations=[
                        "Treat unexpected login/payment emails cautiously.",
                        "Verify important requests through a trusted channel.",
                    ],
                )
            ]

        normalized_statuses = _nearest_auth_statuses(auth_results_values, received_spf_values)

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
                        Evidence(label="SPF Status", value=normalized_statuses["spf"]),
                        Evidence(label="DKIM Status", value=normalized_statuses["dkim"]),
                        Evidence(label="DMARC Status", value=normalized_statuses["dmarc"]),
                        Evidence(
                            label="Authentication-Results Count",
                            value=str(len(auth_results_values)),
                        ),
                        Evidence(label="Received-SPF Count", value=str(len(received_spf_values))),
                        Evidence(label="Risk Delta", value=f"+{risk_delta}"),
                        Evidence(label="Cumulative Risk", value=str(cumulative_risk)),
                    ],
                    recommendations=recommendations,
                )
            )

        spf_status = normalized_statuses["spf"]
        if _is_fail(spf_status):
            add_finding(
                code="EML101_SPF_FAIL",
                risk_delta=30,
                confidence=Confidence.HIGH,
                title="SPF authentication failed",
                explanation=(
                    "SPF status indicates a failure or DNS/authentication error."
                ),
                family_explanation=(
                    "The sender server did not pass a key email authenticity check (SPF)."
                ),
                recommendations=[
                    "Avoid opening links or attachments until sender identity is verified.",
                    "Confirm the message through a separate trusted channel.",
                ],
            )
        elif _is_weak_or_missing(spf_status):
            add_finding(
                code="EML102_SPF_WEAK_OR_MISSING",
                risk_delta=12,
                confidence=Confidence.MEDIUM,
                title="SPF result is weak or missing",
                explanation=(
                    "SPF status is missing or non-pass (for example none/neutral/softfail). "
                    "This can be legitimate in some forwarding paths but reduces trust."
                ),
                family_explanation=(
                    "This email has a weak or missing SPF check, so sender trust is lower."
                ),
                recommendations=[
                    "Be careful with urgent requests, payments, or password resets.",
                ],
            )

        dkim_status = normalized_statuses["dkim"]
        if _is_fail(dkim_status):
            add_finding(
                code="EML201_DKIM_FAIL",
                risk_delta=30,
                confidence=Confidence.HIGH,
                title="DKIM signature validation failed",
                explanation=(
                    "DKIM status indicates a failed or broken signature."
                ),
                family_explanation=(
                    "The email's signed authenticity check (DKIM) did not pass."
                ),
                recommendations=[
                    "Treat the message as suspicious until independently verified.",
                ],
            )
        elif _is_weak_or_missing(dkim_status):
            add_finding(
                code="EML202_DKIM_WEAK_OR_MISSING",
                risk_delta=12,
                confidence=Confidence.MEDIUM,
                title="DKIM result is weak or missing",
                explanation=(
                    "DKIM status is missing or non-pass, "
                    "which lowers confidence in sender authenticity."
                ),
                family_explanation=(
                    "This email has a weak or missing DKIM check, so trust is reduced."
                ),
                recommendations=[
                    "Use caution before trusting links or requests in this message.",
                ],
            )

        dmarc_status = normalized_statuses["dmarc"]
        if _is_fail(dmarc_status):
            add_finding(
                code="EML301_DMARC_FAIL",
                risk_delta=35,
                confidence=Confidence.HIGH,
                title="DMARC policy check failed",
                explanation=(
                    "DMARC status indicates a fail or policy error."
                ),
                family_explanation=(
                    "The sender's domain policy check (DMARC) failed."
                ),
                recommendations=[
                    "Do not act on sensitive requests until verified independently.",
                ],
            )
        elif _is_weak_or_missing(dmarc_status):
            add_finding(
                code="EML302_DMARC_WEAK_OR_MISSING",
                risk_delta=18,
                confidence=Confidence.MEDIUM,
                title="DMARC result is weak or missing",
                explanation=(
                    "DMARC status is missing or non-pass. This can happen on some systems, "
                    "but it reduces sender-policy assurance."
                ),
                family_explanation=(
                    "This email has a weak or missing DMARC result, "
                    "so sender policy trust is lower."
                ),
                recommendations=[
                    "Double-check unexpected instructions before taking action.",
                ],
            )

        return findings
