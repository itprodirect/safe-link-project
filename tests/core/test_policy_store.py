"""Tests for the file-based PolicyStore."""

from __future__ import annotations

from pathlib import Path

import pytest

from lsh.core.policy import PolicyPack
from lsh.core.policy_store import PolicyStore


@pytest.fixture()
def store(tmp_path: Path) -> PolicyStore:
    return PolicyStore(store_dir=str(tmp_path))


def _make_policy(name: str = "test", **kwargs: object) -> PolicyPack:
    return PolicyPack(name=name, **kwargs)


def test_list_empty_store(store: PolicyStore) -> None:
    assert store.list_policies() == []


def test_create_and_list(store: PolicyStore) -> None:
    p = _make_policy("alpha")
    store.create_policy(p)
    policies = store.list_policies()
    assert len(policies) == 1
    assert policies[0].name == "alpha"
    assert policies[0].id == p.id


def test_create_multiple(store: PolicyStore) -> None:
    store.create_policy(_make_policy("one"))
    store.create_policy(_make_policy("two"))
    store.create_policy(_make_policy("three"))
    assert len(store.list_policies()) == 3


def test_get_by_id(store: PolicyStore) -> None:
    p = _make_policy("findme")
    store.create_policy(p)
    found = store.get_policy(p.id)
    assert found is not None
    assert found.name == "findme"


def test_get_missing_returns_none(store: PolicyStore) -> None:
    assert store.get_policy("nonexistent-id") is None


def test_update_changes_fields(store: PolicyStore) -> None:
    p = _make_policy("original")
    store.create_policy(p)

    updated = store.update_policy(p.id, {"name": "renamed", "enabled": False})
    assert updated is not None
    assert updated.name == "renamed"
    assert updated.enabled is False
    assert updated.id == p.id  # ID unchanged
    assert updated.created_at == p.created_at  # created_at protected

    # Verify persistence
    reloaded = store.get_policy(p.id)
    assert reloaded is not None
    assert reloaded.name == "renamed"


def test_update_cannot_change_id(store: PolicyStore) -> None:
    p = _make_policy("protect-id")
    store.create_policy(p)
    updated = store.update_policy(p.id, {"id": "new-id"})
    assert updated is not None
    assert updated.id == p.id  # ID preserved


def test_update_cannot_change_created_at(store: PolicyStore) -> None:
    p = _make_policy("protect-ts")
    store.create_policy(p)
    updated = store.update_policy(p.id, {"created_at": "2020-01-01T00:00:00+00:00"})
    assert updated is not None
    assert updated.created_at == p.created_at


def test_update_missing_returns_none(store: PolicyStore) -> None:
    assert store.update_policy("nonexistent", {"name": "nope"}) is None


def test_update_sets_updated_at(store: PolicyStore) -> None:
    p = _make_policy("ts-update")
    store.create_policy(p)
    original_updated = p.updated_at

    updated = store.update_policy(p.id, {"description": "changed"})
    assert updated is not None
    assert updated.updated_at >= original_updated


def test_delete_removes_policy(store: PolicyStore) -> None:
    p = _make_policy("delete-me")
    store.create_policy(p)
    assert len(store.list_policies()) == 1

    result = store.delete_policy(p.id)
    assert result is True
    assert len(store.list_policies()) == 0


def test_delete_missing_returns_false(store: PolicyStore) -> None:
    assert store.delete_policy("nonexistent") is False


def test_delete_only_target(store: PolicyStore) -> None:
    p1 = _make_policy("keep")
    p2 = _make_policy("remove")
    store.create_policy(p1)
    store.create_policy(p2)

    store.delete_policy(p2.id)
    remaining = store.list_policies()
    assert len(remaining) == 1
    assert remaining[0].id == p1.id


def test_store_creates_directory(tmp_path: Path) -> None:
    nested = tmp_path / "deep" / "nested"
    store = PolicyStore(store_dir=str(nested))
    store.create_policy(_make_policy("mkdir-test"))
    assert (nested / "policies.json").exists()


def test_missing_file_returns_empty(store: PolicyStore) -> None:
    """Reading from a nonexistent file should not raise."""
    assert store.list_policies() == []
    assert store.get_policy("any") is None


def test_corrupted_file_non_list(store: PolicyStore) -> None:
    """A file containing non-list JSON should return empty."""
    store.file_path.parent.mkdir(parents=True, exist_ok=True)
    store.file_path.write_text('{"not": "a list"}')
    assert store.list_policies() == []


def test_full_crud_round_trip(store: PolicyStore) -> None:
    """End-to-end: create, read, update, list, delete."""
    p = _make_policy(
        "e2e",
        allowlist_domains=["a.com"],
        allowlist_categories=["HMG"],
        allowlist_findings=["HMG001"],
        tags=["test"],
    )
    created = store.create_policy(p)
    assert created.name == "e2e"

    fetched = store.get_policy(p.id)
    assert fetched is not None
    assert fetched.allowlist_domains == ["a.com"]

    store.update_policy(p.id, {"allowlist_domains": ["a.com", "b.com"]})
    updated = store.get_policy(p.id)
    assert updated is not None
    assert "b.com" in updated.allowlist_domains

    assert len(store.list_policies()) == 1

    store.delete_policy(p.id)
    assert len(store.list_policies()) == 0


def test_env_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_dir = tmp_path / "env-store"
    monkeypatch.setenv("LSH_POLICY_STORE_DIR", str(env_dir))
    store = PolicyStore()
    store.create_policy(_make_policy("env-test"))
    assert (env_dir / "policies.json").exists()
