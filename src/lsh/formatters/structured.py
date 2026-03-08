"""Structured response payload builders reusable across CLI and API adapters."""

from __future__ import annotations

import re

from lsh.core.allowlist import (
    allowlist_category_prefixes_for_input,
    allowlist_domains_for_input,
    allowlist_findings_for_input,
)
from lsh.core.context import get_runtime_context, url_context_for_input
from lsh.core.models import AnalysisResult, Finding
from lsh.core.url_tools import extract_hostname, registrable_domain, registrable_labels
from lsh.formatters.family import build_family_view

_COMPARE_TOKEN_PATTERN = re.compile(r"[^a-z0-9]+")
_RISK_DELTA_PATTERN = re.compile(r"^[+]?(?P<value>-?\d+)$")


def _analysis_result_payload(result: AnalysisResult) -> dict[str, object]:
    return result.model_dump(mode="json")


def _family_payload(result: AnalysisResult) -> dict[str, object]:
    view = build_family_view(result)
    return {
        "risk_score": view.risk_score,
        "severity": view.severity,
        "summary": view.summary,
        "signal_confidence": view.signal_confidence,
        "reasons": list(view.reasons),
        "recommendations": list(view.recommendations),
    }


def _compare_token(value: str) -> str:
    token = _COMPARE_TOKEN_PATTERN.sub("_", value.strip().lower()).strip("_")
    return token or "value"


def _stable_compare_key(base_key: str, seen_keys: dict[str, int]) -> str:
    occurrence = seen_keys.get(base_key, 0) + 1
    seen_keys[base_key] = occurrence
    if occurrence == 1:
        return base_key
    return f"{base_key}#{occurrence}"


def _evidence_payload(finding: Finding) -> tuple[list[dict[str, str]], dict[str, str]]:
    evidence_entries = []
    evidence_map: dict[str, str] = {}
    seen_keys: dict[str, int] = {}

    for evidence in finding.evidence:
        base_key = _compare_token(evidence.label)
        compare_key = _stable_compare_key(base_key, seen_keys)
        evidence_entries.append(
            {"key": compare_key, "label": evidence.label, "value": evidence.value}
        )
        evidence_map[compare_key] = evidence.value

    return evidence_entries, evidence_map


def _risk_delta_value(evidence_map: dict[str, str]) -> int | None:
    raw_value = evidence_map.get("risk_delta")
    if raw_value is None:
        return None
    match = _RISK_DELTA_PATTERN.match(raw_value.strip())
    if match is None:
        return None
    return int(match.group("value"))


def _finding_evidence_payload(result: AnalysisResult) -> list[dict[str, object]]:
    findings = sorted(
        result.findings,
        key=lambda finding: (-finding.risk_score, finding.module, finding.category, finding.title),
    )
    rows: list[dict[str, object]] = []
    seen_keys: dict[str, int] = {}

    for index, finding in enumerate(findings):
        finding_key = f"{finding.module}:{finding.category}"
        compare_key = _stable_compare_key(finding_key, seen_keys)
        evidence_entries, evidence_map = _evidence_payload(finding)
        rows.append(
            {
                "module": finding.module,
                "category": finding.category,
                "finding_key": finding_key,
                "compare_key": compare_key,
                "sort_index": index,
                "severity": finding.severity.value,
                "confidence": finding.confidence.value,
                "cumulative_risk_score": finding.risk_score,
                "risk_delta": _risk_delta_value(evidence_map),
                "title": finding.title,
                "explanation": finding.explanation,
                "family_explanation": finding.family_explanation,
                "recommendations": list(finding.recommendations),
                "evidence": evidence_entries,
                "evidence_map": evidence_map,
            }
        )

    return rows


def _split_chain(value: str | None) -> list[str]:
    if not value:
        return []
    return [segment.strip() for segment in value.split(" -> ") if segment.strip()]


