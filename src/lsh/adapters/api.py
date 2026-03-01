"""Minimal FastAPI adapter for Link Safety Hub."""
# mypy: disable-error-code=untyped-decorator
# mypy: warn_unused_ignores=False

from __future__ import annotations

import os
from collections.abc import Sequence
from typing import Annotated, Any

from pydantic import BaseModel, Field

from lsh.adapters.api_models import (
    ApiErrorEnvelope,
    EmailCheckResponse,
    QRScanResponse,
    UrlCheckResponse,
)
from lsh.core.models import AnalysisInput, AnalysisResult, Finding
from lsh.core.orchestrator import AnalysisOrchestrator
from lsh.formatters.structured import (
    build_qr_scan_payload,
    build_single_result_payload,
)
from lsh.modules import (
    AsciiLookalikeDetector,
    EmailAuthDetector,
    HomoglyphDetector,
    NetIPDetector,
    RedirectChainDetector,
    URLStructureDetector,
)
from lsh.modules.qr_decode import (
    QRDecodeError,
    QRDecodeUnavailableError,
    decode_qr_payloads_from_bytes,
    extract_url_payloads,
)

try:
    from fastapi import (  # type: ignore[import-not-found]
        FastAPI,
        File,
        Form,
        HTTPException,
        Response,
        UploadFile,
    )
    from fastapi.middleware.cors import CORSMiddleware  # type: ignore[import-not-found]
except ImportError:
    FASTAPI_AVAILABLE = False
else:
    FASTAPI_AVAILABLE = True

_SCHEMA_VERSION = "1.0"
_CORS_ORIGINS_ENV = "LSH_API_CORS_ALLOW_ORIGINS"
_DEFAULT_CORS_ORIGINS = ("http://127.0.0.1:3000", "http://localhost:3000")
_QR_LEGACY_KEYS_ENV = "LSH_API_INCLUDE_QR_LEGACY_KEYS"
_QR_LEGACY_KEYS_HEADER = "X-LSH-QR-Legacy-Keys"
_QR_LEGACY_KEYS_HEADER_VALUE = "included; sunset=2026-06-01; use=item/items"
_QR_LEGACY_KEYS_DISABLED_HEADER_VALUE = "disabled"

_URL_ORCHESTRATOR = AnalysisOrchestrator(
    modules=[
        NetIPDetector(),
        URLStructureDetector(),
        AsciiLookalikeDetector(),
        HomoglyphDetector(),
        RedirectChainDetector(),
    ]
)


def _build_email_summary(findings: Sequence[Finding], overall_risk: int) -> str:
    if not findings:
        return "No obvious email authentication issues were found in the provided headers."

    if overall_risk >= 81:
        return (
            "High-risk email-authentication warning. "
            "Do not trust links or urgent requests until independently verified."
        )
    if overall_risk >= 61:
        return (
            "This message has strong authentication warning signs. "
            "Verify sender identity through a trusted channel."
        )
    if overall_risk >= 41:
        return (
            "This message has authentication concerns. "
            "Use caution before acting on requests."
        )
    return (
        "A mild email authentication warning sign was found. "
        "Double-check sensitive requests before taking action."
    )


_EMAIL_ORCHESTRATOR = AnalysisOrchestrator(
    modules=[EmailAuthDetector()],
    summary_builder=_build_email_summary,
)


def _analyze_url_result(url: str, metadata: dict[str, object] | None = None) -> AnalysisResult:
    return _URL_ORCHESTRATOR.analyze(
        AnalysisInput(input_type="url", content=url, metadata=metadata or {})
    )


class URLCheckRequest(BaseModel):
    url: str = Field(min_length=1)
    family: bool = False
    allowlist_domains: list[str] = Field(default_factory=list)
    allowlist_categories: list[str] = Field(default_factory=list)
    network_enabled: bool = False
    network_max_hops: int = Field(default=5, ge=1, le=15)
    network_timeout: float = Field(default=3.0, ge=0.1)


class EmailCheckRequest(BaseModel):
    headers: str = ""
    source_label: str = "inline headers"
    family: bool = False


def _url_metadata(request: URLCheckRequest) -> dict[str, object]:
    metadata: dict[str, object] = {
        "network_enabled": request.network_enabled,
        "network_max_hops": request.network_max_hops,
        "network_timeout": request.network_timeout,
    }
    if request.allowlist_domains:
        metadata["allowlist_domains"] = request.allowlist_domains
    if request.allowlist_categories:
        metadata["allowlist_categories"] = [item.upper() for item in request.allowlist_categories]
    return metadata


