"""Tests for orchestration behavior and aggregate result semantics."""

from collections.abc import Sequence

from lsh.core.models import AnalysisInput, Confidence, Finding, ModuleInterface, Severity
from lsh.core.orchestrator import AnalysisOrchestrator, build_summary
from lsh.core.scorer import aggregate_findings
from lsh.modules.homoglyph import HomoglyphDetector


def _url_orchestrator() -> AnalysisOrchestrator:
    return AnalysisOrchestrator(modules=[HomoglyphDetector()])


class _ProbeModule(ModuleInterface):
    def __init__(self, supported_input_types: frozenset[str]) -> None:
        self._supported_input_types = supported_input_types
        self.calls = 0

    @property
    def name(self) -> str:
        return "probe"

    @property
    def version(self) -> str:
        return "0.0.0"

    @property
    def supported_input_types(self) -> frozenset[str]:
        return self._supported_input_types

    def analyze(self, input: AnalysisInput) -> list[Finding]:
        self.calls += 1
        return []


def test_orchestrator_returns_empty_findings_for_safe_url() -> None:
    result = _url_orchestrator().analyze(
        AnalysisInput(input_type="url", content="https://example.com/login")
    )
    assert result.findings == []
    assert result.overall_risk == 0
    assert result.overall_severity == Severity.INFO
    assert result.summary.startswith("No obvious lookalike-link")


def test_orchestrator_uses_aggregate_findings_policy_for_overall_risk() -> None:
    result = _url_orchestrator().analyze(
        AnalysisInput(input_type="url", content="https://xn--pple-43d.com")
    )
    assert result.findings
    assert result.overall_risk == aggregate_findings(result.findings)
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


def test_build_summary_mentions_limited_confidence_for_low_confidence_findings() -> None:
    finding = Finding(
        module="test",
        category="TST001",
        severity=Severity.INFO,
        confidence=Confidence.LOW,
        risk_score=65,
        title="Test finding",
        explanation="Test explanation.",
        family_explanation="Test family explanation.",
    )
    summary = build_summary([finding], 65)
    assert "confidence is limited" in summary.lower()


def test_orchestrator_routes_modules_by_supported_input_type() -> None:
    url_probe = _ProbeModule(frozenset({"url"}))
    email_probe = _ProbeModule(frozenset({"email_headers", "email_file"}))
    orchestrator = AnalysisOrchestrator(modules=[url_probe, email_probe])

    orchestrator.analyze(AnalysisInput(input_type="url", content="https://example.com"))

    assert url_probe.calls == 1
    assert email_probe.calls == 0
