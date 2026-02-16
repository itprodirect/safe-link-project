"""Orchestration layer for running modules and building aggregate results."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import UTC, datetime

from lsh.core.models import AnalysisInput, AnalysisResult, Finding, ModuleInterface
from lsh.core.scorer import normalize, score_to_severity

SummaryBuilder = Callable[[Sequence[Finding], int], str]


def build_summary(findings: Sequence[Finding], overall_risk: int) -> str:
    """Build a short, family-friendly, action-oriented summary."""
    if not findings:
        return (
            "No obvious lookalike-link warning signs found. "
            "For important accounts, type the website address yourself."
        )

    if overall_risk >= 81:
        return (
            "High-risk warning: this link may impersonate a trusted site. "
            "Do not open it, and visit the real site by typing the address yourself."
        )
    if overall_risk >= 61:
        return (
            "This link has strong warning signs. "
            "Avoid clicking and verify with the sender through a trusted channel."
        )
    if overall_risk >= 41:
        return (
            "This link has suspicious traits. "
            "Pause and confirm the destination before opening."
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
        findings = normalize(self._run_modules(analysis_input))
        overall_risk = max((finding.risk_score for finding in findings), default=0)
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
            findings.extend(module.analyze(analysis_input))
        return findings
