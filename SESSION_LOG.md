# Session Log — Link Safety Hub

Development session history. Each entry documents what was done, why, and what's next. See `.claude/skills/session-logger/SKILL.md` for the logging format and conventions.

---

## 2026-02-13 — Project scaffold and documentation

**Agent:** Claude.ai

**Goal:** Create the initial project documentation, architecture, and GitHub strategy from ChatGPT's modular security hub plan

**Module(s) Touched:** docs

**Changes:**
- Created `README.md` — project overview, module table, quick start, project structure
- Created `CLAUDE.md` — agent context for Claude Code and Codex sessions
- Created `docs/ARCHITECTURE.md` — core engine, module contract, orchestrator, adapter pattern
- Created `docs/GITHUB_STRATEGY.md` — monorepo rationale, branch strategy, CI/CD, agent workflow tips
- Created `docs/ROADMAP.md` — phased build plan with realistic time estimates
- Created `docs/MODULES.md` — detailed specs for all 10 modules
- Created `docs/SECURITY.md` — responsible use guidelines, safe analysis practices
- Created `docs/PLAN_REVIEW.md` — gaps, corrections, and missing items from ChatGPT plan
- Created `pyproject.toml` — PEP 621 project config with optional dependency groups
- Created `Makefile` — dev commands (test, lint, typecheck, format)
- Created `.gitignore` — Python, IDE, and sensitive data patterns
- Created `.github/workflows/ci.yml` — GitHub Actions pipeline
- Created `.github/ISSUE_TEMPLATE/module-proposal.md`
- Integrated session-logger skill at `.claude/skills/session-logger/`

**Decisions:**
- Monorepo over multi-repo — because shared core engine creates cross-repo dependency hell, and agents work better with full project context
- Swapped #10 (Inbox Scanner) for #9 (Family Mode) in Phase 1 — because Family Mode makes every module useful to non-technical users immediately, and #10 is the most complex module
- Max-score-wins for aggregate risk scoring — because it's simplest to explain and conservative by default
- Python first, Go in the parking lot — because Docker solves distribution without a rewrite, and Python's library ecosystem for email/HTTP/QR is vastly richer

**Open Questions:**
- Should severity bands (0-20 INFO, etc.) be configurable per-deployment?
- How to handle false positives for legitimate international domains in homoglyph detection?
- What's the right threshold for "suspicious" domain age in the Domain Risk Profiler?
- Should the session logger also capture token/cost metrics when using AI agents?

