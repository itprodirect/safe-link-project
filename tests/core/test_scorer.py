"""Focused tests for scorer invariants and aggregate-risk semantics."""

from __future__ import annotations

from lsh.core.models import Confidence, Finding, Severity
from lsh.core.scorer import aggregate_findings, score_to_severity


def _finding(*, risk_score: int, confidence: Confidence) -> Finding:
    return Finding(
        module="test",
        category="TST001",
        severity=Severity.INFO,
        confidence=confidence,
        risk_score=risk_score,
        title="Test",
        explanation="Test explanation.",
        family_explanation="Test family explanation.",
    )


def test_aggregate_findings_is_confidence_independent() -> None:
    low = [_finding(risk_score=60, confidence=Confidence.LOW)]
    high = [_finding(risk_score=60, confidence=Confidence.HIGH)]

    assert aggregate_findings(low) == 60
    assert aggregate_findings(high) == 60
    assert aggregate_findings(low) == aggregate_findings(high)


def test_aggregate_findings_is_order_independent() -> None:
    a = _finding(risk_score=55, confidence=Confidence.HIGH)
    b = _finding(risk_score=30, confidence=Confidence.LOW)
    c = _finding(risk_score=15, confidence=Confidence.MEDIUM)

    assert aggregate_findings([a, b, c]) == aggregate_findings([c, a, b])


def test_score_to_severity_thresholds_stable() -> None:
    assert score_to_severity(20) == Severity.INFO
    assert score_to_severity(21) == Severity.LOW
    assert score_to_severity(40) == Severity.LOW
    assert score_to_severity(41) == Severity.MEDIUM
    assert score_to_severity(60) == Severity.MEDIUM
    assert score_to_severity(61) == Severity.HIGH
    assert score_to_severity(80) == Severity.HIGH
    assert score_to_severity(81) == Severity.CRITICAL
