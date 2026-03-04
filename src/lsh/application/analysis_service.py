"""Shared analysis application service used by CLI and API adapters."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from lsh.core.models import AnalysisInput, AnalysisResult, Finding
from lsh.core.orchestrator import AnalysisOrchestrator
from lsh.modules import (
    AsciiLookalikeDetector,
    EmailAuthDetector,
    HomoglyphDetector,
    NetIPDetector,
    RedirectChainDetector,
    URLStructureDetector,
)


def _build_email_summary(findings: Sequence[Finding], overall_risk: int) -> str:
    """Build a concise summary tuned for email authentication results."""
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


_URL_ORCHESTRATOR = AnalysisOrchestrator(
    modules=[
        NetIPDetector(),
        URLStructureDetector(),
        AsciiLookalikeDetector(),
        HomoglyphDetector(),
        RedirectChainDetector(),
    ]
)
_EMAIL_ORCHESTRATOR = AnalysisOrchestrator(
    modules=[EmailAuthDetector()],
    summary_builder=_build_email_summary,
)


def analyze_url(url: str, metadata: dict[str, object] | None = None) -> AnalysisResult:
    """Analyze one URL using the shared URL orchestrator."""
    return _URL_ORCHESTRATOR.analyze(
        AnalysisInput(input_type="url", content=url, metadata=metadata or {})
    )


def analyze_email(
    headers: str,
    *,
    input_type: Literal["email_headers", "email_file"] = "email_headers",
) -> AnalysisResult:
    """Analyze email headers/content using the shared email orchestrator."""
    return _EMAIL_ORCHESTRATOR.analyze(
        AnalysisInput(input_type=input_type, content=headers)
    )
