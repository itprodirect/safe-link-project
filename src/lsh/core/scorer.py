"""Core scorer for normalizing findings to severity levels.

Severity bands: 0-20 INFO, 21-40 LOW, 41-60 MEDIUM, 61-80 HIGH, 81-100 CRITICAL.

Compound aggregation: the worst finding sets the floor, each additional finding
adds diminishing weight (0.15^position). This rewards "multiple weak signals"
without letting trivial findings stack to CRITICAL.
"""

from lsh.core.models import Confidence, Finding, Severity

# Numeric mapping for confidence enum → float score.
CONFIDENCE_SCORES: dict[Confidence, float] = {
    Confidence.LOW: 0.55,
    Confidence.MEDIUM: 0.75,
    Confidence.HIGH: 0.92,
}


def confidence_score(confidence: Confidence) -> float:
    """Map Confidence enum to a numeric 0.0-1.0 value."""
    return CONFIDENCE_SCORES.get(confidence, 0.75)


def compute_severity_score(risk_score: int, conf: Confidence) -> int:
    """Compute effective severity: risk * confidence."""
    return int(risk_score * confidence_score(conf))


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
    """Compound severity: worst finding sets the floor, each adds diminishing weight.

    This rewards "multiple weak signals" without letting trivial findings
    stack to CRITICAL.

    Example: findings with risk_scores [50, 38, 26] →
      50 + 38*0.15 + 26*0.0225 ≈ 56 → MEDIUM
    """
    if not findings:
        return 0

    scores = sorted([f.risk_score for f in findings], reverse=True)

    base = scores[0]
    bonus = sum(s * (0.15**i) for i, s in enumerate(scores[1:], 1))

    return min(int(base + bonus), 100)


def normalize(findings: list[Finding]) -> list[Finding]:
    """Normalize findings by aligning severity to risk_score."""
    return [
        finding.model_copy(update={"severity": score_to_severity(finding.risk_score)})
        for finding in findings
    ]
