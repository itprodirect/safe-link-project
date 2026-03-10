"""Tests for the PolicyPack data model."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from lsh.core.policy import PolicyPack


def test_minimal_policy_creates_with_defaults() -> None:
    policy = PolicyPack(name="test")
    assert policy.name == "test"
    assert policy.description == ""
    assert policy.allowlist_domains == []
    assert policy.allowlist_categories == []
    assert policy.allowlist_findings == []
    assert policy.input_types == ["url"]
    assert policy.enabled is True
    assert policy.tags == []
    assert len(policy.id) == 36  # UUID string


def test_full_policy_round_trips_through_json() -> None:
    policy = PolicyPack(
        name="corp-allowlist",
        description="Trusted corporate domains",
        allowlist_domains=["example.com", "corp.internal"],
        allowlist_categories=["HMG", "ASCII"],
        allowlist_findings=["HMG002_PUNYCODE_VISIBILITY"],
        input_types=["url", "email_headers"],
        enabled=True,
        tags=["production", "trusted"],
    )
    json_str = policy.model_dump_json()
    restored = PolicyPack.model_validate_json(json_str)
    assert restored.name == policy.name
    assert restored.allowlist_domains == policy.allowlist_domains
    assert restored.allowlist_categories == policy.allowlist_categories
    assert restored.allowlist_findings == policy.allowlist_findings
    assert restored.input_types == policy.input_types
    assert restored.tags == policy.tags
    assert restored.id == policy.id


def test_name_too_short_raises() -> None:
    with pytest.raises(ValidationError):
        PolicyPack(name="")


def test_name_too_long_raises() -> None:
    with pytest.raises(ValidationError):
        PolicyPack(name="x" * 121)


def test_invalid_input_type_raises() -> None:
    with pytest.raises(ValidationError):
        PolicyPack(name="bad", input_types=["unknown_type"])


def test_each_policy_gets_unique_id() -> None:
    ids = {PolicyPack(name="a").id for _ in range(20)}
    assert len(ids) == 20


def test_timestamps_are_utc() -> None:
    before = datetime.now(UTC)
    policy = PolicyPack(name="ts-test")
    after = datetime.now(UTC)
    assert before <= policy.created_at <= after
    assert before <= policy.updated_at <= after


def test_disabled_policy() -> None:
    policy = PolicyPack(name="disabled", enabled=False)
    assert policy.enabled is False
