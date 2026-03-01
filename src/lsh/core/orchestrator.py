"""Orchestration layer for running modules and building aggregate results."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import UTC, datetime

from lsh.core.context import build_runtime_context, set_runtime_context
from lsh.core.models import AnalysisInput, AnalysisResult, Confidence, Finding, ModuleInterface
from lsh.core.scorer import aggregate_findings, normalize, score_to_severity

SummaryBuilder = Callable[[Sequence[Finding], int], str]


def _highest_confidence(findings: Sequence[Finding]) -> Confidence:
    ranking = {Confidence.LOW: 1, Confidence.MEDIUM: 2, Confidence.HIGH: 3}
    return max(findings, key=lambda finding: ranking[finding.confidence]).confidence


def build_summary(findings: Sequence[Finding], overall_risk: int) -> str:
    """Build a short, family-friendly, action-oriented summary."""
    if not findings:
        return (
            "No obvious lookalike-link warning signs found. "
            "For important accounts, type the website address yourself."
        )

    confidence = _highest_confidence(findings)

    if overall_risk >= 81:
        if confidence == Confidence.LOW:
            return (
                "High-risk warning from limited-confidence signals. "
                "Do not open this link until you verify it through a trusted channel."
            )
        return (
            "High-risk warning: this link may impersonate a trusted site. "
            "Do not open it, and visit the real site by typing the address yourself."
        )
    if overall_risk >= 61:
        if confidence == Confidence.LOW:
            return (
                "This link has warning signs, but confidence is limited. "
                "Avoid clicking until you verify the destination."
            )
        return (
            "This link has strong warning signs. "
            "Avoid clicking and verify with the sender through a trusted channel."
        )
    if overall_risk >= 41:
        if confidence == Confidence.LOW:
            return (
                "Some suspicious traits were found with limited confidence. "
                "Pause and verify before opening."
            )
        return (
            "This link has suspicious traits. "
            "Pause and confirm the destination before opening."
        )
    if confidence == Confidence.LOW:
        return (
            "A mild, low-confidence warning sign was found. "
            "Use caution, and double-check the destination before signing in."
        )
    return (
        "A mild warning sign was found. "
        "Use caution and prefer trusted bookmarks for sensitive logins."
    )


class AnalysisOrchestrator:
    """Runs modules against one input and returns an aggregate result."""

    def __init__(
        self,
        modules: Sequence[ModuleInterface],
        *,
        summary_builder: SummaryBuilder | None = None,
    ) -> None:
        self._modules = tuple(modules)
        self._summary_builder = summary_builder or build_summary

    def analyze(self, analysis_input: AnalysisInput) -> AnalysisResult:
        """Run all modules, normalize findings, and return one analysis result."""
        set_runtime_context(analysis_input, build_runtime_context(analysis_input))
        findings = normalize(self._run_modules(analysis_input))
        overall_risk = aggregate_findings(findings)
        return AnalysisResult(
            input=analysis_input,
            findings=findings,
            overall_risk=overall_risk,
            overall_severity=score_to_severity(overall_risk),
            summary=self._summary_builder(findings, overall_risk),
            analyzed_at=datetime.now(UTC),
        )

    def _run_modules(self, analysis_input: AnalysisInput) -> list[Finding]:
        findings: list[Finding] = []
        for module in self._modules:
            if analysis_input.input_type not in module.supported_input_types:
                continue
            findings.extend(module.analyze(analysis_input))
        return findings
