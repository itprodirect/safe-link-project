"""Compatibility loader for the optional ``confusables`` dependency."""

from __future__ import annotations

import importlib.util
import json
from functools import lru_cache
from itertools import product
from pathlib import Path

_MAPPING_RELATIVE_PATH = Path("assets") / "confusable_mapping.json"
_NON_NORMAL_ASCII_CHARS = {"@"}


class ConfusablesCompat:
    """Minimal subset of the third-party confusables API used by this project."""

    def __init__(self, mapping: dict[str, list[str]]) -> None:
        self._mapping = mapping

    def confusable_characters(self, value: str) -> list[str] | None:
        mapped_chars = self._mapping.get(value)
        if mapped_chars is not None:
            return mapped_chars
        if len(value) <= 1:
            return [value]
        return None

    def normalize(self, value: str, *, prioritize_alpha: bool = False) -> list[str]:
        normal_forms = {""}
        for character in value:
            normalized_chars: list[str] = []
            confusable_chars = self.confusable_characters(character) or [character]
            if not character.isascii() or not character.isalpha():
                for confusable in confusable_chars:
                    if not confusable.isascii() or confusable in _NON_NORMAL_ASCII_CHARS:
                        continue
                    if prioritize_alpha:
                        is_ascii_alpha = character.isalpha() and confusable.isalpha()
                        is_ascii_non_alpha = not character.isalpha()
                        if not (is_ascii_alpha or is_ascii_non_alpha):
                            continue
                    normal = confusable
                    if len(confusable) > 1:
                        normal = self.normalize(confusable)[0]
                    normalized_chars.append(normal)
            else:
                normalized_chars = [character]

            if not normalized_chars:
                normalized_chars = [character]
            normal_forms = {
                prefix + suffix.lower()
                for prefix, suffix in product(normal_forms, normalized_chars)
            }
        return sorted(normal_forms)


@lru_cache(maxsize=1)
def load_confusables_compat() -> ConfusablesCompat | None:
    """Load confusable mappings without importing the broken package entrypoint."""
    spec = importlib.util.find_spec("confusables")
    if spec is None or not spec.submodule_search_locations:
        return None

    package_dir = Path(next(iter(spec.submodule_search_locations)))
    mapping_path = package_dir / _MAPPING_RELATIVE_PATH
    try:
        raw_mapping = mapping_path.read_text(encoding="utf-8")
    except OSError:
        return None

    mapping = json.loads(raw_mapping)
    if not isinstance(mapping, dict):
        return None
    normalized_mapping = {
        key: value
        for key, value in mapping.items()
        if isinstance(key, str)
        and isinstance(value, list)
        and all(isinstance(item, str) for item in value)
    }
    return ConfusablesCompat(normalized_mapping)
