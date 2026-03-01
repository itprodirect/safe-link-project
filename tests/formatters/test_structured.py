"""Tests for structured API/JSON payload helpers."""

from __future__ import annotations

from datetime import UTC, datetime

from lsh.core.models import AnalysisInput, AnalysisResult, Confidence, Finding, Severity
from lsh.formatters.structured import (
    build_multi_result_payload,
    build_qr_scan_payload,
    build_single_result_payload,
)


def _result(subject: str, risk: int = 0) -> AnalysisResult:
    finding_list: list[Finding]
    if risk > 0:
        finding_list = [
            Finding(
                module="test",
                category="TST001",
                severity=Severity.INFO,
                confidence=Confidence.MEDIUM,
                risk_score=risk,
                title="Test finding",
                explanation="Test explanation.",
                family_explanation="Test family explanation.",
                recommendations=["Test recommendation."],
            )
        ]
    else:
        finding_list = []

    return AnalysisResult(
        input=AnalysisInput(input_type="url", content=subject),
        findings=finding_list,
        overall_risk=risk,
        overall_severity=Severity.INFO if risk == 0 else Severity.MEDIUM,
        summary="Summary.",
        analyzed_at=datetime.now(UTC),
    )


def test_single_payload_shape_is_stable() -> None:
    payload = build_single_result_payload(
        flow="url_check",
        input_type="url",
        subject="https://example.com",
        result=_result("https://example.com"),
        include_family=True,
    )

    assert payload["schema_version"] == "1.0"
    assert payload["mode"] == "single"
    assert payload["item_count"] == 1
    item = payload["item"]
    assert isinstance(item, dict)
    assert item["subject"] == "https://example.com"
    assert "result" in item
    assert "family" in item


def test_multi_payload_shape_is_stable() -> None:
    payload = build_multi_result_payload(
        flow="batch",
        input_type="url",
        items=[
            ("https://a.example", _result("https://a.example", risk=10)),
            ("https://b.example", _result("https://b.example", risk=20)),
        ],
    )

    assert payload["schema_version"] == "1.0"
    assert payload["mode"] == "multi"
    assert payload["item_count"] == 2
    items = payload["items"]
    assert isinstance(items, list)
    assert len(items) == 2


def test_qr_payload_includes_wrapped_and_legacy_keys_for_single_mode() -> None:
    payload = build_qr_scan_payload(
        image_path="code.png",
        decoded_payloads=["https://example.com"],
        url_results=[("https://example.com", _result("https://example.com", risk=10))],
        analyzed_all=False,
    )

    assert payload["schema_version"] == "1.0"
    assert payload["mode"] == "single"
    assert payload["selected_url"] == "https://example.com"
    assert "result" in payload
    assert "item" in payload


def test_qr_payload_includes_wrapped_and_legacy_keys_for_multi_mode() -> None:
    payload = build_qr_scan_payload(
        image_path="code.png",
        decoded_payloads=["https://a.example", "https://b.example"],
        url_results=[
            ("https://a.example", _result("https://a.example", risk=10)),
            ("https://b.example", _result("https://b.example", risk=20)),
        ],
        analyzed_all=True,
        include_family=True,
    )

    assert payload["schema_version"] == "1.0"
    assert payload["mode"] == "multi"
    assert payload["item_count"] == 2
    assert "items" in payload
    assert "results" in payload
