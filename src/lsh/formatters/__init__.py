"""Reusable output formatters for CLI and future adapters."""

from lsh.formatters.family import FamilyView, build_family_view, render_family_lines
from lsh.formatters.structured import (
    build_multi_result_payload,
    build_qr_scan_payload,
    build_single_result_payload,
)

__all__ = [
    "FamilyView",
    "build_family_view",
    "build_multi_result_payload",
    "build_qr_scan_payload",
    "build_single_result_payload",
    "render_family_lines",
]
