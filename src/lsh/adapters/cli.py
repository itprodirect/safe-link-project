"""CLI adapter for Link Safety Hub."""

from datetime import UTC, datetime

import click

from lsh.core.models import AnalysisInput, AnalysisResult, Finding
from lsh.core.scorer import normalize, score_to_severity
from lsh.modules import HomoglyphDetector


def _run_url_modules(analysis_input: AnalysisInput) -> list[Finding]:
    """Run all URL modules for one analysis input."""
    modules = [HomoglyphDetector()]
    findings: list[Finding] = []
    for module in modules:
        findings.extend(module.analyze(analysis_input))
    return findings


def _build_summary(findings: list[Finding], overall_risk: int) -> str:
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


def _collect_recommendations(findings: list[Finding], limit: int = 3) -> list[str]:
    """Collect unique recommendations from findings."""
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


@click.group()
def main() -> None:
    """Link Safety Hub - modular security toolbelt."""


@main.command()
@click.argument("url")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def check(url: str, as_json: bool) -> None:
    """Analyze a URL for safety issues."""
    analysis_input = AnalysisInput(input_type="url", content=url)
    findings = normalize(_run_url_modules(analysis_input))
    overall_risk = max((finding.risk_score for finding in findings), default=0)
    result = AnalysisResult(
        input=analysis_input,
        findings=findings,
        overall_risk=overall_risk,
        overall_severity=score_to_severity(overall_risk),
        summary=_build_summary(findings, overall_risk),
        analyzed_at=datetime.now(UTC),
    )
    if as_json:
        click.echo(result.model_dump_json(indent=2))
        return

    click.echo(f"URL: {url}")
    click.echo(f"Risk: {result.overall_risk}/100 ({result.overall_severity.value})")
    click.echo(f"Summary: {result.summary}")
    if not findings:
        return

    click.echo("Findings:")
    for finding in findings:
        click.echo(f"- [{finding.category}] {finding.title} ({finding.risk_score}/100)")

    recommendations = _collect_recommendations(findings)
    if not recommendations:
        return

    click.echo("What to do next:")
    for recommendation in recommendations:
        click.echo(f"- {recommendation}")