def _redirect_trace_payload(result: AnalysisResult) -> dict[str, object] | None:
    redirect_findings = [finding for finding in result.findings if finding.module == "redirect"]
    if not redirect_findings:
        return None

    chain: list[str] = []
    start_url: str | None = None
    final_url: str | None = None
    registrable_domain_path: list[str] = []
    hop_count = 0
    loop_target: str | None = None
    request_error: str | None = None

    for finding in redirect_findings:
        evidence_map = {evidence.label: evidence.value for evidence in finding.evidence}
        if not chain:
            chain = _split_chain(evidence_map.get("Chain"))
        if start_url is None:
            start_url = evidence_map.get("Start URL")
        if final_url is None:
            final_url = evidence_map.get("Final URL")
        if not registrable_domain_path:
            registrable_domain_path = _split_chain(evidence_map.get("Domain Path"))
        if hop_count == 0:
            raw_hops = evidence_map.get("Redirect Hops")
            if raw_hops is not None:
                try:
                    hop_count = int(raw_hops)
                except ValueError:
                    hop_count = 0
        if loop_target is None:
            loop_target = evidence_map.get("Loop Target")
        if request_error is None:
            request_error = evidence_map.get("Error")

    if not chain:
        chain = [value for value in (start_url, final_url) if value]
    if chain:
        start_url = start_url or chain[0]
        final_url = final_url or chain[-1]
        hop_count = max(hop_count, len(chain) - 1)

    if not registrable_domain_path and chain:
        for url in chain:
            hostname = extract_hostname(url)
            if hostname is None:
                continue
            registrable_domain_path.append(registrable_domain(hostname))

    if start_url is None or final_url is None:
        return None

    categories = {finding.category for finding in redirect_findings}
    return {
        "hops": chain,
        "start_url": start_url,
        "final_url": final_url,
        "registrable_domain_path": registrable_domain_path,
        "hop_count": hop_count,
        "crosses_registrable_domain": "RED002_CROSS_DOMAIN_REDIRECT" in categories
        or len({domain for domain in registrable_domain_path if domain}) >= 2,
        "max_hops_reached": "RED003_MAX_HOPS_REACHED" in categories,
        "timed_out": "RED005_REQUEST_TIMEOUT" in categories,
        "loop_target": loop_target,
        "request_error": request_error,
    }


def _domain_anatomy_payload(result: AnalysisResult) -> dict[str, object] | None:
    url_context = url_context_for_input(result.input)
    if url_context is None:
        return None

    hostname_labels = [label for label in (url_context.hostname or "").split(".") if label]
    registrable = url_context.registrable_domain or ""
    registrable_parts = registrable_labels(registrable) if registrable else []
    registrable_label_count = len(registrable_parts)
    if registrable_label_count and len(hostname_labels) > registrable_label_count:
        subdomain_labels = hostname_labels[:-registrable_label_count]
    else:
        subdomain_labels = []

    return {
        "submitted_url": url_context.raw_url,
        "canonical_url": url_context.normalized_url.canonical,
        "hostname": url_context.hostname,
        "canonical_hostname": url_context.canonical_hostname,
        "registrable_domain": url_context.registrable_domain,
        "canonical_registrable_domain": url_context.canonical_registrable_domain,
        "subdomain_labels": subdomain_labels,
        "registrable_labels": registrable_parts,
        "idna_ascii_hostname": url_context.idna_ascii_hostname,
        "idna_unicode_hostname": url_context.idna_unicode_hostname,
        "is_ip_literal": url_context.ip_literal is not None,
        "ip_literal": str(url_context.ip_literal) if url_context.ip_literal is not None else None,
        "obfuscated_ipv4": (
            str(url_context.obfuscated_ipv4) if url_context.obfuscated_ipv4 is not None else None
        ),
        "obfuscated_ipv4_notes": list(url_context.obfuscated_ipv4_notes),
        "ipv6_mapped_ipv4": (
            str(url_context.ipv6_mapped_ipv4) if url_context.ipv6_mapped_ipv4 is not None else None
        ),
        "normalization_notes": list(url_context.normalized_url.normalization_notes),
    }


def _suppression_reason(scope: str, *, matched_rule: str) -> str:
    if scope == "category":
        return (
            "Suppressed because the hostname matched an allowlist domain and "
            f"category prefix {matched_rule} was enabled."
        )
    return (
        "Suppressed because the hostname matched an allowlist domain and "
        f"finding token {matched_rule} was enabled."
    )


def _suppression_rows_payload(result: AnalysisResult) -> list[dict[str, object]]:
    runtime_context = get_runtime_context(result.input)
    suppressed_events = [] if runtime_context is None else list(runtime_context.suppressed_findings)
    seen_keys: dict[str, int] = {}
    rows: list[dict[str, object]] = []

    for index, event in enumerate(
        sorted(
            suppressed_events,
            key=lambda value: (value.module, value.finding_code, value.matched_rule),
        )
    ):
        finding_key = f"{event.module}:{event.finding_code}"
        base_compare_key = (
            f"{finding_key}:{event.suppression_scope}:{_compare_token(event.matched_rule)}"
        )
        compare_key = _stable_compare_key(base_compare_key, seen_keys)
        rows.append(
            {
                "module": event.module,
                "category": event.finding_code,
                "finding_key": finding_key,
                "compare_key": compare_key,
                "sort_index": index,
                "hostname": event.hostname,
                "matched_allowlist_domain": event.matched_allowlist_domain,
                "suppression_scope": event.suppression_scope,
                "matched_rule": event.matched_rule,
                "reason": _suppression_reason(
                    event.suppression_scope,
                    matched_rule=event.matched_rule,
                ),
            }
        )

    return rows


