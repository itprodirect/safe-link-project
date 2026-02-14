# CLAUDE.md — Agent Context for Link Safety Hub

## Project Summary

Link Safety Hub (LSH) is a modular Python security toolbelt. Each module analyzes a specific threat vector (phishing links, spoofed emails, malicious QR codes, etc.) and produces structured findings with risk scores and plain-English explanations. Modules share a common core engine and can be used standalone via CLI or composed together.

## Tech Stack

- **Language:** Python 3.11+ (MVP), Go planned for hardened distribution later
- **Package manager:** pip with pyproject.toml (PEP 621)
- **CLI framework:** Click
- **Data models:** Pydantic v2
- **Testing:** pytest with fixtures in `tests/fixtures/`
- **Linting:** ruff
- **Type checking:** mypy (strict mode)
- **Formatting:** ruff format

## Key Architecture Decisions

1. **Every module implements `ModuleInterface`** (see `src/lsh/core/models.py`). This means every module has: `analyze(input) -> Finding`, where `Finding` contains a risk score (0-100), category, evidence list, and explanation text.

2. **Modules must be stateless.** No module stores state between calls. All configuration is passed in.

3. **The core scorer is the single source of truth for risk levels.** Modules produce raw findings; the scorer in `src/lsh/core/scorer.py` normalizes them to a 0-100 scale with severity labels.

4. **Family Mode (#9) is a presentation layer, not a separate analysis.** It takes any Finding and produces simplified output. It should never duplicate detection logic.

5. **No dynamic code execution.** Attachment triage (#6) does static analysis only. No sandboxing, no detonation. Flag and explain, never execute.

6. **Network calls are opt-in and safe.** Redirect expander (#2) uses HEAD requests only by default. Content snapshot (#4) fetches with no JS execution. All network modules have a `--dry-run` flag.

## Starting a Session

Before writing any code, read the last 2-3 entries in `SESSION_LOG.md` to understand:
- What was done in the last session
- What decisions were made and why
- What open questions exist
- What the planned next steps are

This is non-negotiable. Skipping this step leads to duplicated work, contradictory decisions, and wasted time.

## Development Commands

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Test
pytest -v
pytest tests/modules/test_homoglyph.py -v  # single module

# Lint + format
ruff check src/ tests/
ruff format src/ tests/

# Type check
mypy src/

# Run CLI
python -m lsh.adapters.cli check "https://example.com"
```

## File Conventions

- Module code: `src/lsh/modules/<module_name>/`
- Each module has: `__init__.py`, `analyzer.py`, `README.md`
- Test files mirror source: `tests/modules/test_<module_name>.py`
- Test fixtures (sample emails, URLs, QR images): `tests/fixtures/`
- All imports use the `lsh` package namespace

## Current Priority

Current checkpoint:
- Session 0 complete (repo green)
- Session 1 complete (Homoglyph / IDN detector)

Next build order:
1. Redirect chain expander (#2)
2. Email auth checker (#5)
3. QR decoder (#7)
4. Family mode explainer (#9)
5. Extract dedicated orchestrator from CLI wiring

## What NOT to Do

- Don't add FastAPI/web server yet — CLI first
- Don't add database dependencies — everything is stateless for now
- Don't use subprocess to call external tools — pure Python for MVP
- Don't implement sandboxing or dynamic analysis
- Don't store any user credentials or passwords in any form
- Don't make network calls without explicit user opt-in flags

## Module Interface Contract

```python
from abc import ABC, abstractmethod
from lsh.core.models import AnalysisInput, Finding

class ModuleInterface(ABC):
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
```

## Session Logging (REQUIRED)

**Every coding session must end with a session log entry.** Use the `/session-logger` skill or manually append to `SESSION_LOG.md` in the project root.

The skill lives at `.claude/skills/session-logger/SKILL.md`. Trigger it with "log this session" or "end session".

Every entry must include:
- Which agent was used (Claude Code, Codex, Manual, Claude.ai)
- Which module(s) were touched
- All decisions with reasoning (not just "what" but "why")
- Open questions that carry forward

**Do not skip this.** The log is how different agents and sessions maintain continuity. If you're starting a session, read the last 2-3 entries in `SESSION_LOG.md` first to understand current state.

## Testing Philosophy

- Every module gets at least 5 test cases: 2 known-bad, 2 known-good, 1 edge case
- Use real-world phishing examples (sanitized) in fixtures when possible
- Network-dependent tests are marked `@pytest.mark.network` and skipped by default
- Aim for >90% coverage on core engine, >80% on modules

## Agent Collaboration Notes

This repo is developed with Claude Code, OpenAI Codex, and manual coding. Each agent has a different sweet spot:

### Two-Loop Workflow

**Loop A — "Make it pass" (Codex / fast agents):** Use for scaffolding files, straightforward implementations, repetitive test cases, and fixture creation. Definition of done: `make check` passes and one small feature works end-to-end from CLI.

**Loop B — "Make it correct" (Claude Code / thinking agents):** Use for architecture decisions, interface design, scoring semantics, module boundary questions, Unicode/punycode edge cases, and threat modeling. The rule: Claude decides the contract, Codex fills in the code.

### Per-Session Rules

- When adding a new module, always create the module directory, `analyzer.py`, `__init__.py`, `README.md`, and corresponding test file in one pass
- Prefer small, focused commits: one module or one feature per commit
- Always run `ruff check` and `pytest` before suggesting a commit
- **Definition of done for EVERY session:** `make check` passes AND `SESSION_LOG.md` has a new entry. No exceptions.
