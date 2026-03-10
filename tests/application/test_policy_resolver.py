"""Tests for policy pack metadata resolution."""

from __future__ import annotations

from lsh.application.policy_resolver import resolve_metadata_with_policy
from lsh.core.policy import PolicyPack


def _policy(**kwargs: object) -> PolicyPack:
    defaults: dict[str, object] = {"name": "test-policy"}
    defaults.update(kwargs)
    return PolicyPack(**defaults)


def test_none_policy_returns_metadata_unchanged() -> None:
    metadata: dict[str, object] = {"allowlist_domains": ["a.com"]}
    result = resolve_metadata_with_policy(metadata, None)
    assert result is metadata  # same object, not copied


def test_disabled_policy_returns_metadata_unchanged() -> None:
    policy = _policy(enabled=False, allowlist_domains=["b.com"])
    metadata: dict[str, object] = {"allowlist_domains": ["a.com"]}
    result = resolve_metadata_with_policy(metadata, policy)
    assert result is metadata


def test_input_type_mismatch_returns_unchanged() -> None:
    policy = _policy(input_types=["email_headers"], allowlist_domains=["b.com"])
    metadata: dict[str, object] = {}
    result = resolve_metadata_with_policy(metadata, policy, input_type="url")
    assert result is metadata


def test_unions_domains() -> None:
    policy = _policy(allowlist_domains=["b.com", "c.com"])
    metadata: dict[str, object] = {"allowlist_domains": ["a.com", "b.com"]}
    result = resolve_metadata_with_policy(metadata, policy)
    domains = result["allowlist_domains"]
    assert isinstance(domains, list)
    assert set(domains) == {"a.com", "b.com", "c.com"}


def test_unions_categories() -> None:
    policy = _policy(allowlist_categories=["URL", "NET"])
    metadata: dict[str, object] = {"allowlist_categories": ["HMG"]}
    result = resolve_metadata_with_policy(metadata, policy)
    cats = result["allowlist_categories"]
    assert isinstance(cats, list)
    assert set(cats) == {"HMG", "URL", "NET"}


def test_unions_findings() -> None:
    policy = _policy(allowlist_findings=["HMG002_PUNYCODE_VISIBILITY"])
    metadata: dict[str, object] = {"allowlist_findings": ["URL001"]}
    result = resolve_metadata_with_policy(metadata, policy)
    findings = result["allowlist_findings"]
    assert isinstance(findings, list)
    assert set(findings) == {"URL001", "HMG002_PUNYCODE_VISIBILITY"}


def test_empty_metadata_gets_policy_values() -> None:
    policy = _policy(
        allowlist_domains=["trusted.com"],
        allowlist_categories=["ALL"],
        allowlist_findings=["NET001"],
    )
    result = resolve_metadata_with_policy({}, policy)
    assert result["allowlist_domains"] == ["trusted.com"]
    assert result["allowlist_categories"] == ["ALL"]
    assert result["allowlist_findings"] == ["NET001"]


def test_does_not_mutate_original_metadata() -> None:
    policy = _policy(allowlist_domains=["new.com"])
    original: dict[str, object] = {"allowlist_domains": ["old.com"]}
    result = resolve_metadata_with_policy(original, policy)
    assert result is not original
    assert original["allowlist_domains"] == ["old.com"]  # not mutated


def test_tags_provenance_metadata() -> None:
    policy = _policy()
    result = resolve_metadata_with_policy({}, policy)
    assert result["_applied_policy_id"] == policy.id
    assert result["_applied_policy_name"] == policy.name


def test_preserves_non_allowlist_metadata() -> None:
    policy = _policy(allowlist_domains=["x.com"])
    metadata: dict[str, object] = {
        "network_enabled": True,
        "network_max_hops": 10,
        "custom_field": "keep",
    }
    result = resolve_metadata_with_policy(metadata, policy)
    assert result["network_enabled"] is True
    assert result["network_max_hops"] == 10
    assert result["custom_field"] == "keep"


def test_email_input_type_scoping() -> None:
    policy = _policy(
        input_types=["url", "email_headers"],
        allowlist_domains=["mail.example.com"],
    )
    # Should apply to email_headers
    result = resolve_metadata_with_policy({}, policy, input_type="email_headers")
    assert result["allowlist_domains"] == ["mail.example.com"]

    # Should NOT apply to email_file (not in input_types)
    result2 = resolve_metadata_with_policy({}, policy, input_type="email_file")
    assert result2 == {}


def test_csv_string_metadata_coercion() -> None:
    """Metadata values that are CSV strings should be parsed correctly."""
    policy = _policy(allowlist_domains=["new.com"])
    metadata: dict[str, object] = {"allowlist_domains": "old.com, legacy.com"}
    result = resolve_metadata_with_policy(metadata, policy)
    domains = result["allowlist_domains"]
    assert isinstance(domains, list)
    assert set(domains) == {"old.com", "legacy.com", "new.com"}


def test_deduplication_preserves_order() -> None:
    policy = _policy(allowlist_domains=["c.com", "a.com"])
    metadata: dict[str, object] = {"allowlist_domains": ["a.com", "b.com"]}
    result = resolve_metadata_with_policy(metadata, policy)
    domains = result["allowlist_domains"]
    assert isinstance(domains, list)
    # Original order preserved, then new additions
    assert domains == ["a.com", "b.com", "c.com"]
