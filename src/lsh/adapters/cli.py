"""CLI adapter for Link Safety Hub."""

import sys
from collections.abc import Sequence
from pathlib import Path

import click

from lsh.core.models import AnalysisInput, AnalysisResult, Confidence, Finding
from lsh.core.orchestrator import AnalysisOrchestrator
from lsh.modules import (
    AsciiLookalikeDetector,
    EmailAuthDetector,
    HomoglyphDetector,
    NetIPDetector,
    RedirectChainDetector,
    URLStructureDetector,
)

_URL_ORCHESTRATOR = AnalysisOrchestrator(
    modules=[
        NetIPDetector(),
        URLStructureDetector(),
        AsciiLookalikeDetector(),
        HomoglyphDetector(),
        RedirectChainDetector(),
    ]
)
_EMAIL_ORCHESTRATOR: AnalysisOrchestrator


def _build_email_summary(findings: Sequence[Finding], overall_risk: int) -> str:
    """Build a concise summary tuned for email authentication results."""
    if not findings:
        return "No obvious email authentication issues were found in the provided headers."

    if overall_risk >= 81:
        return (
            "High-risk email-authentication warning. "
            "Do not trust links or urgent requests until independently verified."
        )
    if overall_risk >= 61:
        return (
            "This message has strong authentication warning signs. "
            "Verify sender identity through a trusted channel."
        )
    if overall_risk >= 41:
        return (
            "This message has authentication concerns. "
            "Use caution before acting on requests."
        )
    return (
        "A mild email authentication warning sign was found. "
        "Double-check sensitive requests before taking action."
    )


