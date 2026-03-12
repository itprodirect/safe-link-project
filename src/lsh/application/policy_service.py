"""Application service wrapper for policy-pack persistence operations."""

from __future__ import annotations

from collections.abc import Mapping

from lsh.core.policy import PolicyPack
from lsh.core.policy_store import PolicyStore


class PolicyService:
    """Typed application seam over the file-backed policy store."""

    def __init__(self, store: PolicyStore | None = None) -> None:
        self._store = store or PolicyStore()

    def list_policies(self) -> list[PolicyPack]:
        return self._store.list_policies()

    def get_policy(self, policy_id: str) -> PolicyPack | None:
        return self._store.get_policy(policy_id)

    def create_policy(self, policy: PolicyPack) -> PolicyPack:
        # Re-validate to keep service behavior deterministic for all callers.
        validated = PolicyPack.model_validate(policy.model_dump())
        return self._store.create_policy(validated)

    def update_policy(
        self,
        policy_id: str,
        updates: Mapping[str, object],
    ) -> PolicyPack | None:
        existing = self._store.get_policy(policy_id)
        if existing is None:
            return None

        merged = existing.model_dump()
        for key, value in updates.items():
            if key not in {"id", "created_at", "updated_at"}:
                merged[key] = value

        validated = PolicyPack.model_validate(merged)
        persisted_updates = validated.model_dump(
            mode="json",
            exclude={"id", "created_at", "updated_at"},
        )
        return self._store.update_policy(policy_id, persisted_updates)

    def delete_policy(self, policy_id: str) -> bool:
        return self._store.delete_policy(policy_id)
