"""Structured response payload builders reusable across CLI and API adapters."""

from __future__ import annotations

from lsh.core.models import AnalysisResult
from lsh.formatters.family import build_family_view


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


def _item_payload(
    *,
    subject: str,
    result: AnalysisResult,
    include_family: bool,
) -> dict[str, object]:
    item: dict[str, object] = {
        "subject": subject,
        "result": _analysis_result_payload(result),
    }
    if include_family:
        item["family"] = _family_payload(result)
    return item


def build_single_result_payload(
    *,
    flow: str,
    input_type: str,
    subject: str,
    result: AnalysisResult,
    include_family: bool = False,
) -> dict[str, object]:
    """Build a stable single-item payload shape for API/JSON consumers."""
    item = _item_payload(subject=subject, result=result, include_family=include_family)
    return {
        "schema_version": "1.0",
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
) -> dict[str, object]:
    """Build a stable multi-item payload shape for batch-like workflows."""
    payload_items = [
        _item_payload(subject=subject, result=result, include_family=include_family)
        for subject, result in items
    ]
    return {
        "schema_version": "1.0",
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
) -> dict[str, object]:
    """Build QR scan payload with stable wrappers and legacy compatibility keys."""
    base: dict[str, object] = {
        "schema_version": "1.0",
        "flow": "qr_scan",
        "mode": "multi" if analyzed_all else "single",
        "input_type": "url",
        "image_name": image_path,
        # Legacy key kept for existing consumers that still read image_path.
        "image_path": image_path,
        "decoded_payloads": decoded_payloads,
        "decoded_payload_count": len(decoded_payloads),
        "url_payload_count": len(url_results),
        "analyzed_all": analyzed_all,
    }

    if analyzed_all:
        wrapped = build_multi_result_payload(
            flow="qr_scan",
            input_type="url",
            items=url_results,
            include_family=include_family,
        )
        base["item_count"] = wrapped["item_count"]
        base["items"] = wrapped["items"]
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
    # Legacy keys kept for CLI JSON compatibility.
    base["selected_url"] = selected_url
    base["result"] = _analysis_result_payload(selected_result)
    return base
