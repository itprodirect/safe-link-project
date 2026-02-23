"""QR decode helpers and optional detector for local QR image payloads."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from lsh.core.models import AnalysisInput, Confidence, Evidence, Finding, ModuleInterface, Severity
from lsh.core.url_tools import parse_url_like

try:
    from PIL import Image
except Exception as exc:  # pragma: no cover - environment-dependent optional dependency
    Image = None  # type: ignore[assignment]
    _PIL_IMPORT_ERROR: Exception | None = exc
else:
    _PIL_IMPORT_ERROR = None

try:
    from pyzbar.pyzbar import decode as _pyzbar_decode  # type: ignore[import-untyped]
except Exception as exc:  # pragma: no cover - environment-dependent optional dependency
    _pyzbar_decode = None
    _PYZBAR_IMPORT_ERROR: Exception | None = exc
else:
    _PYZBAR_IMPORT_ERROR = None


class QRDecodeUnavailableError(RuntimeError):
    """Raised when QR decoding dependencies/backends are unavailable."""


class QRDecodeError(RuntimeError):
    """Raised when an image cannot be read or decoded."""


def _require_decoder() -> None:
    if Image is None:
        raise QRDecodeUnavailableError(
            "QR decoding is unavailable because Pillow is not installed."
        ) from _PIL_IMPORT_ERROR
    if _pyzbar_decode is None:
        raise QRDecodeUnavailableError(
            "QR decoding is unavailable because the zbar backend (pyzbar) is not available."
        ) from _PYZBAR_IMPORT_ERROR


def decode_qr_payloads_from_image(image_path: str | Path) -> list[str]:
    """Decode QR payload strings from a local image path."""
    _require_decoder()
    assert Image is not None
    assert _pyzbar_decode is not None

    path = Path(image_path)
    try:
        with Image.open(path) as image:
            decoded_objects = _pyzbar_decode(image)
    except OSError as exc:
        raise QRDecodeError(f"Could not open or decode image '{path}': {exc}") from exc

    payloads: list[str] = []
    seen: set[str] = set()
    for obj in decoded_objects:
        raw_data = getattr(obj, "data", b"")
        if not isinstance(raw_data, (bytes, bytearray)):
            continue
        text = bytes(raw_data).decode("utf-8", errors="replace").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        payloads.append(text)
    return payloads


def extract_url_payloads(payloads: list[str]) -> list[str]:
    """Return HTTP(S) URL payloads from decoded QR text values."""
    urls: list[str] = []
    for payload in payloads:
        candidate = payload.strip()
        if not candidate or any(ch.isspace() for ch in candidate):
            continue

        direct = urlparse(candidate)
        if direct.scheme and direct.scheme not in {"http", "https"}:
            continue
        if not direct.scheme and not candidate.startswith("//"):
            continue

        parsed = parse_url_like(payload)
        if parsed.hostname is None:
            continue
        urls.append(candidate)
    return urls


class QRDecodeDetector(ModuleInterface):
    """Optional detector that reports basic QR decode success/failure signals."""

    @property
    def name(self) -> str:
        return "qr_decode"

    @property
    def version(self) -> str:
        return "0.1.0"

    def analyze(self, input: AnalysisInput) -> list[Finding]:
        if input.input_type != "qr_image":
            return []

        image_path = input.content
        try:
            payloads = decode_qr_payloads_from_image(image_path)
        except QRDecodeUnavailableError as exc:
            return [
                self._finding(
                    category="QRC000_DECODER_UNAVAILABLE",
                    risk_score=10,
                    confidence=Confidence.HIGH,
                    title="QR decoder backend is unavailable",
                    family_explanation=(
                        "QR scanning is not available on this system yet."
                    ),
                    explanation=str(exc),
                    evidence=[Evidence(label="Image Path", value=image_path)],
                    recommendations=[
                        "Install QR decoding dependencies (Pillow + pyzbar + zbar backend).",
                    ],
                )
            ]
        except QRDecodeError as exc:
            return [
                self._finding(
                    category="QRC001_IMAGE_READ_ERROR",
                    risk_score=10,
                    confidence=Confidence.MEDIUM,
                    title="QR image could not be decoded",
                    family_explanation=(
                        "This image could not be read as a QR code."
                    ),
                    explanation=str(exc),
                    evidence=[Evidence(label="Image Path", value=image_path)],
                    recommendations=[
                        "Verify the image file and try a clearer QR image.",
                    ],
                )
            ]

        if not payloads:
            return [
                self._finding(
                    category="QRC002_NO_PAYLOADS_FOUND",
                    risk_score=5,
                    confidence=Confidence.LOW,
                    title="No QR payloads were detected",
                    family_explanation="No QR code was found in this image.",
                    explanation="The image was read successfully, but no QR payloads were decoded.",
                    evidence=[Evidence(label="Image Path", value=image_path)],
                    recommendations=["Try a clearer image or crop tightly around the QR code."],
                )
            ]

        return [
            self._finding(
                category="QRC100_URL_PAYLOADS_DECODED",
                risk_score=0,
                confidence=Confidence.HIGH,
                title="QR payloads decoded",
                family_explanation="The QR code was read successfully.",
                explanation="One or more QR payloads were decoded from the image.",
                evidence=[
                    Evidence(label="Image Path", value=image_path),
                    Evidence(label="Payload Count", value=str(len(payloads))),
                ],
                recommendations=[],
            )
        ]

    def _finding(
        self,
        *,
        category: str,
        risk_score: int,
        confidence: Confidence,
        title: str,
        explanation: str,
        family_explanation: str,
        evidence: list[Evidence],
        recommendations: list[str],
    ) -> Finding:
        return Finding(
            module=self.name,
            category=category,
            severity=Severity.INFO,
            confidence=confidence,
            risk_score=risk_score,
            title=title,
            explanation=explanation,
            family_explanation=family_explanation,
            evidence=evidence,
            recommendations=recommendations,
        )
