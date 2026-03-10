"""Smoke tests for the optional FastAPI adapter."""

from __future__ import annotations

from copy import deepcopy

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from lsh.adapters import api

_QR_UPLOADS_AVAILABLE = api._multipart_support_available()
_QR_UPLOADS_SKIP = pytest.mark.skipif(
    not _QR_UPLOADS_AVAILABLE,
    reason="python-multipart is required for QR upload endpoint behavior tests.",
)

def _client() -> TestClient:
    app = api.create_app()
    return TestClient(app)


def _qr_upload(
    filename: str = "code.png",
    content: bytes = b"not-a-real-png",
) -> dict[str, tuple[str, bytes, str]]:
    return {"file": (filename, content, "image/png")}


def _preflight_headers(origin: str) -> dict[str, str]:
    return {
        "Origin": origin,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    }


def _scrub_result_runtime_fields(result: dict[str, object]) -> dict[str, object]:
    """Normalize runtime-variant fields before structural parity assertions."""
    scrubbed = deepcopy(result)
    if "analyzed_at" in scrubbed:
        scrubbed["analyzed_at"] = "<TIMESTAMP>"
    return scrubbed


def test_health_endpoint() -> None:
    client = _client()

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_preflight_allows_default_local_ui_origin() -> None:
    client = _client()
    response = client.options(
        "/api/v1/url/check",
        headers=_preflight_headers("http://127.0.0.1:3000"),
    )
    assert response.status_code in {200, 204}
    assert response.headers.get("access-control-allow-origin") == "http://127.0.0.1:3000"


def test_cors_preflight_respects_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LSH_API_CORS_ALLOW_ORIGINS", "https://ui.example.com")
    client = TestClient(api.create_app())

    allowed = client.options(
        "/api/v1/url/check",
        headers=_preflight_headers("https://ui.example.com"),
    )
    assert allowed.status_code in {200, 204}
    assert allowed.headers.get("access-control-allow-origin") == "https://ui.example.com"

    denied = client.options(
        "/api/v1/url/check",
        headers=_preflight_headers("http://127.0.0.1:3000"),
    )
    assert denied.headers.get("access-control-allow-origin") is None


