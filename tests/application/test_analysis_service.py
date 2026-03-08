"""Tests for shared application-layer analysis services."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from lsh.application import analyze_email, analyze_url
from lsh.core.context import get_runtime_context
from lsh.core.models import Severity


def test_analyze_url_safe_input_has_zero_risk() -> None:
    result = analyze_url("https://example.com")
    assert result.findings == []
    assert result.overall_risk == 0
    assert result.overall_severity == Severity.INFO


def test_analyze_url_allowlist_finding_scope_suppresses_only_targeted_code() -> None:
    result = analyze_url(
        "https://xn--pple-43d.com",
        metadata={
            "allowlist_domains": ["xn--pple-43d.com"],
            "allowlist_categories": ["NONE"],
            "allowlist_findings": ["HMG002_PUNYCODE_VISIBILITY"],
        },
    )
    categories = {finding.category for finding in result.findings}
    assert "HMG002_PUNYCODE_VISIBILITY" not in categories
    assert "HMG003_MIXED_SCRIPT_HOSTNAME" in categories


def test_analyze_url_records_allowlist_suppression_trace() -> None:
    result = analyze_url(
        "https://xn--pple-43d.com",
        metadata={
            "allowlist_domains": ["xn--pple-43d.com"],
            "allowlist_categories": ["NONE"],
            "allowlist_findings": ["HMG002_PUNYCODE_VISIBILITY"],
        },
    )

    runtime_context = get_runtime_context(result.input)
    assert runtime_context is not None
    assert len(runtime_context.suppressed_findings) == 1
    event = runtime_context.suppressed_findings[0]
    assert event.module == "homoglyph"
    assert event.finding_code == "HMG002_PUNYCODE_VISIBILITY"
    assert event.suppression_scope == "finding"
    assert event.matched_rule == "HMG002_PUNYCODE_VISIBILITY"


def test_analyze_email_pass_results_have_no_findings() -> None:
    result = analyze_email(
        "Authentication-Results: mx; spf=pass; dkim=pass; dmarc=pass",
    )
    assert result.findings == []
    assert result.overall_risk == 0


def test_analyze_email_empty_input_is_flagged() -> None:
    result = analyze_email("")
    assert result.findings
    assert result.findings[0].category == "EML000_EMPTY_INPUT"


def test_analyze_email_accepts_email_file_input_type() -> None:
    result = analyze_email(
        "Authentication-Results: mx; spf=fail; dkim=pass; dmarc=pass",
        input_type="email_file",
    )
    categories = {finding.category for finding in result.findings}
    assert "EML101_SPF_FAIL" in categories


@pytest.mark.parametrize(
    "content",
    [
        "",
        "   ",
        "http://",
        "://bad",
        "not a url",
        "http://%zz",
        "https://exa mple.com",
    ],
)
def test_analyze_url_malformed_input_matrix_does_not_raise(content: str) -> None:
    result = analyze_url(content)
    assert 0 <= result.overall_risk <= 100
    assert result.overall_severity in {
        Severity.INFO,
        Severity.LOW,
        Severity.MEDIUM,
        Severity.HIGH,
        Severity.CRITICAL,
    }


@dataclass(slots=True)
class _FakeResponse:
    status_code: int = 200

    @property
    def headers(self) -> dict[str, str]:
        return {}


class _FakeSession:
    def head(
        self,
        _url: str,
        *,
        allow_redirects: bool,
        timeout: float,
        headers: dict[str, str],
    ) -> _FakeResponse:
        assert allow_redirects is False
        assert timeout >= 0.1
        assert "User-Agent" in headers
        return _FakeResponse()

    def close(self) -> None:
        return None


@pytest.mark.parametrize(
    "metadata",
    [
        {"network_enabled": "false", "network_max_hops": "abc", "network_timeout": "bad"},
        {"network_enabled": "off", "network_max_hops": 0, "network_timeout": 0},
        {"network_enabled": "0", "network_max_hops": -1, "network_timeout": -4},
        {"network_enabled": "true", "network_max_hops": "5", "network_timeout": "1.5"},
        {
            "allowlist_domains": "example.com",
            "allowlist_categories": "none",
            "allowlist_findings": "HMG002*",
        },
    ],
)
def test_analyze_url_metadata_edge_matrix_does_not_raise(
    monkeypatch: pytest.MonkeyPatch,
    metadata: dict[str, object],
) -> None:
    monkeypatch.setattr("lsh.modules.redirect.analyzer.requests.Session", lambda: _FakeSession())
    result = analyze_url("https://example.com", metadata=metadata)
    assert 0 <= result.overall_risk <= 100
