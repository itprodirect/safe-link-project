"""Focused tests for the Homoglyph / IDN detector module."""

from lsh.core.models import AnalysisInput
from lsh.modules.homoglyph import HomoglyphDetector


def _codes(findings: list) -> set[str]:
    return {finding.category for finding in findings}


def test_homoglyph_clean_ascii_hostname_has_no_findings() -> None:
    detector = HomoglyphDetector()
    findings = detector.analyze(
        AnalysisInput(input_type="url", content="https://example.com/account/login")
    )
    assert findings == []


def test_homoglyph_unicode_hostname_flags_non_ascii_and_idna_view() -> None:
    detector = HomoglyphDetector()
    findings = detector.analyze(
        AnalysisInput(input_type="url", content="https://\u0430\u0440\u0440\u04cf\u0435.com")
    )
    codes = _codes(findings)
    assert "HMG001_NON_ASCII_HOSTNAME" in codes
    assert "HMG002_PUNYCODE_VISIBILITY" in codes
    assert any(
        evidence.label == "Hostname (idna)" and "xn--" in evidence.value
        for finding in findings
        for evidence in finding.evidence
    )


def test_homoglyph_mixed_scripts_detected() -> None:
    detector = HomoglyphDetector()
    findings = detector.analyze(
        AnalysisInput(input_type="url", content="https://\u0440\u0430ypal.com")
    )
    assert "HMG003_MIXED_SCRIPT_HOSTNAME" in _codes(findings)
    mixed_script = next(
        finding for finding in findings if finding.category == "HMG003_MIXED_SCRIPT_HOSTNAME"
    )
    assert any(
        evidence.label == "Label Scripts"
        and "Latin" in evidence.value
        and "Cyrillic" in evidence.value
        for evidence in mixed_script.evidence
    )


def test_homoglyph_punycode_input_surfaces_unicode_and_punycode_views() -> None:
    detector = HomoglyphDetector()
    findings = detector.analyze(
        AnalysisInput(input_type="url", content="https://xn--pple-43d.com")
    )
    punycode_finding = next(
        finding for finding in findings if finding.category == "HMG002_PUNYCODE_VISIBILITY"
    )
    assert any(
        evidence.label == "Input Hostname" and evidence.value == "xn--pple-43d.com"
        for evidence in punycode_finding.evidence
    )
    unicode_view = next(
        evidence.value for evidence in punycode_finding.evidence if evidence.label == "Unicode View"
    )
    assert not unicode_view.startswith("xn--")
