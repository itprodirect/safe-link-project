"""Homoglyph and IDN detector."""

from __future__ import annotations

import unicodedata
from typing import Any

from lsh.core.allowlist import should_suppress_for_allowlist
from lsh.core.models import AnalysisInput, Confidence, Evidence, Finding, ModuleInterface, Severity
from lsh.core.url_tools import extract_hostname, parse_ip_literal

try:
    import confusables  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover - exercised when optional dependency is missing
    confusables = None

_PUNYCODE_PREFIX = "xn--"
_SCRIPT_NAME_MAP: tuple[tuple[str, str], ...] = (
    ("LATIN", "Latin"),
    ("CYRILLIC", "Cyrillic"),
    ("GREEK", "Greek"),
    ("ARABIC", "Arabic"),
    ("HEBREW", "Hebrew"),
    ("DEVANAGARI", "Devanagari"),
    ("HIRAGANA", "Hiragana"),
    ("KATAKANA", "Katakana"),
    ("HANGUL", "Hangul"),
    ("CJK UNIFIED IDEOGRAPH", "Han"),
)
_MAX_LOOKALIKE_FORMS = 3
_MAX_CHAR_MAPPING_EVIDENCE = 3


def _idna_to_ascii(hostname: str) -> str | None:
    """Convert a hostname to its IDNA ASCII form."""
    try:
        return hostname.encode("idna").decode("ascii")
    except UnicodeError:
        return None


def _idna_to_unicode(hostname: str) -> str | None:
    """Convert an ASCII IDNA hostname to Unicode."""
    try:
        return hostname.encode("ascii").decode("idna")
    except UnicodeError:
        return None


def _contains_punycode_label(hostname: str) -> bool:
    """Return True when any label starts with xn--."""
    return any(label.startswith(_PUNYCODE_PREFIX) for label in hostname.split("."))


def _has_non_ascii(hostname: str) -> bool:
    """Return True if the hostname contains non-ASCII characters."""
    return any(not character.isascii() for character in hostname)


def _script_for_character(character: str) -> str | None:
    """Map a Unicode character to a broad script group."""
    if not character.isalpha():
        return None

    name = unicodedata.name(character, "")
    for keyword, script in _SCRIPT_NAME_MAP:
        if keyword in name:
            return script
    return "Other"


def _scripts_for_label(label: str) -> set[str]:
    """Collect scripts that appear in one domain label."""
    scripts: set[str] = set()
    for character in label:
        script = _script_for_character(character)
        if script is not None:
            scripts.add(script)
    return scripts


def _mixed_script_labels(hostname: str) -> list[tuple[str, list[str]]]:
    """Return labels that mix scripts (e.g., Latin + Cyrillic)."""
    mixed: list[tuple[str, list[str]]] = []
    for label in hostname.split("."):
        scripts = sorted(_scripts_for_label(label))
        if len(scripts) >= 2:
            mixed.append((label, scripts))
    return mixed


def _ascii_lookalike_forms(hostname: str) -> list[str]:
    """Generate ASCII lookalike forms using the confusables package."""
    if confusables is None:
        return []

    raw_forms: list[Any] = confusables.normalize(hostname, prioritize_alpha=True)
    forms: list[str] = []
    seen: set[str] = set()
    for raw_form in raw_forms:
        if not isinstance(raw_form, str):
            continue
        candidate = raw_form.lower()
        if not candidate.isascii():
            continue
        if candidate in seen:
            continue
        seen.add(candidate)
        forms.append(candidate)
    return forms


def _confusable_character_examples(hostname: str) -> list[str]:
    """Return a small set of per-character confusable mappings."""
    if confusables is None:
        return []

    examples: list[str] = []
    for character in hostname:
        if character == "." or character.isascii():
            continue

        raw_mappings: Any = confusables.confusable_characters(character)
        if not isinstance(raw_mappings, list):
            continue

        ascii_matches = sorted(
            {
                candidate.lower()
                for candidate in raw_mappings
                if isinstance(candidate, str) and candidate.isascii() and candidate.isalnum()
            }
        )
        if not ascii_matches:
            continue

        examples.append(f"{character} -> {', '.join(ascii_matches[:4])}")
        if len(examples) >= _MAX_CHAR_MAPPING_EVIDENCE:
            break

    return examples


