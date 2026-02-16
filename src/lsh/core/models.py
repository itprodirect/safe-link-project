"""Core data models for Link Safety Hub."""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class Severity(StrEnum):
    """Risk severity levels mapped to score bands."""

    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Confidence(StrEnum):
    """Detector confidence labels for user trust calibration."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class AnalysisInput(BaseModel):
    """What goes into a module."""

    input_type: Literal["url", "email_headers", "email_file", "qr_image", "text"]
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class Evidence(BaseModel):
    """Supporting data for a finding."""

    label: str
    value: str


class Finding(BaseModel):
    """What comes out of a module."""

    module: str
    category: str
    severity: Severity
    confidence: Confidence = Confidence.MEDIUM
    risk_score: int = Field(ge=0, le=100)
    title: str
    explanation: str
    family_explanation: str
    evidence: list[Evidence] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    """Aggregated output from the orchestrator."""

    input: AnalysisInput
    findings: list[Finding]
    overall_risk: int = Field(ge=0, le=100)
    overall_severity: Severity
    summary: str
    analyzed_at: datetime


class ModuleInterface(ABC):
    """Base class for all analysis modules."""

    @abstractmethod
    def analyze(self, input: AnalysisInput) -> list[Finding]:
        """Analyze input and return findings."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Module display name."""
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        """Semver string."""
        ...
