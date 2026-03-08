"""Domain allowlist helpers for reducing false positives."""

from __future__ import annotations

from collections.abc import Iterable
from urllib.parse import urlparse

from lsh.core.context import SuppressionTraceEvent, append_suppression_trace_event
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
    if "NONE" in normalized:
        normalized.discard("NONE")
        if not normalized:
            return set()
    if "ALL" in normalized:
        return set(SUPPORTED_ALLOWLIST_CATEGORY_PREFIXES)
    return {
        category for category in normalized if category in SUPPORTED_ALLOWLIST_CATEGORY_PREFIXES
    }


def allowlist_findings_for_input(analysis_input: AnalysisInput) -> set[str]:
    """Return finding-code tokens to suppress for allowlisted hostnames."""
    raw_value = analysis_input.metadata.get("allowlist_findings")
    if raw_value is None:
        return set()

    raw_findings: Iterable[str]
    if isinstance(raw_value, str):
        raw_findings = [part.strip() for part in raw_value.split(",")]
    elif isinstance(raw_value, list):
        raw_findings = [item for item in raw_value if isinstance(item, str)]
    else:
        return set()

    return {finding.strip().upper() for finding in raw_findings if finding.strip()}


def matching_allowlist_domain(hostname: str, allowlist_domains: set[str]) -> str | None:
    """Return the most specific allowlist domain that matches this hostname."""
    if not allowlist_domains:
        return None

    matches: set[str] = set()
    host_forms = _expanded_domain_forms(hostname)
    for host in host_forms:
        for allowed in allowlist_domains:
            if host == allowed or host.endswith(f".{allowed}"):
                matches.add(allowed)

    if not matches:
        return None

    return sorted(matches, key=lambda domain: (-len(domain), domain))[0]


def is_hostname_allowlisted(hostname: str, allowlist_domains: set[str]) -> bool:
    """Check exact/suffix match against allowlist with IDNA form expansion."""
    return matching_allowlist_domain(hostname, allowlist_domains) is not None


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
    matched_domain = matching_allowlist_domain(hostname, allowlist_domains)
    if matched_domain is None:
        return False

    categories = allowlist_category_prefixes_for_input(analysis_input)
    return category in categories


def _finding_token_matches(code: str, token: str) -> bool:
    """Return True when a finding token matches one finding code.

    Supported token forms:
    - exact code: HMG002_PUNYCODE_VISIBILITY
    - prefix stem: HMG002 (matches HMG002_*)
    - wildcard prefix: HMG002* (matches HMG002*)
    """
    if token.endswith("*"):
        return code.startswith(token.removesuffix("*"))
    if code == token:
        return True
    return code.startswith(f"{token}_")


def _matching_finding_token(code: str, finding_tokens: set[str]) -> str | None:
    for token in sorted(
        finding_tokens,
        key=lambda value: (-len(value.removesuffix("*")), value.endswith("*"), value),
    ):
        if _finding_token_matches(code, token):
            return token
    return None


def _record_suppression_event(
    analysis_input: AnalysisInput,
    *,
    module_name: str,
    hostname: str,
    finding_code: str,
    category_prefix: str,
    matched_allowlist_domain: str,
    suppression_scope: str,
    matched_rule: str,
) -> None:
    append_suppression_trace_event(
        analysis_input,
        SuppressionTraceEvent(
            module=module_name,
            finding_code=finding_code,
            category_prefix=category_prefix,
            hostname=hostname,
            matched_allowlist_domain=matched_allowlist_domain,
            suppression_scope=suppression_scope,
            matched_rule=matched_rule,
        ),
    )


def should_suppress_finding_for_allowlist(
    analysis_input: AnalysisInput,
    hostname: str,
    *,
    module_name: str | None = None,
    category_prefix: str,
    finding_code: str,
) -> bool:
    """Return True when hostname is allowlisted for category or finding-code scope."""
    category = category_prefix.strip().upper()
    if category not in SUPPORTED_ALLOWLIST_CATEGORY_PREFIXES:
        return False

    allowlist_domains = allowlist_domains_for_input(analysis_input)
    matched_domain = matching_allowlist_domain(hostname, allowlist_domains)
    if matched_domain is None:
        return False

    code = finding_code.strip().upper()
    if not code:
        return False

    resolved_module = module_name or category.lower()
    categories = allowlist_category_prefixes_for_input(analysis_input)
    if category in categories:
        _record_suppression_event(
            analysis_input,
            module_name=resolved_module,
            hostname=hostname,
            finding_code=code,
            category_prefix=category,
            matched_allowlist_domain=matched_domain,
            suppression_scope="category",
            matched_rule=category,
        )
        return True

    finding_tokens = allowlist_findings_for_input(analysis_input)
    matched_token = _matching_finding_token(code, finding_tokens)
    if matched_token is None:
        return False

    _record_suppression_event(
        analysis_input,
        module_name=resolved_module,
        hostname=hostname,
        finding_code=code,
        category_prefix=category,
        matched_allowlist_domain=matched_domain,
        suppression_scope="finding",
        matched_rule=matched_token,
    )
    return True
