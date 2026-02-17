"""Focused tests for the Homoglyph / IDN detector module."""

from lsh.core.models import AnalysisInput, Finding
from lsh.modules.homoglyph import HomoglyphDetector


def _codes(findings: list[Finding]) -> set[str]:
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


def test_homoglyph_skips_ip_literals() -> None:
    detector = HomoglyphDetector()
    findings = detector.analyze(AnalysisInput(input_type="url", content="http://127.0.0.1"))
    assert findings == []


def test_homoglyph_latin_diacritics_have_reduced_risk() -> None:
    """Legitimate IDN domains with Latin diacritics (münchen.de) should score low."""
    detector = HomoglyphDetector()
    findings = detector.analyze(
        AnalysisInput(input_type="url", content="https://m\u00fcnchen.de")
    )
    codes = _codes(findings)
    # Should flag non-ASCII and confusable, but NOT mixed scripts
    assert "HMG001_NON_ASCII_HOSTNAME" in codes
    assert "HMG003_MIXED_SCRIPT_HOSTNAME" not in codes
    # All findings should be LOW confidence for Latin diacritics
    for finding in findings:
        if finding.category in ("HMG001_NON_ASCII_HOSTNAME", "HMG004_CONFUSABLE_CHARACTERS"):
            assert finding.confidence.value == "LOW"
    # Total cumulative risk should be <= 40
    max_risk = max(f.risk_score for f in findings)
    assert max_risk <= 40


def test_homoglyph_cyrillic_attack_is_still_critical() -> None:
    """Cross-script attacks must remain high-risk despite the Latin diacritics heuristic."""
    detector = HomoglyphDetector()
    findings = detector.analyze(
        AnalysisInput(input_type="url", content="https://xn--pple-43d.com")
    )
    codes = _codes(findings)
    assert "HMG003_MIXED_SCRIPT_HOSTNAME" in codes
    assert "HMG004_CONFUSABLE_CHARACTERS" in codes
    hmg004 = next(f for f in findings if f.category == "HMG004_CONFUSABLE_CHARACTERS")
    assert hmg004.confidence.value == "HIGH"
    assert hmg004.risk_score == 100


def test_homoglyph_respects_allowlist_domains() -> None:
    detector = HomoglyphDetector()
    findings = detector.analyze(
        AnalysisInput(
            input_type="url",
            content="https://\u0430\u0440\u0440\u04cf\u0435.com",
            metadata={"allowlist_domains": ["\u0430\u0440\u0440\u04cf\u0435.com"]},
        )
    )
    assert findings == []
