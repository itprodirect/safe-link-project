"""Family-friendly formatter output helpers reusable across adapters."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from lsh.core.models import AnalysisResult, Confidence, Finding


def _collect_recommendations(findings: list[Finding], limit: int = 3) -> list[str]:
    recommendations: list[str] = []
    seen: set[str] = set()
    for finding in findings:
        for recommendation in finding.recommendations:
            if recommendation in seen:
                continue
            seen.add(recommendation)
            recommendations.append(recommendation)
            if len(recommendations) >= limit:
                return recommendations
    return recommendations


def _collect_family_explanations(findings: list[Finding], limit: int = 3) -> list[str]:
    explanations: list[str] = []
    seen: set[str] = set()
    for finding in findings:
        explanation = finding.family_explanation.strip()
        if not explanation or explanation in seen:
            continue
        seen.add(explanation)
        explanations.append(explanation)
        if len(explanations) >= limit:
            return explanations
    return explanations


def _overall_confidence(findings: Sequence[Finding]) -> Confidence:
    ranking = {Confidence.LOW: 1, Confidence.MEDIUM: 2, Confidence.HIGH: 3}
    return max(findings, key=lambda finding: ranking[finding.confidence]).confidence


@dataclass(slots=True, frozen=True)
class FamilyView:
    """Structured family-friendly output that adapters can render differently."""

    risk_score: int
    severity: str
    summary: str
    signal_confidence: str | None
    reasons: tuple[str, ...]
    recommendations: tuple[str, ...]


def build_family_view(result: AnalysisResult) -> FamilyView:
    """Build a reusable family-facing view model from an analysis result."""
    findings = result.findings
    signal_confidence = _overall_confidence(findings).value if findings else None
    reasons = tuple(_collect_family_explanations(findings))
    recommendations = tuple(_collect_recommendations(findings))
    return FamilyView(
        risk_score=result.overall_risk,
        severity=result.overall_severity.value,
        summary=result.summary,
        signal_confidence=signal_confidence,
        reasons=reasons,
        recommendations=recommendations,
    )


def render_family_lines(
    *,
    label: str,
    subject: str,
    result: AnalysisResult,
    fallback_recommendations: Sequence[str],
) -> list[str]:
    """Render family output lines for CLI-style text output."""
    view = build_family_view(result)
    lines = [
        f"{label}: {subject}",
        f"Safety score: {view.risk_score}/100 ({view.severity})",
        f"What this means: {view.summary}",
    ]
    if view.signal_confidence is not None:
        lines.append(f"Signal confidence: {view.signal_confidence}")

    if view.reasons:
        lines.append("Why this may be risky:")
        lines.extend(f"- {reason}" for reason in view.reasons)

    lines.append("Safer next steps:")
    if view.recommendations:
        lines.extend(f"- {recommendation}" for recommendation in view.recommendations)
        return lines

    lines.extend(f"- {recommendation}" for recommendation in fallback_recommendations)
    return lines
