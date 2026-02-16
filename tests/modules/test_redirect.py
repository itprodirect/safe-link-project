"""Focused tests for redirect-chain analysis with mocked network responses."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pytest
import requests  # type: ignore[import-untyped]

from lsh.core.models import AnalysisInput, Finding
from lsh.modules.redirect import RedirectChainDetector


@dataclass(slots=True)
class _FakeResponse:
    status_code: int
    location: str | None = None

    @property
    def headers(self) -> dict[str, str]:
        if self.location is None:
            return {}
        return {"Location": self.location}


class _FakeSession:
    def __init__(
        self,
        responses: list[_FakeResponse] | None = None,
        *,
        error_factory: Callable[[], Exception] | None = None,
    ) -> None:
        self._responses = list(responses or [])
        self._error_factory = error_factory
        self.calls: list[tuple[str, bool, float, dict[str, str]]] = []

    def head(
        self,
        url: str,
        *,
        allow_redirects: bool,
        timeout: float,
        headers: dict[str, str],
    ) -> _FakeResponse:
        self.calls.append((url, allow_redirects, timeout, headers))
        if self._error_factory is not None:
            raise self._error_factory()
        if self._responses:
            return self._responses.pop(0)
        return _FakeResponse(200)

    def close(self) -> None:
        return None


def _code_map(findings: list[Finding]) -> dict[str, Finding]:
    return {finding.category: finding for finding in findings}


def _network_input(url: str, *, max_hops: int = 5, timeout: float = 1.0) -> AnalysisInput:
    return AnalysisInput(
        input_type="url",
        content=url,
        metadata={
            "network_enabled": True,
            "network_max_hops": max_hops,
            "network_timeout": timeout,
        },
    )


def test_redirect_network_disabled_skips_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    def _forbidden_session() -> _FakeSession:
        raise AssertionError("network session should not be created when --network is disabled")

    monkeypatch.setattr("lsh.modules.redirect.analyzer.requests.Session", _forbidden_session)
    detector = RedirectChainDetector()
    findings = detector.analyze(AnalysisInput(input_type="url", content="https://example.com"))
    assert findings == []


def test_redirect_string_false_does_not_enable_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _forbidden_session() -> _FakeSession:
        raise AssertionError("network session should not be created for string false")

    monkeypatch.setattr("lsh.modules.redirect.analyzer.requests.Session", _forbidden_session)
    detector = RedirectChainDetector()
    findings = detector.analyze(
        AnalysisInput(
            input_type="url",
            content="https://example.com",
            metadata={"network_enabled": "false"},
        )
    )
    assert findings == []


def test_redirect_chain_and_cross_domain_are_detected(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_session = _FakeSession(
        [
            _FakeResponse(302, "/step1"),
            _FakeResponse(302, "https://evil.com/login"),
            _FakeResponse(200),
        ]
    )
    monkeypatch.setattr("lsh.modules.redirect.analyzer.requests.Session", lambda: fake_session)

    detector = RedirectChainDetector()
    findings = detector.analyze(_network_input("https://example.com/start"))
    mapped = _code_map(findings)

    assert "RED001_REDIRECT_CHAIN_PRESENT" in mapped
    assert "RED002_CROSS_DOMAIN_REDIRECT" in mapped
    assert len(fake_session.calls) == 3
    assert all(not call[1] for call in fake_session.calls)
    assert any(
        evidence.label == "Domain Path"
        and "example.com" in evidence.value
        and "evil.com" in evidence.value
        for evidence in mapped["RED002_CROSS_DOMAIN_REDIRECT"].evidence
    )


def test_redirect_max_hops_limit_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_session = _FakeSession(
        [
            _FakeResponse(302, "/a"),
            _FakeResponse(302, "/b"),
            _FakeResponse(302, "/c"),
        ]
    )
    monkeypatch.setattr("lsh.modules.redirect.analyzer.requests.Session", lambda: fake_session)

    detector = RedirectChainDetector()
    findings = detector.analyze(_network_input("https://example.com/start", max_hops=2))
    mapped = _code_map(findings)
    assert "RED001_REDIRECT_CHAIN_PRESENT" in mapped
    assert "RED003_MAX_HOPS_REACHED" in mapped


def test_redirect_timeout_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_session = _FakeSession(error_factory=lambda: requests.Timeout("timed out"))
    monkeypatch.setattr("lsh.modules.redirect.analyzer.requests.Session", lambda: fake_session)

    detector = RedirectChainDetector()
    findings = detector.analyze(_network_input("https://example.com"))
    assert "RED005_REQUEST_TIMEOUT" in _code_map(findings)


def test_redirect_requires_explicit_http_or_https_url() -> None:
    detector = RedirectChainDetector()
    findings = detector.analyze(_network_input("example.com"))
    assert "RED000_NETWORK_URL_REQUIRED" in _code_map(findings)
