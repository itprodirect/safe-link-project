"""Tests for reusable family formatter output."""

from __future__ import annotations

from datetime import UTC, datetime

from lsh.core.models import AnalysisInput, AnalysisResult, Confidence, Finding, Severity
from lsh.formatters.family import build_family_view, render_family_lines


def _result(findings: list[Finding], *, summary: str = "Summary text.") -> AnalysisResult:
    return AnalysisResult(
        input=AnalysisInput(input_type="url", content="https://example.com"),
        findings=findings,
        overall_risk=65 if findings else 0,
        overall_severity=Severity.HIGH if findings else Severity.INFO,
        summary=summary,
        analyzed_at=datetime.now(UTC),
    )


def test_build_family_view_collects_top_reasons_and_recommendations() -> None:
    findings = [
        Finding(
            module="test",
            category="TST001",
            severity=Severity.INFO,
            confidence=Confidence.LOW,
            risk_score=40,
            title="One",
            explanation="E1",
            family_explanation="Reason A",
            recommendations=["Step 1", "Step 2"],
        ),
        Finding(
            module="test",
            category="TST002",
            severity=Severity.INFO,
            confidence=Confidence.HIGH,
            risk_score=60,
            title="Two",
            explanation="E2",
            family_explanation="Reason B",
            recommendations=["Step 2", "Step 3"],
        ),
    ]

    view = build_family_view(_result(findings))

    assert view.summary == "Summary text."
    assert view.signal_confidence == "HIGH"
    assert view.reasons == ("Reason A", "Reason B")
    assert view.recommendations == ("Step 1", "Step 2", "Step 3")


def test_render_family_lines_includes_sections_and_fallback_steps() -> None:
    lines = render_family_lines(
        label="Link checked",
        subject="https://example.com",
        result=_result([], summary="No issues."),
        fallback_recommendations=["Fallback 1", "Fallback 2"],
    )

    text = "\n".join(lines)
    assert "Link checked: https://example.com" in text
    assert "What this means: No issues." in text
    assert "Safer next steps:" in text
    assert "- Fallback 1" in text
    assert "- Fallback 2" in text
    assert "Signal confidence:" not in text