def _api_error(
    *,
    status_code: int,
    code: str,
    message: str,
) -> Any:
    if not FASTAPI_AVAILABLE:
        raise RuntimeError("FastAPI is required for API error generation.")
    return HTTPException(
        status_code=status_code,
        detail={
            "schema_version": _SCHEMA_VERSION,
            "error": {
                "code": code,
                "message": message,
                "status": status_code,
            },
        },
    )


def _cors_allowed_origins() -> list[str]:
    raw_value = os.getenv(_CORS_ORIGINS_ENV)
    if raw_value is None:
        return list(_DEFAULT_CORS_ORIGINS)
    return [origin.strip() for origin in raw_value.split(",") if origin.strip()]


def _include_qr_legacy_keys() -> bool:
    raw_value = os.getenv(_QR_LEGACY_KEYS_ENV)
    if raw_value is None:
        return True
    return raw_value.strip().lower() not in {"0", "false", "no", "off"}


_QR_ERROR_RESPONSES: dict[int, dict[str, object]] = {
    400: {"model": ApiErrorEnvelope, "description": "Structured QR request/parse error envelope."},
    503: {"model": ApiErrorEnvelope, "description": "Structured QR decoder-unavailable envelope."},
}


def create_app() -> Any:
    if not FASTAPI_AVAILABLE:
        raise RuntimeError(
            "FastAPI adapter requires optional dependencies. "
            "Install with: pip install -e \".[api]\""
        )

    app = FastAPI(
        title="Link Safety Hub API",
        version="0.1.0",
        description="Minimal API adapter for URL, email, and QR analysis flows.",
    )
    cors_origins = _cors_allowed_origins()
    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=False,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["*"],
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/v1/url/check", response_model=UrlCheckResponse)
    def url_check(request: URLCheckRequest) -> dict[str, object]:
        result = _analyze_url_result(request.url, _url_metadata(request))
        return build_single_result_payload(
            flow="url_check",
            input_type="url",
            subject=request.url,
            result=result,
            include_family=request.family,
        )

    @app.post("/api/v1/email/check", response_model=EmailCheckResponse)
    def email_check(request: EmailCheckRequest) -> dict[str, object]:
        result = _EMAIL_ORCHESTRATOR.analyze(
            AnalysisInput(input_type="email_headers", content=request.headers)
        )
        return build_single_result_payload(
            flow="email_check",
            input_type="email_headers",
            subject=request.source_label,
            result=result,
            include_family=request.family,
        )

    @app.post("/api/v1/qr/scan", response_model=QRScanResponse, responses=_QR_ERROR_RESPONSES)
    async def qr_scan(
        response: Response,
        file: Annotated[UploadFile, File(...)],
        analyze_all: Annotated[bool, Form()] = False,
        family: Annotated[bool, Form()] = False,
    ) -> dict[str, object]:
        image_name = (file.filename or "uploaded-image").strip() or "uploaded-image"
        try:
            image_bytes = await file.read()
        except Exception as exc:
            raise _api_error(
                status_code=400,
                code="QRC_IMAGE_READ_ERROR",
                message=f"Could not read uploaded image '{image_name}': {exc}",
            ) from exc
        finally:
            await file.close()

        try:
            decoded_payloads = decode_qr_payloads_from_bytes(
                image_bytes,
                image_name=image_name,
            )
        except QRDecodeUnavailableError as exc:
            raise _api_error(
                status_code=503,
                code="QRC_DECODER_UNAVAILABLE",
                message=f"QR scanning unavailable: {exc}",
            ) from exc
        except QRDecodeError as exc:
            raise _api_error(
                status_code=400,
                code="QRC_IMAGE_READ_ERROR",
                message=str(exc),
            ) from exc

        if not decoded_payloads:
            raise _api_error(
                status_code=400,
                code="QRC_NO_PAYLOADS",
                message="No QR payloads were decoded from the image.",
            )

        url_payloads = extract_url_payloads(decoded_payloads)
        if not url_payloads:
            raise _api_error(
                status_code=400,
                code="QRC_NO_URL_PAYLOADS",
                message="Decoded QR payloads did not contain URL-like values.",
            )

        selected_urls = url_payloads if analyze_all else [url_payloads[0]]
        url_results = [(url, _analyze_url_result(url)) for url in selected_urls]
        include_legacy_keys = _include_qr_legacy_keys()

        response.headers[_QR_LEGACY_KEYS_HEADER] = (
            _QR_LEGACY_KEYS_HEADER_VALUE
            if include_legacy_keys
            else _QR_LEGACY_KEYS_DISABLED_HEADER_VALUE
        )

        return build_qr_scan_payload(
            image_path=image_name,
            decoded_payloads=decoded_payloads,
            url_results=url_results,
            analyzed_all=analyze_all,
            include_family=family,
            include_legacy_keys=include_legacy_keys,
        )

    return app


app: Any | None = create_app() if FASTAPI_AVAILABLE else None
