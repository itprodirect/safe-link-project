"""Shared per-analysis runtime context and URL preprocessing helpers."""

from __future__ import annotations

from dataclasses import dataclass
from ipaddress import IPv4Address
from typing import cast
from urllib.parse import ParseResult

from lsh.core.models import AnalysisInput, NormalizedURL
from lsh.core.normalizer import normalize_url, parse_host_to_ipv4, resolve_ipv6_mapped_v4
from lsh.core.url_tools import (
    IPAddress,
    normalize_hostname,
    parse_ip_literal,
    parse_url_like,
    registrable_domain,
)


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


@dataclass(slots=True)
class URLAnalysisContext:
    """Preprocessed URL context shared across modules for one analysis run."""

    raw_url: str
    raw_parsed: ParseResult
    normalized_url: NormalizedURL
    canonical_parsed: ParseResult
    hostname: str | None
    registrable_domain: str | None
    canonical_hostname: str | None
    canonical_registrable_domain: str | None
    idna_ascii_hostname: str | None
    idna_unicode_hostname: str | None
    ip_literal: IPAddress | None
    obfuscated_ipv4: IPv4Address | None
    obfuscated_ipv4_notes: tuple[str, ...]
    ipv6_mapped_ipv4: IPv4Address | None


@dataclass(slots=True)
class AnalysisRuntimeContext:
    """Runtime-only context attached to `AnalysisInput` (not serialized)."""

    url: URLAnalysisContext | None = None


def _build_url_context(raw_url: str) -> URLAnalysisContext:
    raw_parsed = parse_url_like(raw_url)
    normalized = normalize_url(raw_url)
    canonical_parsed = parse_url_like(normalized.canonical)

    hostname: str | None = None
    registrable: str | None = None
    raw_hostname = raw_parsed.hostname
    if raw_hostname is not None:
        hostname = normalize_hostname(raw_hostname)
        registrable = registrable_domain(hostname)

    canonical_hostname: str | None = None
    canonical_registrable: str | None = None
    if normalized.canonical_host:
        canonical_hostname = normalize_hostname(normalized.canonical_host)
        canonical_registrable = registrable_domain(canonical_hostname)

    ip_literal = parse_ip_literal(hostname) if hostname is not None else None

    obfuscated_ipv4: IPv4Address | None = None
    obfuscated_notes: list[str] = []
    if hostname is not None:
        obfuscated_ipv4, obfuscated_notes = parse_host_to_ipv4(hostname)

    ipv6_mapped_ipv4: IPv4Address | None = None
    if hostname is not None:
        ipv6_mapped_ipv4, _mapped_notes = resolve_ipv6_mapped_v4(hostname)

    return URLAnalysisContext(
        raw_url=raw_url,
        raw_parsed=raw_parsed,
        normalized_url=normalized,
        canonical_parsed=canonical_parsed,
        hostname=hostname,
        registrable_domain=registrable,
        canonical_hostname=canonical_hostname,
        canonical_registrable_domain=canonical_registrable,
        idna_ascii_hostname=_idna_ascii(hostname) if hostname is not None else None,
        idna_unicode_hostname=_idna_unicode(hostname) if hostname is not None else None,
        ip_literal=ip_literal,
        obfuscated_ipv4=obfuscated_ipv4,
        obfuscated_ipv4_notes=tuple(obfuscated_notes),
        ipv6_mapped_ipv4=ipv6_mapped_ipv4,
    )


def build_runtime_context(analysis_input: AnalysisInput) -> AnalysisRuntimeContext:
    """Build runtime context for one analysis input."""
    if analysis_input.input_type != "url":
        return AnalysisRuntimeContext()
    return AnalysisRuntimeContext(url=_build_url_context(analysis_input.content))


def set_runtime_context(
    analysis_input: AnalysisInput,
    context: AnalysisRuntimeContext | None,
) -> None:
    """Attach runtime context to an analysis input (runtime-only; not serialized)."""
    analysis_input._runtime_context = context


def get_runtime_context(analysis_input: AnalysisInput) -> AnalysisRuntimeContext | None:
    """Return attached runtime context if present."""
    context = analysis_input._runtime_context
    if context is None:
        return None
    return cast(AnalysisRuntimeContext, context)


def url_context_for_input(analysis_input: AnalysisInput) -> URLAnalysisContext | None:
    """Return cached URL context, building and attaching it on first access."""
    if analysis_input.input_type != "url":
        return None

    runtime_context = get_runtime_context(analysis_input)
    if runtime_context is None:
        runtime_context = build_runtime_context(analysis_input)
        set_runtime_context(analysis_input, runtime_context)
    return runtime_context.url