class HomoglyphDetector(ModuleInterface):
    """Analyze URL hostnames for IDN/homoglyph tricks."""

    @property
    def name(self) -> str:
        return "homoglyph"

    @property
    def version(self) -> str:
        return "0.1.0"

    def analyze(self, input: AnalysisInput) -> list[Finding]:
        if input.input_type != "url":
            return []

        hostname = extract_hostname(input.content)
        if hostname is None:
            return [
                Finding(
                    module=self.name,
                    category="HMG000_INVALID_URL",
                    severity=Severity.INFO,
                    confidence=Confidence.LOW,
                    risk_score=10,
                    title="Could not extract a hostname from input",
                    explanation="URL parsing failed, so hostname safety checks could not run.",
                    family_explanation=(
                        "This link could not be read correctly, so safety checks are incomplete."
                    ),
                    evidence=[Evidence(label="Input", value=input.content)],
                    recommendations=[
                        "Double-check the full link format before opening it.",
                        "If this came from a message, ask the sender to resend the exact URL.",
                    ],
                )
            ]
        if parse_ip_literal(hostname) is not None:
            return []
        if should_suppress_for_allowlist(input, hostname, category_prefix="HMG"):
            return []

        unicode_hostname = _idna_to_unicode(hostname) or hostname
        unicode_hostname = unicode_hostname.lower()
        idna_ascii_hostname = _idna_to_ascii(unicode_hostname) or hostname

        findings: list[Finding] = []
        cumulative_risk = 0

        def add_finding(
            *,
            code: str,
            risk_delta: int,
            confidence: Confidence,
            title: str,
            explanation: str,
            family_explanation: str,
            extra_evidence: list[Evidence],
            recommendations: list[str],
        ) -> None:
            nonlocal cumulative_risk
            cumulative_risk = min(100, cumulative_risk + risk_delta)
            findings.append(
                Finding(
                    module=self.name,
                    category=code,
                    severity=Severity.INFO,
                    confidence=confidence,
                    risk_score=cumulative_risk,
                    title=title,
                    explanation=explanation,
                    family_explanation=family_explanation,
                    evidence=[
                        Evidence(label="Hostname", value=unicode_hostname),
                        Evidence(label="Hostname (idna)", value=idna_ascii_hostname),
                        Evidence(label="Risk Delta", value=f"+{risk_delta}"),
                        Evidence(label="Cumulative Risk", value=str(cumulative_risk)),
                        *extra_evidence,
                    ],
                    recommendations=recommendations,
                )
            )

        if _has_non_ascii(unicode_hostname):
            add_finding(
                code="HMG001_NON_ASCII_HOSTNAME",
                risk_delta=25,
                confidence=Confidence.MEDIUM,
                title="Hostname contains non-ASCII characters",
                explanation=(
                    "The domain includes Unicode characters, so visual lookalike checks are needed "
                    "to rule out IDN spoofing."
                ),
                family_explanation=(
                    "This web address uses unusual letters. "
                    "Some scam links use this trick to look real."
                ),
                extra_evidence=[
                    Evidence(
                        label="Signal",
                        value="At least one hostname character is outside ASCII.",
                    )
                ],
                recommendations=[
                    "Pause before opening this link.",
                    "For important accounts, type the known website address yourself.",
                ],
            )

        if _contains_punycode_label(hostname) or _contains_punycode_label(idna_ascii_hostname):
            add_finding(
                code="HMG002_PUNYCODE_VISIBILITY",
                risk_delta=15,
                confidence=Confidence.LOW,
                title="IDN punycode form is present",
                explanation=(
                    "IDNA conversion shows a punycode hostname. "
                    "This does not prove malicious intent, "
                    "but it can hide lookalike Unicode characters."
                ),
                family_explanation=(
                    "This link has a hidden technical form (`xn--...`) "
                    "often used with lookalike text."
                ),
                extra_evidence=[
                    Evidence(label="Input Hostname", value=hostname),
                    Evidence(label="Unicode View", value=unicode_hostname),
                    Evidence(label="Punycode View", value=idna_ascii_hostname),
                ],
                recommendations=[
                    "Compare the website name carefully before clicking.",
                    "Open trusted sites by typing their address directly.",
                ],
            )

        mixed_labels = _mixed_script_labels(unicode_hostname)
        if mixed_labels:
            mixed_script_set = {script for _, scripts in mixed_labels for script in scripts}
            if {"Latin", "Cyrillic"}.issubset(mixed_script_set):
                risk_delta = 35
            elif "Latin" in mixed_script_set:
                risk_delta = 30
            else:
                risk_delta = 20

            label_descriptions = [
                f"{label} ({', '.join(scripts)})" for label, scripts in mixed_labels
            ]
            add_finding(
                code="HMG003_MIXED_SCRIPT_HOSTNAME",
                risk_delta=risk_delta,
                confidence=Confidence.HIGH,
                title="Hostname label mixes writing systems",
                explanation=(
                    "One or more domain labels mix scripts (for example Latin + Cyrillic), "
                    "which is a common homoglyph phishing pattern."
                ),
                family_explanation=(
                    "This link mixes different alphabets in one word to look like a known website."
                ),
                extra_evidence=[
                    Evidence(label="Label Scripts", value="; ".join(label_descriptions))
                ],
                recommendations=[
                    "Do not sign in from this link.",
                    "Verify the destination through a trusted app or bookmark.",
                ],
            )

        lookalike_forms = [
            form for form in _ascii_lookalike_forms(unicode_hostname) if form != unicode_hostname
        ]
        if _has_non_ascii(unicode_hostname) and lookalike_forms:
            evidence = [Evidence(label="ASCII Lookalike", value=lookalike_forms[0])]
            for extra_form in lookalike_forms[1:_MAX_LOOKALIKE_FORMS]:
                evidence.append(Evidence(label="Alternate Lookalike", value=extra_form))

            for mapping in _confusable_character_examples(unicode_hostname):
                evidence.append(Evidence(label="Character Mapping", value=mapping))

            add_finding(
                code="HMG004_CONFUSABLE_CHARACTERS",
                risk_delta=25,
                confidence=Confidence.HIGH,
                title="Confusable hostname characters detected",
                explanation=(
                    "Unicode confusable analysis found hostname characters that can be read as "
                    "different ASCII letters/numbers."
                ),
                family_explanation=(
                    "Some letters in this link can be mistaken "
                    "for normal English letters or numbers."
                ),
                extra_evidence=evidence,
                recommendations=[
                    "Treat this as suspicious until confirmed by a trusted source.",
                    "Use official bookmarks for banking, shopping, and email logins.",
                ],
            )

        return findings