_EMAIL_ORCHESTRATOR = AnalysisOrchestrator(
    modules=[EmailAuthDetector()],
    summary_builder=_build_email_summary,
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


def _overall_confidence(findings: list[Finding]) -> Confidence:
    ranking = {Confidence.LOW: 1, Confidence.MEDIUM: 2, Confidence.HIGH: 3}
    return max(findings, key=lambda finding: ranking[finding.confidence]).confidence


def _load_allowlist_domains(
    allowlist_domains: tuple[str, ...],
    allowlist_files: tuple[str, ...],
) -> list[str]:
    """Collect allowlist domains from CLI values and file inputs."""
    collected: list[str] = []
    seen: set[str] = set()

    def add(value: str) -> None:
        normalized = value.strip().lstrip("\ufeff").strip()
        if not normalized:
            return
        if normalized in seen:
            return
        seen.add(normalized)
        collected.append(normalized)

    for domain in allowlist_domains:
        add(domain)

    for file_path in allowlist_files:
        path = Path(file_path)
        try:
            raw_text = path.read_text(encoding="utf-8")
        except OSError as exc:  # pragma: no cover - click path checks most failures
            raise click.ClickException(
                f"Could not read allowlist file '{file_path}': {exc}"
            ) from exc

        for line in raw_text.splitlines():
            candidate = line.lstrip("\ufeff").split("#", maxsplit=1)[0].strip()
            add(candidate)

    return collected


def _read_text_file(path: Path) -> str:
    """Read text from disk with BOM-aware utf-8 first and latin-1 fallback."""
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise click.ClickException(f"Could not decode file '{path}' as text.")


def _resolve_email_input(source: str, treat_as_file: bool) -> tuple[str, str, str]:
    """Resolve email headers input from inline text or file path."""
    candidate_path = Path(source)
    use_file = treat_as_file or candidate_path.is_file()
    if not use_file:
        return "email_headers", source, "inline headers"

    if not candidate_path.exists() or not candidate_path.is_file():
        raise click.ClickException(f"Email header file not found: {source}")

    return "email_file", _read_text_file(candidate_path), str(candidate_path)


def _print_technical_view(url: str, result: AnalysisResult) -> None:
    """Render technical CLI output with finding codes."""
    click.echo(f"URL: {_safe_console_text(url)}")
    click.echo(f"Risk: {result.overall_risk}/100 ({result.overall_severity.value})")
    click.echo(f"Summary: {result.summary}")
    if not result.findings:
        return

    click.echo("Findings:")
    for finding in result.findings:
        click.echo(
            f"- [{finding.category}] {finding.title} "
            f"({finding.risk_score}/100, confidence={finding.confidence.value})"
        )

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
    if result.findings:
        click.echo(f"Signal confidence: {_overall_confidence(result.findings).value}")

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


def _print_technical_email_view(source_label: str, result: AnalysisResult) -> None:
    """Render technical output for email header analysis."""
    click.echo(f"Email source: {_safe_console_text(source_label)}")
    click.echo(f"Risk: {result.overall_risk}/100 ({result.overall_severity.value})")
    click.echo(f"Summary: {result.summary}")
    if not result.findings:
        return

    click.echo("Findings:")
    for finding in result.findings:
        click.echo(
            f"- [{finding.category}] {finding.title} "
            f"({finding.risk_score}/100, confidence={finding.confidence.value})"
        )

    recommendations = _collect_recommendations(result.findings)
    if not recommendations:
        return

    click.echo("What to do next:")
    for recommendation in recommendations:
        click.echo(f"- {recommendation}")


def _print_family_email_view(source_label: str, result: AnalysisResult) -> None:
    """Render family-oriented output for email header analysis."""
    click.echo(f"Email checked: {_safe_console_text(source_label)}")
    click.echo(f"Safety score: {result.overall_risk}/100 ({result.overall_severity.value})")
    click.echo(f"What this means: {result.summary}")
    if result.findings:
        click.echo(f"Signal confidence: {_overall_confidence(result.findings).value}")

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

    click.echo("- Be careful with urgent requests until sender identity is confirmed.")


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
@click.option(
    "--allowlist-domain",
    "allowlist_domains",
    multiple=True,
    help="Suppress domain-lookalike findings for these trusted domains.",
)
@click.option(
    "--allowlist-file",
    "allowlist_files",
    multiple=True,
    type=click.Path(exists=True, dir_okay=False, path_type=str),
    help="Read allowlisted domains from a file (one domain per line, # comments allowed).",
)
@click.option(
    "--allowlist-category",
    "allowlist_categories",
    multiple=True,
    type=click.Choice(["HMG", "ASCII", "URL", "NET", "ALL"], case_sensitive=False),
    help="Category prefixes suppressed for allowlisted domains (default: HMG,ASCII).",
)
@click.option(
    "--network",
    "network_enabled",
    is_flag=True,
    help="Enable opt-in network checks (for example redirect chain analysis).",
)
@click.option(
    "--max-hops",
    "network_max_hops",
    type=click.IntRange(min=1, max=15),
    default=5,
    show_default=True,
    help="Maximum redirect hops when --network is enabled.",
)
@click.option(
    "--timeout",
    "network_timeout",
    type=click.FloatRange(min=0.1),
    default=3.0,
    show_default=True,
    help="Per-request timeout in seconds when --network is enabled.",
)
def check(
    url: str,
    as_json: bool,
    family_mode: bool,
    allowlist_domains: tuple[str, ...],
    allowlist_files: tuple[str, ...],
    allowlist_categories: tuple[str, ...],
    network_enabled: bool,
    network_max_hops: int,
    network_timeout: float,
) -> None:
    """Analyze a URL for safety issues."""
    resolved_allowlist = _load_allowlist_domains(allowlist_domains, allowlist_files)
    metadata: dict[str, object] = {}
    if resolved_allowlist:
        metadata["allowlist_domains"] = resolved_allowlist
    if allowlist_categories:
        metadata["allowlist_categories"] = [category.upper() for category in allowlist_categories]
    metadata["network_enabled"] = network_enabled
    metadata["network_max_hops"] = network_max_hops
    metadata["network_timeout"] = network_timeout

    analysis_input = AnalysisInput(
        input_type="url",
        content=url,
        metadata=metadata,
    )
    result = _URL_ORCHESTRATOR.analyze(analysis_input)
    if as_json:
        click.echo(result.model_dump_json(indent=2))
        return

    if family_mode:
        _print_family_view(url, result)
        return

    _print_technical_view(url, result)


@main.command("email-check")
@click.argument("headers_or_file")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.option(
    "--family",
    "family_mode",
    is_flag=True,
    help="Use plain-language output with simplified findings.",
)
@click.option(
    "--file",
    "treat_as_file",
    is_flag=True,
    help="Treat input as a file path even if the file does not exist yet.",
)
def email_check(
    headers_or_file: str,
    as_json: bool,
    family_mode: bool,
    treat_as_file: bool,
) -> None:
    """Analyze email headers for SPF/DKIM/DMARC trust signals."""
    input_type, content, source_label = _resolve_email_input(headers_or_file, treat_as_file)
    result = _EMAIL_ORCHESTRATOR.analyze(
        AnalysisInput(input_type=input_type, content=content)
    )

    if as_json:
        click.echo(result.model_dump_json(indent=2))
        return

    if family_mode:
        _print_family_email_view(source_label, result)
        return

    _print_technical_email_view(source_label, result)


if __name__ == "__main__":
    main()
