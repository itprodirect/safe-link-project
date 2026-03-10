"""Resolve policy packs into analysis metadata.

Merges a stored policy pack's suppression rules with inline allowlist
parameters using union semantics.  Inline params continue to work
independently; policy packs are additive.
"""

from __future__ import annotations

from lsh.core.policy import PolicyPack


def resolve_metadata_with_policy(
    metadata: dict[str, object],
    policy: PolicyPack | None,
    *,
    input_type: str = "url",
) -> dict[str, object]:
    """Merge a policy pack's rules into existing request metadata.

    Returns a new dict (does not mutate *metadata*).

    Rules:
    - If *policy* is ``None`` or disabled, return *metadata* unchanged.
    - If *input_type* is not in ``policy.input_types``, return unchanged.
    - Otherwise union each allowlist axis (domains, categories, findings)
      and tag the merged dict with policy provenance metadata.
    """
    if policy is None or not policy.enabled:
        return metadata

    if input_type not in policy.input_types:
        return metadata

    merged: dict[str, object] = dict(metadata)

    merged["allowlist_domains"] = _union_str_lists(
        merged.get("allowlist_domains"), policy.allowlist_domains
    )
    merged["allowlist_categories"] = _union_str_lists(
        merged.get("allowlist_categories"), policy.allowlist_categories
    )
    merged["allowlist_findings"] = _union_str_lists(
        merged.get("allowlist_findings"), policy.allowlist_findings
    )

    # Provenance tags for audit/trace visibility
    merged["_applied_policy_id"] = policy.id
    merged["_applied_policy_name"] = policy.name

    return merged


def _union_str_lists(
    existing: object, additions: list[str]
) -> list[str]:
    """Union two string lists, deduplicating while preserving order."""
    base = _to_str_list(existing)
    seen: set[str] = set(base)
    result = list(base)
    for item in additions:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _to_str_list(value: object) -> list[str]:
    """Coerce a value to a list of strings."""
    if value is None:
        return []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return []
