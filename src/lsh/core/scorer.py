"""Core scorer for normalizing findings to severity levels.

Severity bands: 0-20 INFO, 21-40 LOW, 41-60 MEDIUM, 61-80 HIGH, 81-100 CRITICAL.

Compound aggregation: the worst finding sets the floor, each additional finding
adds diminishing weight (0.15^position). This rewards "multiple weak signals"
without letting trivial findings stack to CRITICAL.

Aggregate risk is intentionally based on `finding.risk_score` only. Confidence
labels are used for user-facing trust calibration text, not score math.
"""

from lsh.core.models import Finding, Severity


def score_to_severity(score: int) -> Severity:
    """Map a 0-100 risk score to a severity level."""
    if score <= 20:
        return Severity.INFO
    if score <= 40:
        return Severity.LOW
    if score <= 60:
        return Severity.MEDIUM
    if score <= 80:
        return Severity.HIGH
    return Severity.CRITICAL


def aggregate_findings(findings: list[Finding]) -> int:
    """Compound severity using risk_score only (not confidence)."""
    if not findings:
        return 0

    scores = sorted((finding.risk_score for finding in findings), reverse=True)
    base = scores[0]
    bonus = sum(score * (0.15**index) for index, score in enumerate(scores[1:], 1))
    return min(int(base + bonus), 100)


def normalize(findings: list[Finding]) -> list[Finding]:
    """Normalize findings by aligning severity to risk_score."""
    return [
        finding.model_copy(update={"severity": score_to_severity(finding.risk_score)})
        for finding in findings
    ]