**Next:**
- Initialize the actual repo on GitHub with this scaffold
- Build core engine: `models.py`, `scorer.py`, `rules.py`
- Build first module: Homoglyph / IDN Detector (#1)
- Set up the Python package structure with `src/lsh/` namespace

**Tests:** N/A — documentation only session

---

## 2026-02-13 — ChatGPT cross-review integration and final doc updates

**Agent:** Claude.ai

**Goal:** Incorporate ChatGPT's review feedback into all project docs before first real coding session

**Module(s) Touched:** docs

**Changes:**
- Fixed `pyproject.toml` — flattened self-referential extras (`phase1 = ["link-safety-hub[...]"]`) to direct dependency list in `[dev]` to avoid editable install breakage
- Updated `docs/ROADMAP.md` — added Session 0/1/2 quickstart plan with specific goals and definitions of done for each session
- Updated `CLAUDE.md` — added two-loop agent workflow (Codex for code, Claude Code for decisions) and per-session definition of done rule
- Updated `docs/PLAN_REVIEW.md` — added new correction #1 about docs-perfect-but-CI-fails gap, renumbered remaining items, noted pyproject.toml fix
- Updated `docs/GITHUB_STRATEGY.md` — expanded agent workflow tips from 4 to 7 items, added session logging as commit convention
- Created `.claude/skills/session-0-green-ci/SKILL.md` — ready-to-use prompt for the first Claude Code session to bootstrap the package skeleton

**Decisions:**
- Kept `.claude/skills/` for skill location (not `skills/` at root) — because `.claude/skills/` is the correct discovery path for Claude Code's skill system
- Kept `SESSION_LOG.md` at project root (not `docs/log.md`) — because root-level visibility is more important than tidy docs folder
- Adopted ChatGPT's two-loop workflow — because the distinction between "make it pass" (Codex) and "make it correct" (Claude Code) matches how these tools actually perform
- Did NOT adopt ChatGPT's copy-paste prompt as a text block — instead created it as a proper Claude Code skill at `.claude/skills/session-0-green-ci/SKILL.md` so it integrates with the skill system

**Open Questions:**
- Should we add more session-N skills for Sessions 1 and 2, or is that over-engineering the workflow?
- ChatGPT mentions Codex 5.3 xhigh — need to verify that's the right model string and available
- Should the session logger skill auto-commit its entry, or leave that to the developer?

**Next:**
- Push this scaffold to GitHub as initial commit
- Run Session 0: `/session-0-green-ci` in Claude Code to bootstrap the package skeleton
- Get `make check` green before touching any module code

**Tests:** N/A — documentation only session

---

## 2026-02-13 — Session 0: Get the repo green

**Agent:** Claude Code (Claude Opus 4.6)

**Goal:** Bootstrap the Python package skeleton so `pip install -e ".[dev]"`, ruff, mypy, and pytest all pass — and the CLI runs

**Module(s) Touched:** core, adapters (stubs only)

**Changes:**
- Created `src/lsh/core/__init__.py` — core engine package
- Created `src/lsh/core/models.py` — Pydantic v2 models: `Severity` (StrEnum), `AnalysisInput`, `Evidence`, `Finding`, `AnalysisResult`, `ModuleInterface` (ABC)
- Created `src/lsh/core/scorer.py` — `score_to_severity()` maps 0-100 to severity bands, `normalize()` aligns finding severity to risk_score
- Created `src/lsh/core/rules.py` — empty placeholder with `__all__ = []`
- Created `src/lsh/modules/__init__.py` — modules package placeholder
- Created `src/lsh/adapters/__init__.py` — adapters package placeholder
- Created `src/lsh/adapters/cli.py` — Click CLI with `lsh --help` and `lsh check <url>` (stub returning 0/100 INFO)
- Created `src/lsh/adapters/__main__.py` — enables `python -m lsh.adapters` invocation
- Created `src/lsh/py.typed` — PEP 561 marker for typed package
- Updated `src/lsh/__init__.py` — added package docstring
- Created `tests/__init__.py` and `tests/test_smoke.py` — 10 smoke tests covering CLI, models, scorer
- Updated `pyproject.toml` — added `mypy_path = "src"` and `plugins = ["pydantic.mypy"]` for correct src-layout type checking

**Decisions:**
- Used `StrEnum` instead of `str, Enum` — ruff UP042 requires it for Python 3.11+, and it's the modern pattern
- Used `datetime.UTC` instead of `timezone.utc` — ruff UP017 requires the alias for Python 3.11+
- Added `pydantic.mypy` plugin — ensures mypy understands Pydantic model fields correctly under strict mode
- Added `mypy_path = "src"` — required for mypy to resolve `lsh` imports with src-layout when running `mypy .`
- Used `Field(ge=0, le=100)` for risk_score/overall_risk — runtime validation of score bounds even in stub phase
- Kept mutable defaults (`= {}`, `= []`) on Pydantic models instead of `Field(default_factory=...)` — Pydantic v2 handles these correctly and it's simpler
- Created `__main__.py` for adapters — CLAUDE.md references `python -m lsh.adapters.cli` invocation pattern

**Open Questions:**
- Should severity bands (0-20 INFO, etc.) be configurable per-deployment? (carried forward)
- How to handle false positives for legitimate international domains in homoglyph detection? (carried forward)
- Windows terminal shows mojibake for em-dash in CLI output — cosmetic only, may need `rich` integration to fix

**Next:**
- Session 1: Build the Homoglyph / IDN Detector module (#1)
- Wire up the first real module through the orchestrator
- Add real test fixtures with known-bad homoglyph URLs

**Tests:** 10 passed — CLI help, CLI check (text + JSON), model validation (AnalysisInput, Finding, Evidence, AnalysisResult), scorer normalize (empty, severity correction, all severity bands)

---

## 2026-02-13 21:05 - Session 1: Homoglyph / IDN detector

**Agent:** Codex

**Goal:** Implement an offline Homoglyph / IDN detector module, wire it into CLI analysis, add focused tests, and keep checks green on Windows

**Module(s) Touched:** homoglyph, adapter:cli

**Changes:**
- Created `src/lsh/modules/homoglyph/analyzer.py` - implemented hostname extraction, non-ASCII detection, IDNA/punycode visibility, mixed-script label detection, confusable detection, and coded findings with evidence
- Created `src/lsh/modules/homoglyph/__init__.py` and `src/lsh/modules/homoglyph/README.md`
- Updated `src/lsh/modules/__init__.py` - exports `HomoglyphDetector`
- Replaced CLI stub flow in `src/lsh/adapters/cli.py` - now runs URL modules, normalizes findings, computes aggregate risk, prints coded findings, and adds family-friendly actionable guidance
- Added `tests/modules/test_homoglyph.py` - focused tests for clean ASCII, Unicode hostname, mixed scripts, and punycode input

**Decisions:**
- Emitted one finding per signal (`HMG001`-`HMG004`) with cumulative scoring evidence (`Risk Delta`, `Cumulative Risk`) - because incremental risk is easier to explain and audit than opaque single-score output
- Performed mixed-script detection per-label instead of across the full hostname - because cross-label checks create false positives on normal ASCII TLDs (for example `.com`)
- Kept analysis fully offline with `urllib.parse`, stdlib IDNA codec, and local `confusables` data only - because Session 1 requirements explicitly disallow network use

**Open Questions:**
- Should we add allow-list controls for legitimate internationalized domains to reduce false positives for bilingual brands?
- Should CLI expose a `--family` mode that suppresses technical finding rows and prints only plain-language actions?

**Next:**
- Start Session 2 redirect-chain module and pass final destination hostnames into this detector
- Add fixture-driven homoglyph regression cases (known-good international domains vs known-bad lookalikes)
- Consider moving module orchestration from CLI into a dedicated orchestrator component

**Tests:** Passing - `ruff check src tests`, `mypy src`, and `pytest -v --tb=short` (14 tests)
<<<<<<< HEAD

## Session Wrap — 2026-02-13/14

### Outcome
- Session 0: Repo turns green. CLI + typed core + smoke tests established.
- Session 1: Homoglyph/IDN detector implemented end-to-end and wired into CLI.
- Verified CLI + JSON outputs against a known homoglyph example (Cyrillic “і” in logіn.com).

### Validation
- ruff: pass
- mypy: pass
- pytest: pass (14 tests)

### Key Decisions (with why)
- Windows environment lacks `make`; local gate is:
  - `python -m ruff check .`
  - `python -m mypy .`
  - `python -m pytest -q`
- Keep network actions opt-in only; default analysis is offline.
- Findings include family-friendly explanations + actionable recommendations.

### Notable Deliverables
- New module: `src/lsh/modules/homoglyph/`
- New tests: `tests/modules/test_homoglyph.py`
- CLI improvements: actionable summary + “What to do next”
- Session logs updated continuously

### Next Session Plan
1) Session 2: Redirect chain expander module
   - CLI flag: `--follow` (opt-in)
   - strict timeouts + max hops + HEAD-first
   - network tests marked/skipped by default
2) CLI polish
   - “Key details” section (shown hostname / punycode / ASCII lookalike)
   - `--explain` flag for full evidence output
