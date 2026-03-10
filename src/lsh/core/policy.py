"""Policy pack data model for persisted suppression configurations."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class PolicyPack(BaseModel):
    """A named, persisted suppression policy.

    Captures the same three suppression axes as inline allowlist params
    (domains, categories, findings) plus metadata for identity and lifecycle.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(min_length=1, max_length=120)
    description: str = ""

    # Suppression rules (same keys as AnalysisInput.metadata allowlist params)
    allowlist_domains: list[str] = Field(default_factory=list)
    allowlist_categories: list[str] = Field(default_factory=list)
    allowlist_findings: list[str] = Field(default_factory=list)

    # Scoping: which input types this policy applies to
    input_types: list[Literal["url", "email_headers", "email_file"]] = Field(
        default=["url"],
    )

    enabled: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    tags: list[str] = Field(default_factory=list)