def test_cors_response_headers_on_actual_post() -> None:
    """Verify CORS headers appear on real POST responses, not just preflight."""
    client = _client()
    response = client.post(
        "/api/v1/url/check",
        json={"url": "https://example.com"},
        headers={"Origin": "http://127.0.0.1:3000"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://127.0.0.1:3000"


def test_cors_response_headers_on_v2_analyze_post() -> None:
    """Verify CORS headers on the v2 analyze endpoint real response."""
    client = _client()
    response = client.post(
        "/api/v2/analyze",
        json={"input_type": "url", "content": "https://example.com"},
        headers={"Origin": "http://127.0.0.1:3000"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://127.0.0.1:3000"


def test_cors_hosted_origin_end_to_end(monkeypatch: pytest.MonkeyPatch) -> None:
    """Simulate hosted deployment with custom domain origins."""
    monkeypatch.setenv(
        "LSH_API_CORS_ALLOW_ORIGINS",
        "https://app.linksafety.example.com,https://staging.linksafety.example.com",
    )
    client = TestClient(api.create_app())

    # Preflight from allowed production origin
    preflight_resp = client.options(
        "/api/v2/analyze",
        headers=_preflight_headers("https://app.linksafety.example.com"),
    )
    assert preflight_resp.status_code in {200, 204}
    assert (
        preflight_resp.headers.get("access-control-allow-origin")
        == "https://app.linksafety.example.com"
    )

    # Actual POST from allowed staging origin
    post_resp = client.post(
        "/api/v1/url/check",
        json={"url": "https://example.com"},
        headers={"Origin": "https://staging.linksafety.example.com"},
    )
    assert post_resp.status_code == 200
    assert (
        post_resp.headers.get("access-control-allow-origin")
        == "https://staging.linksafety.example.com"
    )

    # Denied origin gets no CORS header
    denied_resp = client.post(
        "/api/v1/url/check",
        json={"url": "https://example.com"},
        headers={"Origin": "https://evil.example.com"},
    )
    assert denied_resp.status_code == 200
    assert denied_resp.headers.get("access-control-allow-origin") is None


def test_cors_preflight_all_endpoint_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify CORS preflight works for all API endpoint paths."""
    monkeypatch.setenv("LSH_API_CORS_ALLOW_ORIGINS", "https://ui.example.com")
    client = TestClient(api.create_app())

    for path in ["/api/v1/url/check", "/api/v1/email/check", "/api/v2/analyze"]:
        resp = client.options(path, headers=_preflight_headers("https://ui.example.com"))
        assert resp.status_code in {200, 204}, f"preflight failed for {path}"
        assert (
            resp.headers.get("access-control-allow-origin") == "https://ui.example.com"
        ), f"CORS origin missing for {path}"


def test_url_check_endpoint_returns_wrapped_shape() -> None:
    client = _client()

    response = client.post(
        "/api/v1/url/check",
        json={"url": "https://example.com"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "1.0"
    assert body["flow"] == "url_check"
    assert body["mode"] == "single"
    assert body["item_count"] == 1


def test_openapi_uses_typed_response_models() -> None:
    client = _client()
    schema = client.get("/openapi.json").json()

    url_success = schema["paths"]["/api/v1/url/check"]["post"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]
    assert "$ref" in url_success or "allOf" in url_success

    qr_error = schema["paths"]["/api/v1/qr/scan"]["post"]["responses"]["400"]["content"][
        "application/json"
    ]["schema"]
    assert "$ref" in qr_error

    v2_success = schema["paths"]["/api/v2/analyze"]["post"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]
    assert "$ref" in v2_success or "allOf" in v2_success


def test_url_check_endpoint_can_include_family_payload() -> None:
    client = _client()

    response = client.post(
        "/api/v1/url/check",
        json={"url": "https://example.com", "family": True},
    )
    assert response.status_code == 200
    body = response.json()
    assert "family" in body["item"]


def test_v2_analyze_url_returns_wrapped_shape() -> None:
    client = _client()
    response = client.post(
        "/api/v2/analyze",
        json={"input_type": "url", "content": "https://example.com"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "2.0"
    assert body["flow"] == "analyze"
    assert body["mode"] == "single"
    assert body["input_type"] == "url"
    assert body["item_count"] == 1
    assert "analyst" in body["item"]
    assert body["item"]["analyst"]["domain_anatomy"]["submitted_url"] == "https://example.com"
    assert isinstance(body["item"]["analyst"]["evidence_rows"], list)


def test_v2_analyze_email_returns_wrapped_shape() -> None:
    client = _client()
    response = client.post(
        "/api/v2/analyze",
        json={
            "input_type": "email_headers",
            "content": "Authentication-Results: mx; spf=pass; dkim=pass; dmarc=pass",
            "subject": "sample headers",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "2.0"
    assert body["flow"] == "analyze"
    assert body["input_type"] == "email_headers"
    assert body["item"]["subject"] == "sample headers"
    assert "analyst" not in body["item"]


def test_v2_analyze_can_include_family_payload() -> None:
    client = _client()
    response = client.post(
        "/api/v2/analyze",
        json={
            "input_type": "url",
            "content": "https://example.com",
            "family": True,
        },
    )
    assert response.status_code == 200
    assert "family" in response.json()["item"]


def test_v2_analyze_url_allowlist_finding_targets_single_code() -> None:
    client = _client()
    response = client.post(
        "/api/v2/analyze",
        json={
            "input_type": "url",
            "content": "https://xn--pple-43d.com",
            "allowlist_domains": ["xn--pple-43d.com"],
            "allowlist_categories": ["NONE"],
            "allowlist_findings": ["HMG002_PUNYCODE_VISIBILITY"],
        },
    )
    assert response.status_code == 200
    body = response.json()
    findings = body["item"]["result"]["findings"]
    categories = {finding["category"] for finding in findings}
    assert "HMG002_PUNYCODE_VISIBILITY" not in categories
    assert "HMG003_MIXED_SCRIPT_HOSTNAME" in categories

    evidence_rows = body["item"]["analyst"]["evidence_rows"]
    assert evidence_rows
    assert all("compare_key" in row for row in evidence_rows)
    assert all("finding_key" in row for row in evidence_rows)
    assert all("evidence_map" in row for row in evidence_rows)
    assert all("key" in entry for row in evidence_rows for entry in row["evidence"])

    suppression_trace = body["item"]["analyst"]["suppression_trace"]
    assert suppression_trace["suppressed_count"] == 1
    assert suppression_trace["suppressed_rows"][0]["category"] == "HMG002_PUNYCODE_VISIBILITY"
    assert suppression_trace["suppressed_rows"][0]["compare_key"] == (
        "homoglyph:HMG002_PUNYCODE_VISIBILITY:finding:hmg002_punycode_visibility"
    )
    assert suppression_trace["suppressed_rows"][0]["suppression_scope"] == "finding"


def test_v2_analyze_url_allowlist_categories_can_be_lowercase() -> None:
    client = _client()
    response = client.post(
        "/api/v2/analyze",
        json={
            "input_type": "url",
            "content": "https://xn--pple-43d.com",
            "allowlist_domains": ["xn--pple-43d.com"],
            "allowlist_categories": ["none"],
            "allowlist_findings": ["hmg002_punycode_visibility"],
        },
    )
    assert response.status_code == 200
    findings = response.json()["item"]["result"]["findings"]
    categories = {finding["category"] for finding in findings}
    assert "HMG002_PUNYCODE_VISIBILITY" not in categories
    assert "HMG003_MIXED_SCRIPT_HOSTNAME" in categories


def test_v2_analyze_empty_url_content_is_handled() -> None:
    client = _client()
    response = client.post(
        "/api/v2/analyze",
        json={"input_type": "url", "content": ""},
    )
    assert response.status_code == 200
    findings = response.json()["item"]["result"]["findings"]
    categories = {finding["category"] for finding in findings}
    assert "HMG000_INVALID_URL" in categories


def test_v2_analyze_email_ignores_url_only_metadata_fields() -> None:
    client = _client()
    response = client.post(
        "/api/v2/analyze",
        json={
            "input_type": "email_headers",
            "content": "Authentication-Results: mx; spf=pass; dkim=pass; dmarc=pass",
            "allowlist_domains": ["example.com"],
            "allowlist_categories": ["ALL"],
            "allowlist_findings": ["HMG002*"],
            "network_enabled": True,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["input_type"] == "email_headers"
    assert body["item"]["result"]["findings"] == []


def test_v1_v2_url_result_parity_for_overlapping_fields() -> None:
    client = _client()
    v1_response = client.post(
        "/api/v1/url/check",
        json={
            "url": "https://xn--pple-43d.com",
            "family": True,
            "allowlist_domains": ["xn--pple-43d.com"],
            "allowlist_categories": ["NONE"],
            "allowlist_findings": ["HMG002_PUNYCODE_VISIBILITY"],
            "network_enabled": False,
            "network_max_hops": 5,
            "network_timeout": 3.0,
        },
    )
    assert v1_response.status_code == 200
    v1_body = v1_response.json()

    v2_response = client.post(
        "/api/v2/analyze",
        json={
            "input_type": "url",
            "content": "https://xn--pple-43d.com",
            "subject": "https://xn--pple-43d.com",
            "family": True,
            "allowlist_domains": ["xn--pple-43d.com"],
            "allowlist_categories": ["NONE"],
            "allowlist_findings": ["HMG002_PUNYCODE_VISIBILITY"],
            "network_enabled": False,
            "network_max_hops": 5,
            "network_timeout": 3.0,
        },
    )
    assert v2_response.status_code == 200
    v2_body = v2_response.json()

    assert _scrub_result_runtime_fields(v1_body["item"]["result"]) == _scrub_result_runtime_fields(
        v2_body["item"]["result"]
    )
    assert v1_body["item"]["family"] == v2_body["item"]["family"]
    assert v1_body["item"]["subject"] == v2_body["item"]["subject"]
    assert "analyst" not in v1_body["item"]
    assert "analyst" in v2_body["item"]
    assert v1_body["mode"] == v2_body["mode"] == "single"
    assert v1_body["item_count"] == v2_body["item_count"] == 1


def test_v1_v2_email_result_parity_for_overlapping_fields() -> None:
    client = _client()
    headers = "Authentication-Results: mx; spf=fail; dkim=pass; dmarc=pass"

    v1_response = client.post(
        "/api/v1/email/check",
        json={"headers": headers, "source_label": "sample", "family": True},
    )
    assert v1_response.status_code == 200
    v1_body = v1_response.json()

    v2_response = client.post(
        "/api/v2/analyze",
        json={
            "input_type": "email_headers",
            "content": headers,
            "subject": "sample",
            "family": True,
        },
    )
    assert v2_response.status_code == 200
    v2_body = v2_response.json()

    assert _scrub_result_runtime_fields(v1_body["item"]["result"]) == _scrub_result_runtime_fields(
        v2_body["item"]["result"]
    )
    assert v1_body["item"]["family"] == v2_body["item"]["family"]
    assert v1_body["item"]["subject"] == v2_body["item"]["subject"]
    assert v1_body["mode"] == v2_body["mode"] == "single"
    assert v1_body["item_count"] == v2_body["item_count"] == 1


def test_v2_analyze_rejects_unknown_input_type() -> None:
    client = _client()
    response = client.post(
        "/api/v2/analyze",
        json={"input_type": "qr_image", "content": "ignored"},
    )
    assert response.status_code == 422


def test_url_check_allowlist_finding_targets_single_code() -> None:
    client = _client()
    response = client.post(
        "/api/v1/url/check",
        json={
            "url": "https://xn--pple-43d.com",
            "allowlist_domains": ["xn--pple-43d.com"],
            "allowlist_categories": ["NONE"],
            "allowlist_findings": ["HMG002_PUNYCODE_VISIBILITY"],
        },
    )
    assert response.status_code == 200
    findings = response.json()["item"]["result"]["findings"]
    categories = {finding["category"] for finding in findings}
    assert "HMG002_PUNYCODE_VISIBILITY" not in categories
    assert "HMG003_MIXED_SCRIPT_HOSTNAME" in categories


def test_email_check_endpoint_returns_wrapped_shape() -> None:
    client = _client()
    response = client.post(
        "/api/v1/email/check",
        json={"headers": "Authentication-Results: mx; spf=pass; dkim=pass; dmarc=pass"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "1.0"
    assert body["flow"] == "email_check"
    assert body["mode"] == "single"
    assert body["item_count"] == 1


def test_qr_scan_endpoint_reports_missing_multipart_dependency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(api, "_multipart_support_available", lambda: False)
    client = TestClient(api.create_app())

    response = client.post("/api/v1/qr/scan")
    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["schema_version"] == "1.0"
    assert detail["error"]["code"] == "QRC_MULTIPART_UNAVAILABLE"


@_QR_UPLOADS_SKIP
def test_qr_scan_endpoint_returns_single_wrapped_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _client()

    def _decode_single(_image_bytes: bytes, image_name: str = "<uploaded-image>") -> list[str]:
        return ["https://example.com", "plain payload"]

    monkeypatch.setattr(
        "lsh.adapters.api.decode_qr_payloads_from_bytes",
        _decode_single,
    )

    response = client.post("/api/v1/qr/scan", files=_qr_upload())
    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "1.0"
    assert body["flow"] == "qr_scan"
    assert body["mode"] == "single"
    assert body["item_count"] == 1
    assert body["image_name"] == "code.png"
    assert body["selected_url"] == "https://example.com"
    assert "item" in body
    assert response.headers["x-lsh-qr-legacy-keys"].startswith("included;")


@_QR_UPLOADS_SKIP
def test_qr_scan_endpoint_returns_multi_wrapped_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _client()

    def _decode_multi(_image_bytes: bytes, image_name: str = "<uploaded-image>") -> list[str]:
        return ["https://a.example", "https://b.example"]

    monkeypatch.setattr(
        "lsh.adapters.api.decode_qr_payloads_from_bytes",
        _decode_multi,
    )

    response = client.post(
        "/api/v1/qr/scan",
        files=_qr_upload(),
        data={"analyze_all": "true"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "1.0"
    assert body["mode"] == "multi"
    assert body["item_count"] == 2
    assert len(body["items"]) == 2
    assert len(body["results"]) == 2
    assert response.headers["x-lsh-qr-legacy-keys"].startswith("included;")


@_QR_UPLOADS_SKIP
def test_qr_scan_endpoint_can_disable_legacy_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LSH_API_INCLUDE_QR_LEGACY_KEYS", "false")
    client = TestClient(api.create_app())

    def _decode_single(_image_bytes: bytes, image_name: str = "<uploaded-image>") -> list[str]:
        return ["https://example.com"]

    monkeypatch.setattr(
        "lsh.adapters.api.decode_qr_payloads_from_bytes",
        _decode_single,
    )

    response = client.post("/api/v1/qr/scan", files=_qr_upload())
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "single"
    assert body["image_name"] == "code.png"
    assert "image_path" not in body
    assert "selected_url" not in body
    assert "result" not in body
    assert response.headers["x-lsh-qr-legacy-keys"] == "disabled"


@_QR_UPLOADS_SKIP
def test_qr_scan_decoder_unavailable_uses_error_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from lsh.modules.qr_decode import QRDecodeUnavailableError

    client = _client()

    def _raise_unavailable(_image_bytes: bytes, image_name: str = "<uploaded-image>") -> list[str]:
        raise QRDecodeUnavailableError("missing zbar")

    monkeypatch.setattr(
        "lsh.adapters.api.decode_qr_payloads_from_bytes",
        _raise_unavailable,
    )

    response = client.post("/api/v1/qr/scan", files=_qr_upload())
    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["schema_version"] == "1.0"
    assert detail["error"]["code"] == "QRC_DECODER_UNAVAILABLE"


@_QR_UPLOADS_SKIP
def test_qr_scan_no_url_payloads_uses_error_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _client()

    def _decode_no_urls(_image_bytes: bytes, image_name: str = "<uploaded-image>") -> list[str]:
        return ["plain text payload"]

    monkeypatch.setattr(
        "lsh.adapters.api.decode_qr_payloads_from_bytes",
        _decode_no_urls,
    )

    response = client.post("/api/v1/qr/scan", files=_qr_upload())
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["schema_version"] == "1.0"
    assert detail["error"]["code"] == "QRC_NO_URL_PAYLOADS"


@_QR_UPLOADS_SKIP
def test_qr_scan_no_payloads_uses_error_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _client()

    def _decode_none(_image_bytes: bytes, image_name: str = "<uploaded-image>") -> list[str]:
        return []

    monkeypatch.setattr(
        "lsh.adapters.api.decode_qr_payloads_from_bytes",
        _decode_none,
    )

    response = client.post("/api/v1/qr/scan", files=_qr_upload())
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["schema_version"] == "1.0"
    assert detail["error"]["code"] == "QRC_NO_PAYLOADS"


@_QR_UPLOADS_SKIP
def test_qr_scan_requires_upload_file() -> None:
    client = _client()
    response = client.post("/api/v1/qr/scan", data={"analyze_all": "false"})
    assert response.status_code == 422






