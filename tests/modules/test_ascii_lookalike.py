"""Focused tests for ASCII lookalike/leet brand impersonation patterns."""

import pytest

from lsh.core.models import AnalysisInput
from lsh.modules.ascii_lookalike import AsciiLookalikeDetector


def _codes(url: str) -> set[str]:
    detector = AsciiLookalikeDetector()
    findings = detector.analyze(AnalysisInput(input_type="url", content=url))
    return {finding.category for finding in findings}


def test_ambiguous_glyph_domain_is_flagged() -> None:
    assert "ASCII001_AMBIGUOUS_GLYPHS" in _codes("https://paypaI.com")


def test_ambiguous_glyph_domain_is_flagged_for_multi_part_suffix() -> None:
    assert "ASCII001_AMBIGUOUS_GLYPHS" in _codes("https://paypaI.co.in")


def test_leet_substitution_domain_is_flagged() -> None:
    assert "ASCII002_LEET_SUBSTITUTION" in _codes("https://micros0ft.com")


def test_leet_substitution_for_paypal_is_flagged() -> None:
    codes = _codes("https://paypa1.com")
    assert "ASCII002_LEET_SUBSTITUTION" in codes


def test_ascii_lookalike_respects_allowlist_domains() -> None:
    detector = AsciiLookalikeDetector()
    findings = detector.analyze(
        AnalysisInput(
            input_type="url",
            content="https://paypaI.com",
            metadata={"allowlist_domains": ["paypai.com"]},
        )
    )
    assert findings == []


def test_ascii_lookalike_allowlist_finding_can_suppress_single_code() -> None:
    detector = AsciiLookalikeDetector()
    findings = detector.analyze(
        AnalysisInput(
            input_type="url",
            content="https://paypaI.com",
            metadata={
                "allowlist_domains": ["paypai.com"],
                "allowlist_categories": ["NONE"],
                "allowlist_findings": ["ASCII001_AMBIGUOUS_GLYPHS"],
            },
        )
    )
    assert findings == []


def test_ascii_lookalike_allowlist_finding_does_not_blanket_category() -> None:
    detector = AsciiLookalikeDetector()
    findings = detector.analyze(
        AnalysisInput(
            input_type="url",
            content="https://paypaI.com",
            metadata={
                "allowlist_domains": ["paypai.com"],
                "allowlist_categories": ["NONE"],
                "allowlist_findings": ["ASCII002_LEET_SUBSTITUTION"],
            },
        )
    )
    assert any(finding.category == "ASCII001_AMBIGUOUS_GLYPHS" for finding in findings)


@pytest.mark.parametrize(
    ("url", "expected_code"),
    [
        ("https://paypaI.co.uk", "ASCII001_AMBIGUOUS_GLYPHS"),
        ("https://paypa1.com.au", "ASCII002_LEET_SUBSTITUTION"),
        ("https://micros0ft.co.jp", "ASCII002_LEET_SUBSTITUTION"),
    ],
)
def test_ascii_lookalike_brand_calibration_across_suffixes(
    url: str,
    expected_code: str,
) -> None:
    assert expected_code in _codes(url)
