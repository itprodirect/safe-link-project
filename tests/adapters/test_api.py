"""Smoke tests for the optional FastAPI adapter."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # type: ignore[import-not-found]

from lsh.adapters import api


def _client() -> TestClient:
    app = api.create_app()
    return TestClient(app)


def test_health_endpoint() -> None:
    client = _client()

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


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

    monkeypatch.setattr(
        "lsh.adapters.api.decode_qr_payloads_from_image",
        lambda _path: ["https://example.com", "plain payload"],
    )

    response = client.post("/api/v1/qr/scan", json={"image_path": "code.png"})
    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "1.0"
    assert body["flow"] == "qr_scan"
    assert body["mode"] == "single"
    assert body["item_count"] == 1
    assert body["selected_url"] == "https://example.com"
    assert "item" in body


def test_qr_scan_endpoint_returns_multi_wrapped_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _client()

    monkeypatch.setattr(
        "lsh.adapters.api.decode_qr_payloads_from_image",
        lambda _path: ["https://a.example", "https://b.example"],
    )

    response = client.post(
        "/api/v1/qr/scan",
        json={"image_path": "code.png", "analyze_all": True},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "1.0"
    assert body["mode"] == "multi"
    assert body["item_count"] == 2
    assert len(body["items"]) == 2
    assert len(body["results"]) == 2


def test_qr_scan_decoder_unavailable_uses_error_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from lsh.modules.qr_decode import QRDecodeUnavailableError

    client = _client()

    def _raise_unavailable(_path: str) -> list[str]:
        raise QRDecodeUnavailableError("missing zbar")

    monkeypatch.setattr(
        "lsh.adapters.api.decode_qr_payloads_from_image",
        _raise_unavailable,
    )

    response = client.post("/api/v1/qr/scan", json={"image_path": "code.png"})
    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["schema_version"] == "1.0"
    assert detail["error"]["code"] == "QRC_DECODER_UNAVAILABLE"


def test_qr_scan_no_url_payloads_uses_error_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _client()
    monkeypatch.setattr(
        "lsh.adapters.api.decode_qr_payloads_from_image",
        lambda _path: ["plain text payload"],
    )

    response = client.post("/api/v1/qr/scan", json={"image_path": "code.png"})
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["schema_version"] == "1.0"
    assert detail["error"]["code"] == "QRC_NO_URL_PAYLOADS"


def test_qr_scan_no_payloads_uses_error_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _client()
    monkeypatch.setattr(
        "lsh.adapters.api.decode_qr_payloads_from_image",
        lambda _path: [],
    )

    response = client.post("/api/v1/qr/scan", json={"image_path": "code.png"})
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["schema_version"] == "1.0"
    assert detail["error"]["code"] == "QRC_NO_PAYLOADS"
