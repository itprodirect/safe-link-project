"""Shared detection constants used across URL analysis modules."""

from __future__ import annotations

# A compact, high-signal seed set for offline brand-style spoof heuristics.
KNOWN_BRAND_TOKENS = frozenset(
    {
        "google",
        "paypal",
        "apple",
        "microsoft",
        "amazon",
        "facebook",
        "instagram",
        "netflix",
        "openai",
        "chase",
        "wellsfargo",
        "bankofamerica",
    }
)

# Extra "looks trusted" tokens commonly used in deceptive host prefixes.
DECEPTIVE_PREFIX_HINTS = frozenset(
    {
        "login",
        "secure",
        "verify",
        "update",
        "account",
        "signin",
        "support",
        "billing",
    }
)

# Common redirect-style parameters that carry nested destinations.
NESTED_URL_PARAM_KEYS = frozenset(
    {
        "url",
        "u",
        "next",
        "continue",
        "redirect",
        "redirect_url",
        "return",
        "return_url",
        "target",
        "destination",
        "dest",
        "to",
        "r",
    }
)

# Common second-level labels used under country-code TLDs (for example co.in, com.au).
COMMON_COUNTRY_SECOND_LEVEL_LABELS = frozenset(
    {
        "ac",
        "co",
        "com",
        "edu",
        "gov",
        "mil",
        "net",
        "org",
    }
)

# Fallback multi-part suffixes used by registrable-domain extraction heuristics.
COMMON_MULTI_PART_SUFFIXES = frozenset(
    {
        "co.uk",
        "org.uk",
        "ac.uk",
        "gov.uk",
        "com.au",
        "net.au",
        "org.au",
        "co.nz",
        "com.br",
        "com.mx",
        "co.jp",
        "co.kr",
        "com.sg",
        "com.tr",
        "com.cn",
        "com.hk",
    }
)

# Character groups with common visual ambiguity in ASCII domains.
ASCII_AMBIGUOUS_GROUPS: tuple[tuple[str, ...], ...] = (
    ("i", "l", "1"),
    ("o", "0"),
    ("s", "5"),
)

# Conservative leet substitutions for brand-style impersonation checks.
ASCII_LEET_SUBSTITUTIONS: dict[str, str] = {
    "0": "o",
    "1": "l",
    "3": "e",
    "4": "a",
    "5": "s",
    "7": "t",
    "8": "b",
}

__all__ = [
    "ASCII_AMBIGUOUS_GROUPS",
    "ASCII_LEET_SUBSTITUTIONS",
    "COMMON_COUNTRY_SECOND_LEVEL_LABELS",
    "COMMON_MULTI_PART_SUFFIXES",
    "DECEPTIVE_PREFIX_HINTS",
    "KNOWN_BRAND_TOKENS",
    "NESTED_URL_PARAM_KEYS",
]
