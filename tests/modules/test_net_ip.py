"""Focused tests for IP literal URL host detection."""

from lsh.core.models import AnalysisInput
from lsh.modules.net_ip import NetIPDetector


def test_private_ip_literal_is_flagged() -> None:
    detector = NetIPDetector()
    findings = detector.analyze(AnalysisInput(input_type="url", content="http://127.0.0.1"))
    assert any(finding.category == "NET001_PRIVATE_IP_LITERAL" for finding in findings)


def test_public_ip_literal_is_flagged() -> None:
    detector = NetIPDetector()
    findings = detector.analyze(AnalysisInput(input_type="url", content="http://8.8.8.8"))
    assert any(finding.category == "NET002_PUBLIC_IP_LITERAL" for finding in findings)
