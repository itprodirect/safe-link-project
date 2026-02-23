"""CLI adapter for Link Safety Hub."""

import json
import sys
from collections.abc import Sequence
from pathlib import Path

import click

from lsh.core.models import AnalysisInput, AnalysisResult, Finding
from lsh.core.orchestrator import AnalysisOrchestrator
from lsh.formatters.family import render_family_lines
from lsh.modules import (
    AsciiLookalikeDetector,
    EmailAuthDetector,
    HomoglyphDetector,
    NetIPDetector,
    RedirectChainDetector,
    URLStructureDetector,
)
from lsh.modules.qr_decode import (
    QRDecodeError,
    QRDecodeUnavailableError,
    decode_qr_payloads_from_image,
    extract_url_payloads,
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


def _analyze_url_result(url: str, metadata: dict[str, object] | None = None) -> AnalysisResult:
    """Run URL analysis and return the aggregate result."""
    return _URL_ORCHESTRATOR.analyze(
        AnalysisInput(input_type="url", content=url, metadata=metadata or {})
    )


def _print_qr_scan_header(image_path: str, decoded_count: int, url_count: int) -> None:
    click.echo(f"QR image: {_safe_console_text(image_path)}")
    click.echo(f"Decoded payloads: {decoded_count} (URL-like: {url_count})")


def _qr_json_payload(
    *,
    image_path: str,
    decoded_payloads: list[str],
    url_results: list[tuple[str, AnalysisResult]],
    analyzed_all: bool,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "image_path": image_path,
        "decoded_payloads": decoded_payloads,
        "decoded_payload_count": len(decoded_payloads),
        "url_payload_count": len(url_results),
        "analyzed_all": analyzed_all,
    }
    if analyzed_all:
        payload["results"] = [
            {"url": url, "result": result.model_dump(mode="json")} for url, result in url_results
        ]
        return payload

    selected_url, selected_result = url_results[0]
    payload["selected_url"] = selected_url
    payload["result"] = selected_result.model_dump(mode="json")
    return payload


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
    for line in render_family_lines(
        label="Link checked",
        subject=_safe_console_text(url),
        result=result,
        fallback_recommendations=[
            "Keep using trusted bookmarks for important accounts.",
            "If unsure, verify with the sender in a separate message or call.",
        ],
    ):
        click.echo(line)


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
    for line in render_family_lines(
        label="Email checked",
        subject=_safe_console_text(source_label),
        result=result,
        fallback_recommendations=[
            "Be careful with urgent requests until sender identity is confirmed.",
        ],
    ):
        click.echo(line)


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

    result = _analyze_url_result(url, metadata)
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


@main.command("qr-scan")
@click.argument(
    "image_path",
    type=click.Path(exists=True, dir_okay=False, path_type=str),
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.option(
    "--family",
    "family_mode",
    is_flag=True,
    help="Use plain-language output with simplified findings.",
)
@click.option(
    "--all",
    "analyze_all",
    is_flag=True,
    help="Analyze all decoded URL payloads instead of only the first URL payload.",
)
def qr_scan(
    image_path: str,
    as_json: bool,
    family_mode: bool,
    analyze_all: bool,
) -> None:
    """Decode a QR image and analyze extracted URL payloads."""
    try:
        decoded_payloads = decode_qr_payloads_from_image(image_path)
    except QRDecodeUnavailableError as exc:
        raise click.ClickException(f"QR scanning unavailable: {exc}") from exc
    except QRDecodeError as exc:
        raise click.ClickException(str(exc)) from exc

    if not decoded_payloads:
        raise click.ClickException("No QR payloads were decoded from the image.")

    url_payloads = extract_url_payloads(decoded_payloads)
    if not url_payloads:
        raise click.ClickException("Decoded QR payloads did not contain URL-like values.")

    selected_urls = url_payloads if analyze_all else [url_payloads[0]]
    url_results = [(url, _analyze_url_result(url)) for url in selected_urls]

    if as_json:
        click.echo(
            json.dumps(
                _qr_json_payload(
                    image_path=image_path,
                    decoded_payloads=decoded_payloads,
                    url_results=url_results,
                    analyzed_all=analyze_all,
                ),
                indent=2,
            )
        )
        return

    _print_qr_scan_header(image_path, len(decoded_payloads), len(url_payloads))

    if not analyze_all and len(url_payloads) > 1:
        click.echo("Using first URL payload (use --all to analyze every decoded URL).")

    for index, (url, result) in enumerate(url_results, start=1):
        if analyze_all:
            if index > 1:
                click.echo()
            click.echo(f"[{index}/{len(url_results)}]")

        if family_mode:
            _print_family_view(url, result)
        else:
            _print_technical_view(url, result)


if __name__ == "__main__":
    main()
