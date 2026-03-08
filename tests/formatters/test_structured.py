"""Tests for structured API/JSON payload helpers."""

from __future__ import annotations

from datetime import UTC, datetime

from lsh.application import analyze_url
from lsh.core.models import AnalysisInput, AnalysisResult, Confidence, Evidence, Finding, Severity
from lsh.formatters.structured import (
    build_multi_result_payload,
    build_qr_scan_payload,
    build_single_result_payload,
)


def _finding(risk: int, *, module: str = "test", category: str = "TST001") -> Finding:
    return Finding(
        module=module,
        category=category,
        severity=Severity.INFO,
        confidence=Confidence.MEDIUM,
        risk_score=risk,
        title="Test finding",
        explanation="Test explanation.",
        family_explanation="Test family explanation.",
        recommendations=["Test recommendation."],
    )


def _result(subject: str, risk: int = 0, findings: list[Finding] | None = None) -> AnalysisResult:
    finding_list = findings if findings is not None else ([_finding(risk)] if risk > 0 else [])
    overall_risk = finding_list[-1].risk_score if finding_list else risk
    return AnalysisResult(
        input=AnalysisInput(input_type="url", content=subject),
        findings=finding_list,
        overall_risk=overall_risk,
        overall_severity=Severity.INFO if overall_risk == 0 else Severity.MEDIUM,
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
    assert "analyst" not in item


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


def test_single_payload_can_override_schema_version() -> None:
    payload = build_single_result_payload(
        flow="analyze",
        input_type="url",
        subject="https://example.com",
        result=_result("https://example.com"),
        schema_version="2.0",
    )
    assert payload["schema_version"] == "2.0"
    item = payload["item"]
    assert isinstance(item, dict)
    assert "analyst" in item


def test_v2_url_payload_includes_analyst_projection() -> None:
    result = analyze_url("https://xn--pple-43d.com")
    payload = build_single_result_payload(
        flow="analyze",
        input_type="url",
        subject="https://xn--pple-43d.com",
        result=result,
        include_family=True,
        schema_version="2.0",
    )

    item = payload["item"]
    assert isinstance(item, dict)
    analyst = item["analyst"]
    assert isinstance(analyst, dict)
    domain_anatomy = analyst["domain_anatomy"]
    evidence_rows = analyst["evidence_rows"]
    assert isinstance(domain_anatomy, dict)
    assert domain_anatomy["submitted_url"] == "https://xn--pple-43d.com"
    assert domain_anatomy["canonical_url"] == "https://xn--pple-43d.com/"
    assert domain_anatomy["hostname"] == "xn--pple-43d.com"
    assert domain_anatomy["registrable_domain"] == "xn--pple-43d.com"
    assert isinstance(evidence_rows, list)
    assert evidence_rows
    assert evidence_rows[0]["cumulative_risk_score"] >= evidence_rows[-1]["cumulative_risk_score"]


def test_v2_url_payload_builds_redirect_trace_from_findings() -> None:
    redirect_findings = [
        Finding(
            module="redirect",
            category="RED001_REDIRECT_CHAIN_PRESENT",
            severity=Severity.INFO,
            confidence=Confidence.LOW,
            risk_score=15,
            title="URL redirects before reaching a final destination",
            explanation="Redirect chain present.",
            family_explanation=(
                "This link bounces through another address before it finishes loading."
            ),
            evidence=[
                Evidence(label="Redirect Hops", value="2"),
                Evidence(label="Chain", value="https://start.example -> https://mid.example -> https://final.example"),
                Evidence(label="Start URL", value="https://start.example"),
                Evidence(label="Final URL", value="https://final.example"),
            ],
            recommendations=[
                "Check the final destination before signing in or entering payment details."
            ],
        ),
        Finding(
            module="redirect",
            category="RED002_CROSS_DOMAIN_REDIRECT",
            severity=Severity.INFO,
            confidence=Confidence.MEDIUM,
            risk_score=40,
            title="Redirect chain changes registrable domain",
            explanation="Cross-domain jumps increase destination uncertainty.",
            family_explanation=(
                "This link starts on one site name and ends on a different site name."
            ),
            evidence=[
                Evidence(label="Redirect Hops", value="2"),
                Evidence(label="Chain", value="https://start.example -> https://mid.example -> https://final.example"),
                Evidence(
                    label="Domain Path",
                    value="start.example -> mid.example -> final.example",
                ),
            ],
            recommendations=["Verify that the final site name is expected and trusted."],
        ),
        Finding(
            module="redirect",
            category="RED005_REQUEST_TIMEOUT",
            severity=Severity.INFO,
            confidence=Confidence.MEDIUM,
            risk_score=70,
            title="Redirect check timed out",
            explanation="Network redirect analysis timed out before completion.",
            family_explanation="This link took too long to resolve, so checks are incomplete.",
            evidence=[
                Evidence(label="Redirect Hops", value="2"),
                Evidence(label="Chain", value="https://start.example -> https://mid.example -> https://final.example"),
            ],
            recommendations=["Treat unresolved links cautiously and verify before opening."],
        ),
    ]
    payload = build_single_result_payload(
        flow="analyze",
        input_type="url",
        subject="https://start.example",
        result=_result("https://start.example", findings=redirect_findings),
        schema_version="2.0",
    )

    item = payload["item"]
    assert isinstance(item, dict)
    analyst = item["analyst"]
    assert isinstance(analyst, dict)
    redirect_trace = analyst["redirect_trace"]
    assert isinstance(redirect_trace, dict)
    assert redirect_trace["start_url"] == "https://start.example"
    assert redirect_trace["final_url"] == "https://final.example"
    assert redirect_trace["hop_count"] == 2
    assert redirect_trace["crosses_registrable_domain"] is True
    assert redirect_trace["timed_out"] is True


def test_multi_payload_can_override_schema_version() -> None:
    payload = build_multi_result_payload(
        flow="batch",
        input_type="url",
        items=[("https://a.example", _result("https://a.example", risk=10))],
        schema_version="2.0",
    )
    assert payload["schema_version"] == "2.0"


def test_qr_payload_includes_wrapped_and_legacy_keys_for_single_mode() -> None:
    payload = build_qr_scan_payload(
        image_path="code.png",
        decoded_payloads=["https://example.com"],
        url_results=[("https://example.com", _result("https://example.com", risk=10))],
        analyzed_all=False,
    )

    assert payload["schema_version"] == "1.0"
    assert payload["mode"] == "single"
    assert payload["image_name"] == "code.png"
    assert payload["image_path"] == "code.png"
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


def test_qr_payload_can_disable_legacy_keys_for_single_mode() -> None:
    payload = build_qr_scan_payload(
        image_path="code.png",
        decoded_payloads=["https://example.com"],
        url_results=[("https://example.com", _result("https://example.com", risk=10))],
        analyzed_all=False,
        include_legacy_keys=False,
    )

    assert payload["schema_version"] == "1.0"
    assert payload["mode"] == "single"
    assert payload["image_name"] == "code.png"
    assert "item" in payload
    assert "image_path" not in payload
    assert "selected_url" not in payload
    assert "result" not in payload


def test_qr_payload_can_disable_legacy_keys_for_multi_mode() -> None:
    payload = build_qr_scan_payload(
        image_path="code.png",
        decoded_payloads=["https://a.example", "https://b.example"],
        url_results=[
            ("https://a.example", _result("https://a.example", risk=10)),
            ("https://b.example", _result("https://b.example", risk=20)),
        ],
        analyzed_all=True,
        include_legacy_keys=False,
    )

    assert payload["schema_version"] == "1.0"
    assert payload["mode"] == "multi"
    assert "items" in payload
    assert "image_path" not in payload
    assert "results" not in payload
