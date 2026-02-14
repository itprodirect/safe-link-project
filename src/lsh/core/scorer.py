"""Core scorer for normalizing findings to severity levels.

Severity bands: 0-20 INFO, 21-40 LOW, 41-60 MEDIUM, 61-80 HIGH, 81-100 CRITICAL.
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


def normalize(findings: list[Finding]) -> list[Finding]:
    """Normalize findings by aligning severity to risk_score.

    Stub implementation: sets severity from score but does not
    adjust scores themselves.
    """
    return [
        finding.model_copy(update={"severity": score_to_severity(finding.risk_score)})
        for finding in findings
    ]
