"""Tests for orchestration behavior and aggregate result semantics."""

from collections.abc import Sequence

from lsh.core.models import AnalysisInput, Finding, Severity
from lsh.core.orchestrator import AnalysisOrchestrator
from lsh.modules.homoglyph import HomoglyphDetector


def _url_orchestrator() -> AnalysisOrchestrator:
    return AnalysisOrchestrator(modules=[HomoglyphDetector()])


def test_orchestrator_returns_empty_findings_for_safe_url() -> None:
    result = _url_orchestrator().analyze(
        AnalysisInput(input_type="url", content="https://example.com/login")
    )
    assert result.findings == []
    assert result.overall_risk == 0
    assert result.overall_severity == Severity.INFO
    assert result.summary.startswith("No obvious lookalike-link")


def test_orchestrator_uses_max_finding_score_as_overall_risk() -> None:
    result = _url_orchestrator().analyze(
        AnalysisInput(input_type="url", content="https://xn--pple-43d.com")
    )
    assert result.findings
    assert result.overall_risk == max(finding.risk_score for finding in result.findings)
    assert any(finding.category == "HMG002_PUNYCODE_VISIBILITY" for finding in result.findings)
    assert result.overall_severity in {
        Severity.LOW,
        Severity.MEDIUM,
        Severity.HIGH,
        Severity.CRITICAL,
    }


def test_orchestrator_accepts_custom_summary_builder() -> None:
    def summary_builder(findings: Sequence[Finding], overall_risk: int) -> str:
        return f"{overall_risk}:{len(findings)}"

    result = AnalysisOrchestrator(
        modules=[HomoglyphDetector()],
        summary_builder=summary_builder,
    ).analyze(AnalysisInput(input_type="url", content="https://example.com"))

    assert result.summary == "0:0"
