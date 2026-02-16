"""CLI adapter for Link Safety Hub."""

import sys

import click

from lsh.core.models import AnalysisInput, AnalysisResult, Finding
from lsh.core.orchestrator import AnalysisOrchestrator
from lsh.modules import (
    AsciiLookalikeDetector,
    HomoglyphDetector,
    NetIPDetector,
    URLStructureDetector,
)

_URL_ORCHESTRATOR = AnalysisOrchestrator(
    modules=[
        NetIPDetector(),
        URLStructureDetector(),
        AsciiLookalikeDetector(),
        HomoglyphDetector(),
    ]
)


def _safe_console_text(value: str) -> str:
    """Best-effort console-safe text rendering for non-UTF terminals."""
    encoding = sys.stdout.encoding or "utf-8"
    return value.encode(encoding, errors="replace").decode(encoding, errors="replace")


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


def _collect_family_explanations(findings: list[Finding], limit: int = 3) -> list[str]:
    """Collect unique family-mode explanations from findings."""
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


def _print_technical_view(url: str, result: AnalysisResult) -> None:
    """Render technical CLI output with finding codes."""
    click.echo(f"URL: {_safe_console_text(url)}")
    click.echo(f"Risk: {result.overall_risk}/100 ({result.overall_severity.value})")
    click.echo(f"Summary: {result.summary}")
    if not result.findings:
        return

    click.echo("Findings:")
    for finding in result.findings:
        click.echo(f"- [{finding.category}] {finding.title} ({finding.risk_score}/100)")

    recommendations = _collect_recommendations(result.findings)
    if not recommendations:
        return

    click.echo("What to do next:")
    for recommendation in recommendations:
        click.echo(f"- {recommendation}")


def _print_family_view(url: str, result: AnalysisResult) -> None:
    """Render plain-language output intended for non-technical users."""
    click.echo(f"Link checked: {_safe_console_text(url)}")
    click.echo(f"Safety score: {result.overall_risk}/100 ({result.overall_severity.value})")
    click.echo(f"What this means: {result.summary}")

    explanations = _collect_family_explanations(result.findings)
    if explanations:
        click.echo("Why this may be risky:")
        for explanation in explanations:
            click.echo(f"- {explanation}")

    recommendations = _collect_recommendations(result.findings)
    click.echo("Safer next steps:")
    if recommendations:
        for recommendation in recommendations:
            click.echo(f"- {recommendation}")
        return

    click.echo("- Keep using trusted bookmarks for important accounts.")
    click.echo("- If unsure, verify with the sender in a separate message or call.")


@click.group()
def main() -> None:
    """Link Safety Hub - modular security toolbelt."""


@main.command()
@click.argument("url")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.option(
    "--family",
    "family_mode",
    is_flag=True,
    help="Use plain-language output with simplified findings.",
)
def check(url: str, as_json: bool, family_mode: bool) -> None:
    """Analyze a URL for safety issues."""
    analysis_input = AnalysisInput(input_type="url", content=url)
    result = _URL_ORCHESTRATOR.analyze(analysis_input)
    if as_json:
        click.echo(result.model_dump_json(indent=2))
        return

    if family_mode:
        _print_family_view(url, result)
        return

    _print_technical_view(url, result)


if __name__ == "__main__":
    main()