3) Prevent recommendation duplication as modules scale (top-3 aggregated guidance)

### Open Questions / Risks
- `pyzbar` may require zbar DLL on Windows; keep QR support optional and not on critical path.

||||||| parent of e430ae0 (docs: sync Session 1 status and Session 2 handoff docs)
=======

---

## 2026-02-13 21:26 - Docs sync for Session 2 handoff

**Agent:** Codex

**Goal:** Align project documentation with current implementation state and prepare clear next-session guidance

**Module(s) Touched:** docs

**Changes:**
- Rewrote `README.md` to reflect current implemented scope (`lsh check`, Homoglyph module) and explicitly mark unimplemented commands as planned
- Rewrote `docs/ROADMAP.md` with completed Session 0/1 checkpoint and concrete Session 2 scope/definition of done
- Rewrote `docs/MODULES.md` to document implemented Homoglyph detector behavior and finding codes (`HMG000`-`HMG004`)
- Rewrote `docs/ARCHITECTURE.md` to distinguish current architecture from target orchestrator architecture
- Updated `CLAUDE.md` current-priority section to reflect Session 1 completion and Session 2 ordering
- Updated `docs/PLAN_REVIEW.md` to mark the CI scaffold gap as resolved and add a status note

**Decisions:**
- Kept docs explicit about implemented vs planned capabilities - because stale command examples caused ambiguity for next-session execution
- Prioritized concise, operational handoff language over broad aspirational text - because the immediate need is Session 2 implementation clarity

**Open Questions:**
- Should we add a dedicated `docs/NEXT_SESSION.md` checklist, or keep handoff guidance centralized in `docs/ROADMAP.md` + `SESSION_LOG.md`?

**Next:**
- Begin Session 2 redirect module scaffold and CLI flag design
- Add redirect-focused test plan with mocked chains and timeout coverage

**Tests:** N/A - docs-only session
>>>>>>> e430ae0 (docs: sync Session 1 status and Session 2 handoff docs)
