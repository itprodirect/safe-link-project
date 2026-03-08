"""Typed API contract models for FastAPI response validation and OpenAPI docs."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from lsh.core.models import AnalysisResult


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
    label: str
    value: str


class AnalystEvidenceRowPayload(_StrictModel):
    module: str
    category: str
    severity: str
    confidence: str
    cumulative_risk_score: int
    title: str
    explanation: str
    family_explanation: str
    recommendations: list[str]
    evidence: list[EvidenceValuePayload]


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
