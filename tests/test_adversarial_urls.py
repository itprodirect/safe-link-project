"""Adversarial URL detection test suite.

15 parametrized test cases covering obfuscated IPs, localhost aliases,
fragment deception, encoding evasion, mixed/compound attacks, and IPv6 evasion.
"""

from __future__ import annotations

import pytest

from lsh.core.models import AnalysisInput
from lsh.core.orchestrator import AnalysisOrchestrator
from lsh.modules import (
    AsciiLookalikeDetector,
    HomoglyphDetector,
    NetIPDetector,
    URLStructureDetector,
)

_ORCHESTRATOR = AnalysisOrchestrator(
    modules=[
        NetIPDetector(),
        URLStructureDetector(),
        AsciiLookalikeDetector(),
        HomoglyphDetector(),
    ]
)


def _analyze(url: str) -> set[str]:
    """Run URL through the detection pipeline and return triggered rule IDs."""
    result = _ORCHESTRATOR.analyze(
        AnalysisInput(input_type="url", content=url)
    )
    return {f.category for f in result.findings}


def _severity(url: str) -> int:
    """Run URL through detection and return overall risk score."""
    result = _ORCHESTRATOR.analyze(
        AnalysisInput(input_type="url", content=url)
    )
    return result.overall_risk


ADVERSARIAL_TESTS = [
    # -- Obfuscated IP addresses --
    ("http://2130706433", "NET003", "Integer IP (127.0.0.1)"),
    ("http://0177.0.0.1", "NET003", "Octal dotted-quad (127.0.0.1)"),
    ("http://0x7f.0x0.0x0.0x1", "NET003", "Hex dotted-quad (127.0.0.1)"),
    ("http://0x7f000001", "NET003", "Hex integer IP (127.0.0.1)"),
    ("http://127.1", "NET003", "Abbreviated IP (127.0.0.1)"),
    # -- Localhost variants --
    ("http://localhost", "NET004", "Localhost keyword"),
    ("http://localhost.localdomain", "NET004", "Localhost FQDN alias"),
    # -- Fragment-based deception --
    ("http://evil.com#@google.com", "URL004", "Fragment with @brand"),
    ("http://evil.com#https://paypal.com", "URL004", "Fragment with full URL"),
    # -- Encoding evasion --
    ("http://%65%76%69%6c.com", "URL005", "Fully percent-encoded hostname"),
    ("http://evil.com/%2e%2e/admin", "URL005", "Encoded path traversal"),
    ("http://evil.com%252Fgoogle.com", "URL005", "Double-encoded slash"),
    # -- Mixed / compound attacks --
    ("http://google.com:80@0x7f000001", "URL001+NET003", "Userinfo + hex IP"),
    ("http://0177.0.0.1:8080#@paypal.com", "NET003+URL004", "Octal IP + fragment deception"),
    # -- IPv6 evasion --
    ("http://[::ffff:127.0.0.1]", "NET005", "IPv6-mapped loopback"),
]


@pytest.mark.parametrize("url,expected_rules,description", ADVERSARIAL_TESTS)
def test_adversarial_detection(url: str, expected_rules: str, description: str) -> None:
    """Each adversarial URL must produce at least the expected rule IDs."""
    triggered = _analyze(url)

    for rule_prefix in expected_rules.split("+"):
        assert any(rule_prefix in r for r in triggered), (
            f"MISSED {rule_prefix} on: {url} ({description}). "
            f"Got: {triggered}"
        )


@pytest.mark.parametrize("url,expected_rules,description", ADVERSARIAL_TESTS)
def test_adversarial_nonzero_severity(
    url: str, expected_rules: str, description: str
) -> None:
    """Every adversarial URL must score > 0."""
    score = _severity(url)
    assert score > 0, f"Zero severity on known-bad URL: {url} ({description})"


class TestCompoundAttacks:
    """Verify compound attacks produce ALL expected rules."""

    def test_userinfo_plus_hex_ip(self) -> None:
        triggered = _analyze("http://google.com:80@0x7f000001")
        assert any("URL001" in r for r in triggered), f"Missing URL001, got {triggered}"
        assert any("NET003" in r for r in triggered), f"Missing NET003, got {triggered}"

    def test_octal_ip_plus_fragment(self) -> None:
        triggered = _analyze("http://0177.0.0.1:8080#@paypal.com")
        assert any("NET003" in r for r in triggered), f"Missing NET003, got {triggered}"
        assert any("URL004" in r for r in triggered), f"Missing URL004, got {triggered}"


class TestSeverityBands:
    """Verify severity band reasonableness for key adversarial URLs."""

    def test_userinfo_attack_is_medium_or_higher(self) -> None:
        score = _severity("http://google.com:80@evil.com")
        assert score >= 40, f"Expected >= MEDIUM for userinfo attack, got {score}"

    def test_localhost_is_low_or_higher(self) -> None:
        score = _severity("http://localhost")
        assert score >= 20, f"Expected >= LOW for localhost, got {score}"

    def test_clean_url_is_safe(self) -> None:
        score = _severity("https://google.com")
        assert score == 0, f"Expected 0 for clean URL, got {score}"
