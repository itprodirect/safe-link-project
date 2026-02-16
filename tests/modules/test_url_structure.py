"""Focused tests for URL structure deception patterns."""

from lsh.core.models import AnalysisInput, Finding
from lsh.modules.url_structure import URLStructureDetector


def _code_map(findings: list[Finding]) -> dict[str, Finding]:
    return {finding.category: finding for finding in findings}


def test_userinfo_pattern_flags_true_host_after_at_symbol() -> None:
    detector = URLStructureDetector()
    findings = detector.analyze(
        AnalysisInput(input_type="url", content="http://google.com:80@evil.com")
    )
    mapped = _code_map(findings)
    assert "URL001_USERINFO_PRESENT" in mapped

    userinfo_finding = mapped["URL001_USERINFO_PRESENT"]
    true_host_evidence = next(
        evidence.value for evidence in userinfo_finding.evidence if evidence.label == "True Host"
    )
    assert true_host_evidence == "evil.com"


def test_deceptive_subdomain_pattern_flags_brand_like_prefix() -> None:
    detector = URLStructureDetector()
    findings = detector.analyze(
        AnalysisInput(input_type="url", content="https://login.google.com.evil.com")
    )
    assert "URL002_DECEPTIVE_SUBDOMAIN" in _code_map(findings)


def test_nested_url_parameter_pattern_is_detected() -> None:
    detector = URLStructureDetector()
    findings = detector.analyze(
        AnalysisInput(
            input_type="url",
            content="https://example.com/redirect?url=https://google.com",
        )
    )
    mapped = _code_map(findings)
    assert "URL003_NESTED_URL_PARAMETER" in mapped
    assert any(
        evidence.label == "Nested Host" and evidence.value == "google.com"
        for evidence in mapped["URL003_NESTED_URL_PARAMETER"].evidence
    )
