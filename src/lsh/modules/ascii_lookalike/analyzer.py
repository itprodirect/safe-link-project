"""ASCII lookalike detector for common brand impersonation tricks."""

from __future__ import annotations

from lsh.core.allowlist import allowlist_domains_for_input, is_hostname_allowlisted
from lsh.core.models import (
    AnalysisInput,
    Confidence,
    Evidence,
    Finding,
    ModuleInterface,
    Severity,
)
from lsh.core.rules import ASCII_AMBIGUOUS_GROUPS, ASCII_LEET_SUBSTITUTIONS, KNOWN_BRAND_TOKENS
from lsh.core.url_tools import extract_hostname, parse_ip_literal, registrable_domain


def _primary_label(hostname: str) -> str:
    """Return the registrable-domain label used for brand-like checks."""
    labels = [label for label in registrable_domain(hostname).split(".") if label]
    return labels[0] if labels else hostname


def _single_swap_ambiguous_candidates(label: str) -> set[str]:
    """Generate candidate labels by swapping one visually ambiguous ASCII glyph."""
    candidates: set[str] = set()
    for index, character in enumerate(label):
        if character.isdigit():
            continue
        for group in ASCII_AMBIGUOUS_GROUPS:
            if character not in group:
                continue
            for replacement in group:
                if replacement.isdigit():
                    continue
                if replacement == character:
                    continue
                candidates.add(f"{label[:index]}{replacement}{label[index + 1:]}")
            break
    return candidates


def _leet_normalized(label: str) -> tuple[str, bool]:
    """Apply conservative leet substitutions to a label."""
    changed = False
    transformed: list[str] = []
    for character in label:
        replacement = ASCII_LEET_SUBSTITUTIONS.get(character, character)
        if replacement != character:
            changed = True
        transformed.append(replacement)
    return "".join(transformed), changed


class AsciiLookalikeDetector(ModuleInterface):
    """Detect ASCII-only glyph substitutions that mimic common brands."""

    @property
    def name(self) -> str:
        return "ascii_lookalike"

    @property
    def version(self) -> str:
        return "0.1.0"

    def analyze(self, input: AnalysisInput) -> list[Finding]:
        if input.input_type != "url":
            return []

        hostname = extract_hostname(input.content)
        if hostname is None:
            return []
        if is_hostname_allowlisted(hostname, allowlist_domains_for_input(input)):
            return []

        if parse_ip_literal(hostname) is not None:
            return []
        if not hostname.isascii():
            return []

        primary_label = _primary_label(hostname).replace("-", "")
        if len(primary_label) < 4:
            return []
        if not any(character.isalpha() for character in primary_label):
            return []

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
                        Evidence(label="Hostname", value=hostname),
                        Evidence(label="Primary Label", value=primary_label),
                        Evidence(label="Risk Delta", value=f"+{risk_delta}"),
                        Evidence(label="Cumulative Risk", value=str(cumulative_risk)),
                        *extra_evidence,
                    ],
                    recommendations=recommendations,
                )
            )

        ambiguous_matches = sorted(
            candidate
            for candidate in _single_swap_ambiguous_candidates(primary_label)
            if candidate in KNOWN_BRAND_TOKENS and candidate != primary_label
        )
        if ambiguous_matches:
            add_finding(
                code="ASCII001_AMBIGUOUS_GLYPHS",
                risk_delta=25,
                confidence=Confidence.MEDIUM,
                title="ASCII glyph ambiguity resembles a common brand",
                explanation=(
                    "The registrable domain label differs by one ambiguous ASCII glyph "
                    "(for example i/l/1) from a known brand token."
                ),
                family_explanation=(
                    "This link uses lookalike English letters or numbers that can imitate "
                    "a familiar website name."
                ),
                extra_evidence=[
                    Evidence(label="Likely Brand Target", value=ambiguous_matches[0])
                ],
                recommendations=[
                    "Do not rely on visual similarity alone for brand names.",
                    "Open the known site from a trusted bookmark instead.",
                ],
            )

        leet_label, changed = _leet_normalized(primary_label)
        if changed and leet_label in KNOWN_BRAND_TOKENS and leet_label != primary_label:
            add_finding(
                code="ASCII002_LEET_SUBSTITUTION",
                risk_delta=30,
                confidence=Confidence.MEDIUM,
                title="Digit-to-letter substitution resembles a common brand",
                explanation=(
                    "The domain label uses digit substitutions (for example 0->o or 1->l) "
                    "that normalize to a known brand token."
                ),
                family_explanation=(
                    "This link swaps numbers for letters to look like a trusted brand."
                ),
                extra_evidence=[
                    Evidence(label="Leet-Normalized Label", value=leet_label),
                ],
                recommendations=[
                    "Treat number-swapped brand names as suspicious.",
                    "Type the official website address yourself before signing in.",
                ],
            )

        return findings
