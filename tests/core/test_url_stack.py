"""Integration tests for the current URL analysis module stack."""

from lsh.core.models import AnalysisInput
from lsh.core.orchestrator import AnalysisOrchestrator
from lsh.modules import (
    AsciiLookalikeDetector,
    HomoglyphDetector,
    NetIPDetector,
    RedirectChainDetector,
    URLStructureDetector,
)


def _url_stack() -> AnalysisOrchestrator:
    return AnalysisOrchestrator(
        modules=[
            NetIPDetector(),
            URLStructureDetector(),
            AsciiLookalikeDetector(),
            HomoglyphDetector(),
            RedirectChainDetector(),
        ]
    )


def _codes_for(url: str) -> set[str]:
    result = _url_stack().analyze(AnalysisInput(input_type="url", content=url))
    return {finding.category for finding in result.findings}


def test_private_ip_uses_net_category_not_homoglyph_confusable() -> None:
    codes = _codes_for("http://127.0.0.1")
    assert "NET001_PRIVATE_IP_LITERAL" in codes
    assert "HMG004_CONFUSABLE_CHARACTERS" not in codes


def test_ascii_spoof_patterns_are_detected_with_ascii_categories() -> None:
    paypai_codes = _codes_for("https://paypaI.com")
    assert "ASCII001_AMBIGUOUS_GLYPHS" in paypai_codes
    assert "HMG004_CONFUSABLE_CHARACTERS" not in paypai_codes

    micros0ft_codes = _codes_for("https://micros0ft.com")
    assert "ASCII002_LEET_SUBSTITUTION" in micros0ft_codes
    assert "HMG004_CONFUSABLE_CHARACTERS" not in micros0ft_codes

    paypa1_codes = _codes_for("https://paypa1.com")
    assert "ASCII002_LEET_SUBSTITUTION" in paypa1_codes
    assert "HMG004_CONFUSABLE_CHARACTERS" not in paypa1_codes
