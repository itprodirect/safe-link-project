"""Smoke tests for the optional FastAPI adapter."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # type: ignore[import-not-found]

from lsh.adapters import api


def test_health_endpoint() -> None:
    app = api.create_app()
    client = TestClient(app)

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_url_check_endpoint_returns_wrapped_shape() -> None:
    app = api.create_app()
    client = TestClient(app)

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