def _suppression_trace_payload(result: AnalysisResult) -> dict[str, object] | None:
    url_context = url_context_for_input(result.input)
    configured_domains = sorted(allowlist_domains_for_input(result.input))
    if not configured_domains:
        return None

    configured_categories = sorted(allowlist_category_prefixes_for_input(result.input))
    configured_findings = sorted(allowlist_findings_for_input(result.input))
    suppressed_rows = _suppression_rows_payload(result)
    matched_domains = sorted(
        {
            row["matched_allowlist_domain"]
            for row in suppressed_rows
            if row["matched_allowlist_domain"]
        }
    )

    return {
        "hostname": None if url_context is None else url_context.hostname,
        "configured_allowlist_domains": configured_domains,
        "configured_allowlist_categories": configured_categories,
        "configured_allowlist_findings": configured_findings,
        "matched_allowlist_domains": matched_domains,
        "suppressed_count": len(suppressed_rows),
        "suppressed_rows": suppressed_rows,
    }


def _url_analyst_payload(result: AnalysisResult) -> dict[str, object] | None:
    domain_anatomy = _domain_anatomy_payload(result)
    if domain_anatomy is None:
        return None

    return {
        "domain_anatomy": domain_anatomy,
        "evidence_rows": _finding_evidence_payload(result),
        "redirect_trace": _redirect_trace_payload(result),
        "suppression_trace": _suppression_trace_payload(result),
    }


def _item_payload(
    *,
    input_type: str,
    subject: str,
    result: AnalysisResult,
    include_family: bool,
    include_analyst: bool,
) -> dict[str, object]:
    item: dict[str, object] = {
        "subject": subject,
        "result": _analysis_result_payload(result),
    }
    if include_family:
        item["family"] = _family_payload(result)
    if include_analyst and input_type == "url":
        analyst = _url_analyst_payload(result)
        if analyst is not None:
            item["analyst"] = analyst
    return item


def build_single_result_payload(
    *,
    flow: str,
    input_type: str,
    subject: str,
    result: AnalysisResult,
    include_family: bool = False,
    schema_version: str = "1.0",
    include_analyst: bool | None = None,
) -> dict[str, object]:
    """Build a stable single-item payload shape for API/JSON consumers."""
    if include_analyst is None:
        resolved_include_analyst = schema_version == "2.0" and input_type == "url"
    else:
        resolved_include_analyst = include_analyst and input_type == "url"
    item = _item_payload(
        input_type=input_type,
        subject=subject,
        result=result,
        include_family=include_family,
        include_analyst=resolved_include_analyst,
    )
    return {
        "schema_version": schema_version,
        "flow": flow,
        "mode": "single",
        "input_type": input_type,
        "item_count": 1,
        "item": item,
    }


def build_multi_result_payload(
    *,
    flow: str,
    input_type: str,
    items: list[tuple[str, AnalysisResult]],
    include_family: bool = False,
    schema_version: str = "1.0",
    include_analyst: bool = False,
) -> dict[str, object]:
    """Build a stable multi-item payload shape for batch-like workflows."""
    payload_items = [
        _item_payload(
            input_type=input_type,
            subject=subject,
            result=result,
            include_family=include_family,
            include_analyst=include_analyst and input_type == "url",
        )
        for subject, result in items
    ]
    return {
        "schema_version": schema_version,
        "flow": flow,
        "mode": "multi",
        "input_type": input_type,
        "item_count": len(payload_items),
        "items": payload_items,
    }


def build_qr_scan_payload(
    *,
    image_path: str,
    decoded_payloads: list[str],
    url_results: list[tuple[str, AnalysisResult]],
    analyzed_all: bool,
    include_family: bool = False,
    include_legacy_keys: bool = True,
) -> dict[str, object]:
    """Build QR scan payload with stable wrappers and legacy compatibility keys."""
    base: dict[str, object] = {
        "schema_version": "1.0",
        "flow": "qr_scan",
        "mode": "multi" if analyzed_all else "single",
        "input_type": "url",
        "image_name": image_path,
        "decoded_payloads": decoded_payloads,
        "decoded_payload_count": len(decoded_payloads),
        "url_payload_count": len(url_results),
        "analyzed_all": analyzed_all,
    }
    if include_legacy_keys:
        # Legacy key kept for existing consumers that still read image_path.
        base["image_path"] = image_path

    if analyzed_all:
        wrapped = build_multi_result_payload(
            flow="qr_scan",
            input_type="url",
            items=url_results,
            include_family=include_family,
        )
        base["item_count"] = wrapped["item_count"]
        base["items"] = wrapped["items"]
        if include_legacy_keys:
            # Legacy key kept for CLI JSON compatibility.
            base["results"] = [
                {"url": subject, "result": _analysis_result_payload(result)}
                for subject, result in url_results
            ]
        return base

    selected_url, selected_result = url_results[0]
    wrapped = build_single_result_payload(
        flow="qr_scan",
        input_type="url",
        subject=selected_url,
        result=selected_result,
        include_family=include_family,
    )
    base["item_count"] = wrapped["item_count"]
    base["item"] = wrapped["item"]
    if include_legacy_keys:
        # Legacy keys kept for CLI JSON compatibility.
        base["selected_url"] = selected_url
        base["result"] = _analysis_result_payload(selected_result)
    return base
