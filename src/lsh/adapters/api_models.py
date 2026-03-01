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


class WrappedItem(_StrictModel):
    subject: str
    result: AnalysisResult
    family: FamilyPayload | None = None


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
