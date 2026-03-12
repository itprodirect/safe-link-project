"""Typed API contract models for FastAPI response validation and OpenAPI docs."""

from __future__ import annotations

from typing import Annotated, Literal, cast

from pydantic import BaseModel, ConfigDict, Field, model_validator

from lsh.core.models import AnalysisResult
from lsh.core.policy import PolicyPack


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FamilyPayload(_StrictModel):
    risk_score: int
    severity: str
    summary: str
    signal_confidence: str | None = None
    reasons: list[str]
    recommendations: list[str]


class EvidenceValuePayload(_StrictModel):
    key: str
    label: str
    value: str


class AnalystEvidenceRowPayload(_StrictModel):
    module: str
    category: str
    finding_key: str
    compare_key: str
    sort_index: int = Field(ge=0)
    severity: str
    confidence: str
    cumulative_risk_score: int
    risk_delta: int | None = None
    title: str
    explanation: str
    family_explanation: str
    recommendations: list[str]
    evidence: list[EvidenceValuePayload]
    evidence_map: dict[str, str]


class DomainAnatomyPayload(_StrictModel):
    submitted_url: str
    canonical_url: str
    hostname: str | None = None
    canonical_hostname: str | None = None
    registrable_domain: str | None = None
    canonical_registrable_domain: str | None = None
    subdomain_labels: list[str]
    registrable_labels: list[str]
    idna_ascii_hostname: str | None = None
    idna_unicode_hostname: str | None = None
    is_ip_literal: bool
    ip_literal: str | None = None
    obfuscated_ipv4: str | None = None
    obfuscated_ipv4_notes: list[str]
    ipv6_mapped_ipv4: str | None = None
    normalization_notes: list[str]


class RedirectTracePayload(_StrictModel):
    hops: list[str]
    start_url: str
    final_url: str
    registrable_domain_path: list[str]
    hop_count: int = Field(ge=0)
    crosses_registrable_domain: bool
    max_hops_reached: bool
    timed_out: bool
    loop_target: str | None = None
    request_error: str | None = None


class SuppressionTraceRowPayload(_StrictModel):
    module: str
    category: str
    finding_key: str
    compare_key: str
    sort_index: int = Field(ge=0)
    hostname: str
    matched_allowlist_domain: str
    suppression_scope: Literal["category", "finding"]
    matched_rule: str
    reason: str


class SuppressionTracePayload(_StrictModel):
    hostname: str | None = None
    configured_allowlist_domains: list[str]
    configured_allowlist_categories: list[str]
    configured_allowlist_findings: list[str]
    matched_allowlist_domains: list[str]
    suppressed_count: int = Field(ge=0)
    suppressed_rows: list[SuppressionTraceRowPayload]


class UrlAnalystPayload(_StrictModel):
    domain_anatomy: DomainAnatomyPayload
    evidence_rows: list[AnalystEvidenceRowPayload]
    redirect_trace: RedirectTracePayload | None = None
    suppression_trace: SuppressionTracePayload | None = None


class WrappedItem(_StrictModel):
    subject: str
    result: AnalysisResult
    family: FamilyPayload | None = None


class WrappedItemV2(WrappedItem):
    analyst: UrlAnalystPayload | None = None


class UrlCheckResponse(_StrictModel):
    schema_version: Literal["1.0"]
    flow: Literal["url_check"]
    mode: Literal["single"]
    input_type: Literal["url"]
    item_count: Literal[1]
    item: WrappedItem


class EmailCheckResponse(_StrictModel):
    schema_version: Literal["1.0"]
    flow: Literal["email_check"]
    mode: Literal["single"]
    input_type: Literal["email_headers"]
    item_count: Literal[1]
    item: WrappedItem


class AnalyzeV2Response(_StrictModel):
    schema_version: Literal["2.0"]
    flow: Literal["analyze"]
    mode: Literal["single"]
    input_type: Literal["url", "email_headers", "email_file"]
    item_count: Literal[1]
    item: WrappedItemV2


class PolicyCreateRequest(_StrictModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = ""
    allowlist_domains: list[str] = Field(default_factory=list)
    allowlist_categories: list[str] = Field(default_factory=list)
    allowlist_findings: list[str] = Field(default_factory=list)
    input_types: list[Literal["url", "email_headers", "email_file"]] = Field(
        default_factory=lambda: cast(
            list[Literal["url", "email_headers", "email_file"]],
            ["url"],
        )
    )
    enabled: bool = True
    tags: list[str] = Field(default_factory=list)

    def to_policy_pack(self) -> PolicyPack:
        return PolicyPack.model_validate(self.model_dump())


class PolicyUpdateRequest(_StrictModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    allowlist_domains: list[str] | None = None
    allowlist_categories: list[str] | None = None
    allowlist_findings: list[str] | None = None
    input_types: list[Literal["url", "email_headers", "email_file"]] | None = None
    enabled: bool | None = None
    tags: list[str] | None = None

    @model_validator(mode="after")
    def _validate_non_empty_update(self) -> PolicyUpdateRequest:
        if not self.model_dump(exclude_none=True):
            raise ValueError("At least one field must be provided.")
        return self

    def to_updates(self) -> dict[str, object]:
        return self.model_dump(exclude_none=True)


class PolicyListResponse(_StrictModel):
    schema_version: Literal["2.0"]
    flow: Literal["policies_list"]
    item_count: int = Field(ge=0)
    items: list[PolicyPack]


class PolicyItemResponse(_StrictModel):
    schema_version: Literal["2.0"]
    flow: Literal["policies_get", "policies_create", "policies_update"]
    item: PolicyPack


class PolicyDeleteResponse(_StrictModel):
    schema_version: Literal["2.0"]
    flow: Literal["policies_delete"]
    id: str
    deleted: bool


class QRLegacyResultItem(_StrictModel):
    url: str
    result: AnalysisResult


class QRScanSingleResponse(_StrictModel):
    schema_version: Literal["1.0"]
    flow: Literal["qr_scan"]
    mode: Literal["single"]
    input_type: Literal["url"]
    image_name: str
    image_path: str | None = None
    decoded_payloads: list[str]
    decoded_payload_count: int = Field(ge=0)
    url_payload_count: int = Field(ge=1)
    analyzed_all: Literal[False]
    item_count: Literal[1]
    item: WrappedItem
    selected_url: str | None = None
    result: AnalysisResult | None = None


class QRScanMultiResponse(_StrictModel):
    schema_version: Literal["1.0"]
    flow: Literal["qr_scan"]
    mode: Literal["multi"]
    input_type: Literal["url"]
    image_name: str
    image_path: str | None = None
    decoded_payloads: list[str]
    decoded_payload_count: int = Field(ge=0)
    url_payload_count: int = Field(ge=1)
    analyzed_all: Literal[True]
    item_count: int = Field(ge=1)
    items: list[WrappedItem]
    results: list[QRLegacyResultItem] | None = None


QRScanResponse = Annotated[QRScanSingleResponse | QRScanMultiResponse, Field(discriminator="mode")]


class ApiErrorObject(_StrictModel):
    code: str
    message: str
    status: int = Field(ge=400, le=599)


class ApiErrorDetail(_StrictModel):
    schema_version: Literal["1.0"]
    error: ApiErrorObject


class ApiErrorEnvelope(_StrictModel):
    detail: ApiErrorDetail
