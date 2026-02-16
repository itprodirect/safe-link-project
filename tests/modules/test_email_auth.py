"""Focused tests for email authentication header analysis."""

from lsh.core.models import AnalysisInput, Finding
from lsh.modules.email_auth import EmailAuthDetector


def _code_map(findings: list[Finding]) -> dict[str, Finding]:
    return {finding.category: finding for finding in findings}


def test_email_auth_no_auth_headers_is_flagged() -> None:
    detector = EmailAuthDetector()
    findings = detector.analyze(
        AnalysisInput(
            input_type="email_headers",
            content="From: user@example.com\nSubject: hi\n\nhello",
        )
    )
    assert "EML001_NO_AUTH_HEADERS" in _code_map(findings)


def test_email_auth_all_pass_results_have_no_findings() -> None:
    detector = EmailAuthDetector()
    findings = detector.analyze(
        AnalysisInput(
            input_type="email_headers",
            content=(
                "From: billing@example.com\n"
                "Authentication-Results: mx.example; spf=pass smtp.mailfrom=example.com; "
                "dkim=pass header.d=example.com; dmarc=pass\n\nbody"
            ),
        )
    )
    assert findings == []


def test_email_auth_failures_are_reported() -> None:
    detector = EmailAuthDetector()
    findings = detector.analyze(
        AnalysisInput(
            input_type="email_headers",
            content=(
                "Authentication-Results: mx.example; spf=fail smtp.mailfrom=evil.com; "
                "dkim=fail header.d=evil.com; dmarc=fail\n\n"
            ),
        )
    )
    codes = _code_map(findings)
    assert "EML101_SPF_FAIL" in codes
    assert "EML201_DKIM_FAIL" in codes
    assert "EML301_DMARC_FAIL" in codes


def test_email_auth_received_spf_is_used_for_spf_status() -> None:
    detector = EmailAuthDetector()
    findings = detector.analyze(
        AnalysisInput(
            input_type="email_file",
            content="Received-SPF: fail (example) client-ip=203.0.113.10;\n\n",
        )
    )
    assert "EML101_SPF_FAIL" in _code_map(findings)


def test_email_auth_empty_input_is_flagged() -> None:
    detector = EmailAuthDetector()
    findings = detector.analyze(AnalysisInput(input_type="email_headers", content=""))
    assert "EML000_EMPTY_INPUT" in _code_map(findings)
