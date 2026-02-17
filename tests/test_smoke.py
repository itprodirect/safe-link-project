"""Smoke tests for Link Safety Hub."""

from datetime import UTC, datetime
from pathlib import Path

from click.testing import CliRunner

from lsh.adapters.cli import main
from lsh.core.models import (
    AnalysisInput,
    AnalysisResult,
    Evidence,
    Finding,
    Severity,
)
from lsh.core.scorer import normalize, score_to_severity


def test_cli_help() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Link Safety Hub" in result.output
    assert "email-check" in result.output


def test_cli_check_help_includes_network_options() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["check", "--help"])
    assert result.exit_code == 0
    assert "--network" in result.output
    assert "--max-hops" in result.output
    assert "--timeout" in result.output


def test_cli_email_check_json_inline_headers() -> None:
    runner = CliRunner()
    headers = "Authentication-Results: mx; spf=fail; dkim=pass; dmarc=pass"
    result = runner.invoke(main, ["email-check", headers, "--json"])
    assert result.exit_code == 0
    assert "EML101_SPF_FAIL" in result.output


def test_cli_email_check_file_input(tmp_path: Path) -> None:
    headers_file = tmp_path / "headers.txt"
    headers_file.write_text(
        "Authentication-Results: mx; spf=pass; dkim=pass; dmarc=pass\n",
        encoding="utf-8",
    )
    runner = CliRunner()
    result = runner.invoke(main, ["email-check", str(headers_file), "--json"])
    assert result.exit_code == 0
    assert '"findings": []' in result.output


def test_cli_check_stub() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["check", "https://example.com"])
    assert result.exit_code == 0
    assert "example.com" in result.output
    assert "0/100" in result.output


def test_cli_check_json() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["check", "https://example.com", "--json"])
    assert result.exit_code == 0
    assert '"overall_risk": 0' in result.output


def test_cli_check_json_unicode_url_is_console_safe() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["check", "https://\u0430\u0440\u0440\u04cf\u0435.com", "--json"])
    assert result.exit_code == 0
    assert "\u0430" in result.output


def test_cli_check_technical_view_shows_finding_codes() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["check", "https://xn--pple-43d.com"])
    assert result.exit_code == 0
    assert "Findings:" in result.output
    assert "HMG002_PUNYCODE_VISIBILITY" in result.output
    assert "confidence=" in result.output


def test_cli_check_family_view_hides_technical_codes() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["check", "https://xn--pple-43d.com", "--family"])
    assert result.exit_code == 0
    assert "What this means:" in result.output
    assert "Signal confidence:" in result.output
    assert "Why this may be risky:" in result.output
    assert "HMG002_PUNYCODE_VISIBILITY" not in result.output
    assert "Safer next steps:" in result.output


def test_cli_allowlist_domain_suppresses_domain_lookalike_findings() -> None:
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["check", "https://paypaI.com", "--allowlist-domain", "paypai.com", "--json"],
    )
    assert result.exit_code == 0
    assert '"findings": []' in result.output


def test_cli_allowlist_category_limits_suppression_scope() -> None:
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "check",
            "https://paypaI.com",
            "--allowlist-domain",
            "paypai.com",
            "--allowlist-category",
            "HMG",
            "--json",
        ],
    )
    assert result.exit_code == 0
    assert "ASCII001_AMBIGUOUS_GLYPHS" in result.output


def test_cli_allowlist_category_all_can_suppress_url_findings() -> None:
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "check",
            "https://login.google.com.evil.com",
            "--allowlist-domain",
            "evil.com",
            "--allowlist-category",
            "ALL",
            "--json",
        ],
    )
    assert result.exit_code == 0
    assert '"findings": []' in result.output


def test_cli_allowlist_file_is_applied(tmp_path: Path) -> None:
    allowlist_file = tmp_path / "allowlist.txt"
    allowlist_file.write_text("# trusted domains\npaypai.com\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "check",
            "https://paypaI.com",
            "--allowlist-file",
            str(allowlist_file),
            "--json",
        ],
    )
    assert result.exit_code == 0
    assert '"findings": []' in result.output


def test_cli_allowlist_file_with_utf8_bom_is_applied(tmp_path: Path) -> None:
    allowlist_file = tmp_path / "allowlist-bom.txt"
    allowlist_file.write_bytes("# trusted domains\npaypai.com\n".encode("utf-8-sig"))

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "check",
            "https://paypaI.com",
            "--allowlist-file",
            str(allowlist_file),
            "--json",
        ],
    )
    assert result.exit_code == 0
    assert '"findings": []' in result.output


def test_models_analysis_input() -> None:
    inp = AnalysisInput(input_type="url", content="https://example.com")
    assert inp.input_type == "url"
    assert inp.content == "https://example.com"
    assert inp.metadata == {}


def test_models_finding() -> None:
    finding = Finding(
        module="test",
        category="test",
        severity=Severity.HIGH,
        risk_score=75,
        title="Test finding",
        explanation="Technical explanation.",
        family_explanation="Simple explanation.",
    )
    assert finding.risk_score == 75
    assert finding.severity == Severity.HIGH


def test_models_evidence() -> None:
    evidence = Evidence(label="Decoded", value="xn--example.com")
    assert evidence.label == "Decoded"


def test_models_analysis_result() -> None:
    inp = AnalysisInput(input_type="url", content="https://example.com")
    result = AnalysisResult(
        input=inp,
        findings=[],
        overall_risk=0,
        overall_severity=Severity.INFO,
        summary="No issues.",
        analyzed_at=datetime.now(UTC),
    )
    assert result.overall_risk == 0
    assert result.overall_severity == Severity.INFO


def test_scorer_normalize_empty() -> None:
    assert normalize([]) == []


def test_scorer_normalize_sets_severity() -> None:
    finding = Finding(
        module="test",
        category="test",
        severity=Severity.INFO,
        risk_score=85,
        title="Test",
        explanation="Test.",
        family_explanation="Test.",
    )
    normalized = normalize([finding])
    assert normalized[0].severity == Severity.CRITICAL


def test_scorer_severity_bands() -> None:
    assert score_to_severity(0) == Severity.INFO
    assert score_to_severity(20) == Severity.INFO
    assert score_to_severity(21) == Severity.LOW
    assert score_to_severity(40) == Severity.LOW
    assert score_to_severity(41) == Severity.MEDIUM
    assert score_to_severity(60) == Severity.MEDIUM
    assert score_to_severity(61) == Severity.HIGH
    assert score_to_severity(80) == Severity.HIGH
    assert score_to_severity(81) == Severity.CRITICAL
    assert score_to_severity(100) == Severity.CRITICAL
