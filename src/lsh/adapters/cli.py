"""CLI adapter for Link Safety Hub."""

from datetime import UTC, datetime

import click

from lsh.core.models import AnalysisInput, AnalysisResult, Severity
from lsh.core.scorer import normalize


@click.group()
def main() -> None:
    """Link Safety Hub — modular security toolbelt."""


@main.command()
@click.argument("url")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def check(url: str, as_json: bool) -> None:
    """Analyze a URL for safety issues."""
    analysis_input = AnalysisInput(input_type="url", content=url)
    findings = normalize([])
    result = AnalysisResult(
        input=analysis_input,
        findings=findings,
        overall_risk=0,
        overall_severity=Severity.INFO,
        summary="No issues found (stub — no modules loaded yet).",
        analyzed_at=datetime.now(UTC),
    )
    if as_json:
        click.echo(result.model_dump_json(indent=2))
    else:
        click.echo(f"URL: {url}")
        click.echo(f"Risk: {result.overall_risk}/100 ({result.overall_severity.value})")
        click.echo(f"Summary: {result.summary}")
