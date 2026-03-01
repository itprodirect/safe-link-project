"""Smoke tests for the optional FastAPI adapter."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # type: ignore[import-not-found]

from lsh.adapters import api


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


def test_url_check_endpoint_can_include_family_payload() -> None:
    client = _client()

    response = client.post(
        "/api/v1/url/check",
        json={"url": "https://example.com", "family": True},
    )
    assert response.status_code == 200
    body = response.json()
    assert "family" in body["item"]


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


def test_qr_scan_requires_upload_file() -> None:
    client = _client()
    response = client.post("/api/v1/qr/scan", data={"analyze_all": "false"})
    assert response.status_code == 422
