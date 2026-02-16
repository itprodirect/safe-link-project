"""Domain allowlist helpers for reducing false positives."""

from __future__ import annotations

from collections.abc import Iterable
from urllib.parse import urlparse

from lsh.core.models import AnalysisInput
from lsh.core.url_tools import normalize_hostname

SUPPORTED_ALLOWLIST_CATEGORY_PREFIXES = frozenset({"HMG", "ASCII", "URL", "NET"})
DEFAULT_ALLOWLIST_CATEGORY_PREFIXES = frozenset({"HMG", "ASCII"})


def _idna_ascii(hostname: str) -> str | None:
    try:
        return hostname.encode("idna").decode("ascii")
    except UnicodeError:
        return None


def _idna_unicode(hostname: str) -> str | None:
    try:
        return hostname.encode("ascii").decode("idna")
    except UnicodeError:
        return None


def _extract_raw_domain(entry: str) -> str | None:
    raw = entry.strip()
    if not raw:
        return None

    parsed = urlparse(raw if "://" in raw else f"//{raw}")
    hostname = parsed.hostname
    if hostname is None:
        candidate = raw.strip().strip("/").strip()
        if not candidate:
            return None
        return normalize_hostname(candidate)
    return normalize_hostname(hostname)


def _expanded_domain_forms(domain: str) -> set[str]:
    forms = {normalize_hostname(domain)}
    ascii_form = _idna_ascii(domain)
    if ascii_form is not None:
        forms.add(normalize_hostname(ascii_form))
    unicode_form = _idna_unicode(domain)
    if unicode_form is not None:
        forms.add(normalize_hostname(unicode_form))
    return {form for form in forms if form}


def allowlist_domains_for_input(analysis_input: AnalysisInput) -> set[str]:
    """Return normalized allowlist domains from input metadata."""
    raw_value = analysis_input.metadata.get("allowlist_domains")
    if raw_value is None:
        return set()

    raw_domains: Iterable[str]
    if isinstance(raw_value, str):
        raw_domains = [part.strip() for part in raw_value.split(",")]
    elif isinstance(raw_value, list):
        raw_domains = [item for item in raw_value if isinstance(item, str)]
    else:
        return set()

    normalized: set[str] = set()
    for entry in raw_domains:
        domain = _extract_raw_domain(entry)
        if domain is None:
            continue
        normalized.update(_expanded_domain_forms(domain))
    return normalized


def allowlist_category_prefixes_for_input(analysis_input: AnalysisInput) -> set[str]:
    """Return category prefixes that allowlist rules should suppress."""
    raw_value = analysis_input.metadata.get("allowlist_categories")
    if raw_value is None:
        return set(DEFAULT_ALLOWLIST_CATEGORY_PREFIXES)

    raw_categories: Iterable[str]
    if isinstance(raw_value, str):
        raw_categories = [part.strip() for part in raw_value.split(",")]
    elif isinstance(raw_value, list):
        raw_categories = [item for item in raw_value if isinstance(item, str)]
    else:
        return set(DEFAULT_ALLOWLIST_CATEGORY_PREFIXES)

    normalized = {category.strip().upper() for category in raw_categories if category.strip()}
    if "ALL" in normalized:
        return set(SUPPORTED_ALLOWLIST_CATEGORY_PREFIXES)
    return {
        category for category in normalized if category in SUPPORTED_ALLOWLIST_CATEGORY_PREFIXES
    }


def is_hostname_allowlisted(hostname: str, allowlist_domains: set[str]) -> bool:
    """Check exact/suffix match against allowlist with IDNA form expansion."""
    if not allowlist_domains:
        return False

    host_forms = _expanded_domain_forms(hostname)
    for host in host_forms:
        for allowed in allowlist_domains:
            if host == allowed or host.endswith(f".{allowed}"):
                return True
    return False


def should_suppress_for_allowlist(
    analysis_input: AnalysisInput,
    hostname: str,
    *,
    category_prefix: str,
) -> bool:
    """Return True when hostname is allowlisted for this category prefix."""
    category = category_prefix.strip().upper()
    if category not in SUPPORTED_ALLOWLIST_CATEGORY_PREFIXES:
        return False

    allowlist_domains = allowlist_domains_for_input(analysis_input)
    if not is_hostname_allowlisted(hostname, allowlist_domains):
        return False

    categories = allowlist_category_prefixes_for_input(analysis_input)
    return category in categories
