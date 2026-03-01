"""Minimal FastAPI adapter for Link Safety Hub."""
# mypy: disable-error-code=untyped-decorator

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pydantic import BaseModel, Field

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
    decode_qr_payloads_from_image,
    extract_url_payloads,
)

try:
    from fastapi import FastAPI, HTTPException  # type: ignore[import-not-found]
except ImportError:
    FASTAPI_AVAILABLE = False
else:
    FASTAPI_AVAILABLE = True

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


class QRScanRequest(BaseModel):
    image_path: str = Field(min_length=1)
    analyze_all: bool = False
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

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/v1/url/check")
    def url_check(request: URLCheckRequest) -> dict[str, object]:
        result = _analyze_url_result(request.url, _url_metadata(request))
        return build_single_result_payload(
            flow="url_check",
            input_type="url",
            subject=request.url,
            result=result,
            include_family=request.family,
        )

    @app.post("/api/v1/email/check")
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

    @app.post("/api/v1/qr/scan")
    def qr_scan(request: QRScanRequest) -> dict[str, object]:
        try:
            decoded_payloads = decode_qr_payloads_from_image(request.image_path)
        except QRDecodeUnavailableError as exc:
            raise HTTPException(status_code=503, detail=f"QR scanning unavailable: {exc}") from exc
        except QRDecodeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        if not decoded_payloads:
            raise HTTPException(
                status_code=400,
                detail="No QR payloads were decoded from the image.",
            )

        url_payloads = extract_url_payloads(decoded_payloads)
        if not url_payloads:
            raise HTTPException(
                status_code=400,
                detail="Decoded QR payloads did not contain URL-like values.",
            )

        selected_urls = url_payloads if request.analyze_all else [url_payloads[0]]
        url_results = [(url, _analyze_url_result(url)) for url in selected_urls]

        return build_qr_scan_payload(
            image_path=request.image_path,
            decoded_payloads=decoded_payloads,
            url_results=url_results,
            analyzed_all=request.analyze_all,
            include_family=request.family,
        )

    return app


app: Any | None = create_app() if FASTAPI_AVAILABLE else None
