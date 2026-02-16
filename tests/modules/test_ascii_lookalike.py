"""Focused tests for ASCII lookalike/leet brand impersonation patterns."""

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
