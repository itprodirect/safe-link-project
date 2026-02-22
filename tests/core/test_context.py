"""Tests for shared runtime context and orchestrator URL preprocessing."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from lsh.core.context import url_context_for_input
from lsh.core.models import AnalysisInput, Finding, ModuleInterface
from lsh.core.orchestrator import AnalysisOrchestrator


class _ContextProbe(ModuleInterface):
    def __init__(self, recorder: Callable[[AnalysisInput], None]) -> None:
        self._recorder = recorder

    @property
    def name(self) -> str:
        return "probe"

    @property
    def version(self) -> str:
        return "0.0.0"

    def analyze(self, input: AnalysisInput) -> list[Finding]:
        self._recorder(input)
        return []


def test_orchestrator_builds_url_context_once(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    from lsh.core import context as context_module

    original = context_module._build_url_context

    def counted(raw: str) -> object:
        nonlocal calls
        calls += 1
        return original(raw)

    monkeypatch.setattr(context_module, "_build_url_context", counted)

    seen_context_ids: list[int] = []

    def record(input: AnalysisInput) -> None:
        ctx = url_context_for_input(input)
        assert ctx is not None
        seen_context_ids.append(id(ctx))

    orchestrator = AnalysisOrchestrator(modules=[_ContextProbe(record), _ContextProbe(record)])
    orchestrator.analyze(AnalysisInput(input_type="url", content="http://google.com:80@0x7f000001"))

    assert calls == 1
    assert len(seen_context_ids) == 2
    assert seen_context_ids[0] == seen_context_ids[1]


def test_url_context_exposes_raw_and_canonical_hosts_for_adversarial_input() -> None:
    analysis_input = AnalysisInput(input_type="url", content="http://google.com:80@0x7f000001")

    captured: list[tuple[str | None, str | None, str | None, str | None]] = []

    def record(input: AnalysisInput) -> None:
        ctx = url_context_for_input(input)
        assert ctx is not None
        captured.append(
            (
                ctx.hostname,
                ctx.registrable_domain,
                ctx.canonical_hostname,
                ctx.canonical_registrable_domain,
            )
        )

    orchestrator = AnalysisOrchestrator(modules=[_ContextProbe(record), _ContextProbe(record)])
    orchestrator.analyze(analysis_input)

    assert captured == [
        ("0x7f000001", "0x7f000001", "127.0.0.1", "127.0.0.1"),
        ("0x7f000001", "0x7f000001", "127.0.0.1", "127.0.0.1"),
    ]
