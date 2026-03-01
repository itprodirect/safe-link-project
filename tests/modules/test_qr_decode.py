"""Tests for QR decode helper behavior."""

from __future__ import annotations

from pathlib import Path

import pytest

from lsh.modules.qr_decode import (
    QRDecodeUnavailableError,
    decode_qr_payloads_from_bytes,
    decode_qr_payloads_from_image,
    extract_url_payloads,
)

_QR_FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "qr"
_QR_TEXT_FIXTURE = _QR_FIXTURE_DIR / "qrcode_text.png"
_QR_ROTATED_FIXTURE = _QR_FIXTURE_DIR / "qrcode_text_rotated.png"
_QR_EMPTY_FIXTURE = _QR_FIXTURE_DIR / "empty.png"
_EXPECTED_TEXT_PAYLOAD = "Thalassiodracon"


@pytest.fixture(scope="module")
def _require_qr_decoder() -> None:
    try:
        decode_qr_payloads_from_image(_QR_TEXT_FIXTURE)
    except QRDecodeUnavailableError as exc:  # pragma: no cover - env dependent
        pytest.skip(f"QR decoder backend unavailable in test environment: {exc}")


def test_decode_qr_payloads_from_fixture_image(_require_qr_decoder: None) -> None:
    payloads = decode_qr_payloads_from_image(_QR_TEXT_FIXTURE)
    assert payloads == [_EXPECTED_TEXT_PAYLOAD]


def test_decode_qr_payloads_from_rotated_fixture_image(_require_qr_decoder: None) -> None:
    payloads = decode_qr_payloads_from_image(_QR_ROTATED_FIXTURE)
    assert payloads == [_EXPECTED_TEXT_PAYLOAD]


def test_decode_qr_payloads_from_fixture_bytes(_require_qr_decoder: None) -> None:
    payloads = decode_qr_payloads_from_bytes(_QR_TEXT_FIXTURE.read_bytes())
    assert payloads == [_EXPECTED_TEXT_PAYLOAD]


def test_decode_qr_payloads_empty_fixture_returns_no_payloads(_require_qr_decoder: None) -> None:
    payloads = decode_qr_payloads_from_image(_QR_EMPTY_FIXTURE)
    assert payloads == []


def test_extract_url_payloads_filters_to_http_like_urls() -> None:
    payloads = [
        "https://example.com",
        "http://google.com:80@evil.com",
        "mailto:test@example.com",
        "plain text",
    ]

    assert extract_url_payloads(payloads) == [
        "https://example.com",
        "http://google.com:80@evil.com",
    ]


def test_extract_url_payloads_accepts_whitespace_wrapped_urls() -> None:
    payloads = [
        "  https://example.com/login  ",
        "\nhttp://google.com:80@evil.com\t",
        "   ",
    ]

    assert extract_url_payloads(payloads) == [
        "https://example.com/login",
        "http://google.com:80@evil.com",
    ]
