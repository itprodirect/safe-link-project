"""Snapshot and parity tests for overlapping v1/v2 single-result contracts."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from lsh.application import analyze_email, analyze_url
from lsh.formatters.structured import build_single_result_payload

_FIXTURE_PATH = Path("tests/fixtures/contracts/v1_v2_single_payloads.json")


def _scrub_runtime_fields(payload: dict[str, object]) -> dict[str, object]:
    """Normalize runtime-variant fields before snapshot comparison."""
    scrubbed = deepcopy(payload)
    item = scrubbed.get("item")
    if isinstance(item, dict):
        result = item.get("result")
        if isinstance(result, dict) and "analyzed_at" in result:
            result["analyzed_at"] = "<TIMESTAMP>"
    return scrubbed


def _build_payloads() -> dict[str, dict[str, object]]:
    url = "https://xn--pple-43d.com"
    metadata = {
        "allowlist_domains": ["xn--pple-43d.com"],
        "allowlist_categories": ["NONE"],
        "allowlist_findings": ["HMG002_PUNYCODE_VISIBILITY"],
        "network_enabled": False,
        "network_max_hops": 5,
        "network_timeout": 3.0,
    }
    url_result = analyze_url(url, metadata)
    headers = "Authentication-Results: mx; spf=fail; dkim=pass; dmarc=pass"
    email_result = analyze_email(headers)

    return {
        "url_v1": _scrub_runtime_fields(
            build_single_result_payload(
                flow="url_check",
                input_type="url",
                subject=url,
                result=url_result,
                include_family=True,
            )
        ),
        "url_v2": _scrub_runtime_fields(
            build_single_result_payload(
                flow="analyze",
                input_type="url",
                subject=url,
                result=url_result,
                include_family=True,
                schema_version="2.0",
            )
        ),
        "email_v1": _scrub_runtime_fields(
            build_single_result_payload(
                flow="email_check",
                input_type="email_headers",
                subject="sample",
                result=email_result,
                include_family=True,
            )
        ),
        "email_v2": _scrub_runtime_fields(
            build_single_result_payload(
                flow="analyze",
                input_type="email_headers",
                subject="sample",
                result=email_result,
                include_family=True,
                schema_version="2.0",
            )
        ),
    }


def test_v1_v2_single_payloads_match_snapshot_fixture() -> None:
    expected = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    assert _build_payloads() == expected


def test_v1_v2_url_overlap_fields_are_parity_consistent() -> None:
    payloads = _build_payloads()
    url_v1 = payloads["url_v1"]
    url_v2 = payloads["url_v2"]
    v1_item = url_v1["item"]
    v2_item = url_v2["item"]

    assert isinstance(v1_item, dict)
    assert isinstance(v2_item, dict)
    assert v1_item["result"] == v2_item["result"]
    assert v1_item["family"] == v2_item["family"]
    assert v1_item["subject"] == v2_item["subject"]


def test_v1_v2_email_overlap_fields_are_parity_consistent() -> None:
    payloads = _build_payloads()
    email_v1 = payloads["email_v1"]
    email_v2 = payloads["email_v2"]
    v1_item = email_v1["item"]
    v2_item = email_v2["item"]

    assert isinstance(v1_item, dict)
    assert isinstance(v2_item, dict)
    assert v1_item["result"] == v2_item["result"]
    assert v1_item["family"] == v2_item["family"]
    assert v1_item["subject"] == v2_item["subject"]

