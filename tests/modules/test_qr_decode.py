"""Tests for QR decode helper behavior."""

from lsh.modules.qr_decode import extract_url_payloads


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
