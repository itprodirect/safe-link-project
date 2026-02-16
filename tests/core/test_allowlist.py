"""Tests for allowlist normalization and scoped suppression behavior."""

from lsh.core.allowlist import (
    allowlist_category_prefixes_for_input,
    should_suppress_for_allowlist,
)
from lsh.core.models import AnalysisInput


def test_allowlist_defaults_to_hmg_and_ascii_categories() -> None:
    analysis_input = AnalysisInput(
        input_type="url",
        content="https://paypaI.com",
        metadata={"allowlist_domains": ["paypai.com"]},
    )
    categories = allowlist_category_prefixes_for_input(analysis_input)
    assert categories == {"HMG", "ASCII"}

    assert should_suppress_for_allowlist(analysis_input, "paypai.com", category_prefix="HMG")
    assert not should_suppress_for_allowlist(analysis_input, "paypai.com", category_prefix="URL")


def test_allowlist_all_category_enables_url_and_net_suppression() -> None:
    analysis_input = AnalysisInput(
        input_type="url",
        content="https://login.google.com.evil.com",
        metadata={
            "allowlist_domains": ["evil.com", "8.8.8.8"],
            "allowlist_categories": ["ALL"],
        },
    )
    assert should_suppress_for_allowlist(
        analysis_input,
        "login.google.com.evil.com",
        category_prefix="URL",
    )
    assert should_suppress_for_allowlist(analysis_input, "8.8.8.8", category_prefix="NET")


def test_allowlist_supports_unicode_and_punycode_forms() -> None:
    analysis_input = AnalysisInput(
        input_type="url",
        content="https://xn--pple-43d.com",
        metadata={"allowlist_domains": ["\u0430pple.com"], "allowlist_categories": ["HMG"]},
    )
    assert should_suppress_for_allowlist(analysis_input, "xn--pple-43d.com", category_prefix="HMG")
