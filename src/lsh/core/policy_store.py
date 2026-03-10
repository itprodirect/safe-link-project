"""File-based JSON storage for policy packs."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

from lsh.core.policy import PolicyPack

_DEFAULT_STORE_DIR = ".lsh"
_POLICY_FILE = "policies.json"
_LSH_STORE_DIR_ENV = "LSH_POLICY_STORE_DIR"


class PolicyStore:
    """CRUD operations for policy packs backed by a single JSON file.

    Storage layout::

        <store_dir>/policies.json   # JSON array of serialized PolicyPack objects

    The store directory defaults to ``.lsh/`` in the working directory and can
    be overridden via the ``LSH_POLICY_STORE_DIR`` environment variable or the
    ``store_dir`` constructor argument.
    """

    def __init__(self, store_dir: str | None = None) -> None:
        env_dir = os.getenv(_LSH_STORE_DIR_ENV)
        self._store_dir = Path(store_dir or env_dir or _DEFAULT_STORE_DIR)
        self._file_path = self._store_dir / _POLICY_FILE

    @property
    def file_path(self) -> Path:
        return self._file_path

    def _read_all_raw(self) -> list[dict[str, object]]:
        if not self._file_path.exists():
            return []
        with open(self._file_path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        return data

    def _write_all_raw(self, policies: list[dict[str, object]]) -> None:
        self._store_dir.mkdir(parents=True, exist_ok=True)
        with open(self._file_path, "w", encoding="utf-8") as f:
            json.dump(policies, f, indent=2, default=str)

    def list_policies(self) -> list[PolicyPack]:
        """Return all stored policy packs."""
        return [PolicyPack.model_validate(item) for item in self._read_all_raw()]

    def get_policy(self, policy_id: str) -> PolicyPack | None:
        """Return a single policy pack by ID, or ``None`` if not found."""
        for item in self._read_all_raw():
            if item.get("id") == policy_id:
                return PolicyPack.model_validate(item)
        return None

    def create_policy(self, policy: PolicyPack) -> PolicyPack:
        """Persist a new policy pack and return it."""
        all_data = self._read_all_raw()
        all_data.append(json.loads(policy.model_dump_json()))
        self._write_all_raw(all_data)
        return policy

    def update_policy(
        self, policy_id: str, updates: dict[str, object]
    ) -> PolicyPack | None:
        """Apply partial updates to an existing policy pack.

        Returns the updated policy, or ``None`` if the ID was not found.
        Protected fields (``id``, ``created_at``) cannot be changed.
        """
        all_data = self._read_all_raw()
        for i, item in enumerate(all_data):
            if item.get("id") == policy_id:
                for key, value in updates.items():
                    if key not in ("id", "created_at"):
                        item[key] = value
                item["updated_at"] = datetime.now(UTC).isoformat()
                all_data[i] = item
                self._write_all_raw(all_data)
                return PolicyPack.model_validate(item)
        return None

    def delete_policy(self, policy_id: str) -> bool:
        """Delete a policy pack by ID. Returns ``True`` if found and removed."""
        all_data = self._read_all_raw()
        filtered = [item for item in all_data if item.get("id") != policy_id]
        if len(filtered) == len(all_data):
            return False
        self._write_all_raw(filtered)
        return True
