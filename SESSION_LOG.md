# Session Log â€” Link Safety Hub

Development session history. Each entry documents what was done, why, and what's next. See `.claude/skills/session-logger/SKILL.md` for the logging format and conventions.

---

## 2026-02-13 â€” Project scaffold and documentation

**Agent:** Claude.ai

**Goal:** Create the initial project documentation, architecture, and GitHub strategy from ChatGPT's modular security hub plan

**Module(s) Touched:** docs

**Changes:**
- Created `README.md` â€” project overview, module table, quick start, project structure
- Created `CLAUDE.md` â€” agent context for Claude Code and Codex sessions
- Created `docs/ARCHITECTURE.md` â€” core engine, module contract, orchestrator, adapter pattern
- Created `docs/GITHUB_STRATEGY.md` â€” monorepo rationale, branch strategy, CI/CD, agent workflow tips
- Created `docs/ROADMAP.md` â€” phased build plan with realistic time estimates
- Created `docs/MODULES.md` â€” detailed specs for all 10 modules
- Created `docs/SECURITY.md` â€” responsible use guidelines, safe analysis practices
- Created `docs/PLAN_REVIEW.md` â€” gaps, corrections, and missing items from ChatGPT plan
- Created `pyproject.toml` â€” PEP 621 project config with optional dependency groups
- Created `Makefile` â€” dev commands (test, lint, typecheck, format)
- Created `.gitignore` â€” Python, IDE, and sensitive data patterns
- Created `.github/workflows/ci.yml` â€” GitHub Actions pipeline
- Created `.github/ISSUE_TEMPLATE/module-proposal.md`
- Integrated session-logger skill at `.claude/skills/session-logger/`

**Decisions:**
- Monorepo over multi-repo â€” because shared core engine creates cross-repo dependency hell, and agents work better with full project context
- Swapped #10 (Inbox Scanner) for #9 (Family Mode) in Phase 1 â€” because Family Mode makes every module useful to non-technical users immediately, and #10 is the most complex module
- Max-score-wins for aggregate risk scoring â€” because it's simplest to explain and conservative by default
- Python first, Go in the parking lot â€” because Docker solves distribution without a rewrite, and Python's library ecosystem for email/HTTP/QR is vastly richer

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

**Tests:** N/A â€” documentation only session

---

## 2026-02-13 â€” ChatGPT cross-review integration and final doc updates

**Agent:** Claude.ai

**Goal:** Incorporate ChatGPT's review feedback into all project docs before first real coding session

**Module(s) Touched:** docs

**Changes:**
- Fixed `pyproject.toml` â€” flattened self-referential extras (`phase1 = ["link-safety-hub[...]"]`) to direct dependency list in `[dev]` to avoid editable install breakage
- Updated `docs/ROADMAP.md` â€” added Session 0/1/2 quickstart plan with specific goals and definitions of done for each session
- Updated `CLAUDE.md` â€” added two-loop agent workflow (Codex for code, Claude Code for decisions) and per-session definition of done rule
- Updated `docs/PLAN_REVIEW.md` â€” added new correction #1 about docs-perfect-but-CI-fails gap, renumbered remaining items, noted pyproject.toml fix
- Updated `docs/GITHUB_STRATEGY.md` â€” expanded agent workflow tips from 4 to 7 items, added session logging as commit convention
- Created `.claude/skills/session-0-green-ci/SKILL.md` â€” ready-to-use prompt for the first Claude Code session to bootstrap the package skeleton

**Decisions:**
- Kept `.claude/skills/` for skill location (not `skills/` at root) â€” because `.claude/skills/` is the correct discovery path for Claude Code's skill system
- Kept `SESSION_LOG.md` at project root (not `docs/log.md`) â€” because root-level visibility is more important than tidy docs folder
- Adopted ChatGPT's two-loop workflow â€” because the distinction between "make it pass" (Codex) and "make it correct" (Claude Code) matches how these tools actually perform
- Did NOT adopt ChatGPT's copy-paste prompt as a text block â€” instead created it as a proper Claude Code skill at `.claude/skills/session-0-green-ci/SKILL.md` so it integrates with the skill system

**Open Questions:**
- Should we add more session-N skills for Sessions 1 and 2, or is that over-engineering the workflow?
- ChatGPT mentions Codex 5.3 xhigh â€” need to verify that's the right model string and available
- Should the session logger skill auto-commit its entry, or leave that to the developer?

**Next:**
- Push this scaffold to GitHub as initial commit
- Run Session 0: `/session-0-green-ci` in Claude Code to bootstrap the package skeleton
- Get `make check` green before touching any module code

**Tests:** N/A â€” documentation only session

---

## 2026-02-13 â€” Session 0: Get the repo green

**Agent:** Claude Code (Claude Opus 4.6)

**Goal:** Bootstrap the Python package skeleton so `pip install -e ".[dev]"`, ruff, mypy, and pytest all pass â€” and the CLI runs

**Module(s) Touched:** core, adapters (stubs only)

**Changes:**
- Created `src/lsh/core/__init__.py` â€” core engine package
- Created `src/lsh/core/models.py` â€” Pydantic v2 models: `Severity` (StrEnum), `AnalysisInput`, `Evidence`, `Finding`, `AnalysisResult`, `ModuleInterface` (ABC)
- Created `src/lsh/core/scorer.py` â€” `score_to_severity()` maps 0-100 to severity bands, `normalize()` aligns finding severity to risk_score
- Created `src/lsh/core/rules.py` â€” empty placeholder with `__all__ = []`
- Created `src/lsh/modules/__init__.py` â€” modules package placeholder
- Created `src/lsh/adapters/__init__.py` â€” adapters package placeholder
- Created `src/lsh/adapters/cli.py` â€” Click CLI with `lsh --help` and `lsh check <url>` (stub returning 0/100 INFO)
- Created `src/lsh/adapters/__main__.py` â€” enables `python -m lsh.adapters` invocation
- Created `src/lsh/py.typed` â€” PEP 561 marker for typed package
- Updated `src/lsh/__init__.py` â€” added package docstring
- Created `tests/__init__.py` and `tests/test_smoke.py` â€” 10 smoke tests covering CLI, models, scorer
- Updated `pyproject.toml` â€” added `mypy_path = "src"` and `plugins = ["pydantic.mypy"]` for correct src-layout type checking

**Decisions:**
- Used `StrEnum` instead of `str, Enum` â€” ruff UP042 requires it for Python 3.11+, and it's the modern pattern
- Used `datetime.UTC` instead of `timezone.utc` â€” ruff UP017 requires the alias for Python 3.11+
- Added `pydantic.mypy` plugin â€” ensures mypy understands Pydantic model fields correctly under strict mode
- Added `mypy_path = "src"` â€” required for mypy to resolve `lsh` imports with src-layout when running `mypy .`
- Used `Field(ge=0, le=100)` for risk_score/overall_risk â€” runtime validation of score bounds even in stub phase
- Kept mutable defaults (`= {}`, `= []`) on Pydantic models instead of `Field(default_factory=...)` â€” Pydantic v2 handles these correctly and it's simpler
- Created `__main__.py` for adapters â€” CLAUDE.md references `python -m lsh.adapters.cli` invocation pattern

**Open Questions:**
- Should severity bands (0-20 INFO, etc.) be configurable per-deployment? (carried forward)
- How to handle false positives for legitimate international domains in homoglyph detection? (carried forward)
- Windows terminal shows mojibake for em-dash in CLI output â€” cosmetic only, may need `rich` integration to fix

**Next:**
- Session 1: Build the Homoglyph / IDN Detector module (#1)
- Wire up the first real module through the orchestrator
- Add real test fixtures with known-bad homoglyph URLs

**Tests:** 10 passed â€” CLI help, CLI check (text + JSON), model validation (AnalysisInput, Finding, Evidence, AnalysisResult), scorer normalize (empty, severity correction, all severity bands)

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

## Session Wrap â€” 2026-02-13/14

### Outcome
- Session 0: Repo turns green. CLI + typed core + smoke tests established.
- Session 1: Homoglyph/IDN detector implemented end-to-end and wired into CLI.
- Verified CLI + JSON outputs against a known homoglyph example (Cyrillic â€œÑ–â€ in logÑ–n.com).

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
- CLI improvements: actionable summary + â€œWhat to do nextâ€
- Session logs updated continuously

### Next Session Plan
1) Session 2: Redirect chain expander module
   - CLI flag: `--follow` (opt-in)
   - strict timeouts + max hops + HEAD-first
   - network tests marked/skipped by default
2) CLI polish
   - â€œKey detailsâ€ section (shown hostname / punycode / ASCII lookalike)
   - `--explain` flag for full evidence output
3) Prevent recommendation duplication as modules scale (top-3 aggregated guidance)

### Open Questions / Risks
- `pyzbar` may require zbar DLL on Windows; keep QR support optional and not on critical path.


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

---

## 2026-02-16 09:40 - Orchestrator refactor, family UX improvements, and documentation sync

**Agent:** Codex

**Goal:** Make substantial forward progress by extracting orchestration from CLI, improving user-facing CLI UX, tightening quality checks, and fully syncing project documentation/process files

**Module(s) Touched:** core, adapters:cli, docs/process

**Changes:**
- Added `src/lsh/core/orchestrator.py` with `AnalysisOrchestrator` and shared `build_summary()`
- Updated `src/lsh/adapters/cli.py` to use orchestrator instead of module execution/scoring inline
- Added `--family` output mode for plain-language CLI rendering
- Added dedicated CLI render helpers for technical and family views
- Updated `src/lsh/core/models.py` to use `Field(default_factory=...)` for list/dict defaults
- Updated `src/lsh/core/__init__.py` exports
- Added `tests/core/test_orchestrator.py` for aggregate behavior and custom summary hook
- Expanded `tests/test_smoke.py` for technical and family-mode CLI coverage
- Tightened typing in `tests/modules/test_homoglyph.py`
- Rewrote and synchronized markdown docs across root and `docs/`:
  - `README.md`
  - `CLAUDE.md`
  - `ROADMAP.md`
  - `PLAN_REVIEW.md`
  - `SKILL.md`
  - `docs/ARCHITECTURE.md`
  - `docs/MODULES.md`
  - `docs/ROADMAP.md`
  - `docs/PLAN_REVIEW.md`
  - `docs/GITHUB_STRATEGY.md`
  - `docs/SECURITY.md`
  - `src/lsh/modules/homoglyph/README.md`

**Decisions:**
- Extracted orchestration into core now (before adding redirect module) because continuing to grow CLI-local orchestration would increase coupling and make future modules harder to add safely.
- Added family output mode now because user-facing clarity is part of product value, and the existing summary/recommendation model already supported this with low implementation risk.
- Included `mypy src tests` in validation during this session to catch strict-typing drift early, even though legacy docs mostly referenced `mypy src`.
- Rewrote stale markdown docs as part of this same session because code and process docs were diverging, and that creates immediate onboarding and execution risk.

**Open Questions:**
- Should `--family` and `--json` be mutually exclusive by design, or should family formatting metadata also be represented in JSON output?
- Should allowlist/false-positive controls be implemented before redirect module, or after redirect module lands?
- Do you want root docs and `docs/` to remain mirrored, or should one become canonical and the other reduced to pointers?

**Next:**
- Session 2B: implement redirect module with strict opt-in network behavior (`--network`, hop cap, timeout)
- Add dependency vulnerability scanning (`pip-audit`) to local and CI checks
- Introduce first-pass false-positive controls for homoglyph findings (allowlist or confidence labels)

**Tests:**
- `ruff check src tests` passed
- `mypy src tests` passed
- `pytest -q` passed (19 tests)

---

## 2026-02-16 10:40 - Offline URL trust-signal expansion (ASCII, URL structure, IP)

**Agent:** Codex

**Goal:** Improve perceived correctness and user trust for common link tricks while staying offline and conservative on false positives.

**Module(s) Touched:** core, adapters:cli, modules:homoglyph/ascii_lookalike/url_structure/net_ip, docs

**Changes:**
- Added shared URL/IP helpers in `src/lsh/core/url_tools.py`:
  - robust URL-like parsing (`parse_url_like`)
  - hostname extraction/normalization
  - IP literal parsing
  - lightweight registrable-domain heuristic
- Expanded shared detection constants in `src/lsh/core/rules.py`:
  - brand token set
  - deceptive prefix hints
  - nested URL parameter keys
  - ASCII ambiguous/leet mappings
- Added module `src/lsh/modules/url_structure/`:
  - `URL001_USERINFO_PRESENT`
  - `URL002_DECEPTIVE_SUBDOMAIN`
  - `URL003_NESTED_URL_PARAMETER`
- Added module `src/lsh/modules/net_ip/`:
  - `NET001_PRIVATE_IP_LITERAL`
  - `NET002_PUBLIC_IP_LITERAL`
- Added module `src/lsh/modules/ascii_lookalike/`:
  - `ASCII001_AMBIGUOUS_GLYPHS`
  - `ASCII002_LEET_SUBSTITUTION`
- Updated `src/lsh/modules/homoglyph/analyzer.py`:
  - skip IP literals
  - only emit `HMG004_CONFUSABLE_CHARACTERS` for non-ASCII hostnames
- Updated module wiring:
  - `src/lsh/modules/__init__.py`
  - `src/lsh/adapters/cli.py` orchestrator now runs `net_ip`, `url_structure`, `ascii_lookalike`, `homoglyph`
- Added console-safe URL rendering in CLI to avoid Windows codepage crashes on Unicode input
- Added/expanded tests:
  - `tests/modules/test_url_structure.py`
  - `tests/modules/test_net_ip.py`
  - `tests/modules/test_ascii_lookalike.py`
  - `tests/core/test_url_stack.py`
  - updated `tests/modules/test_homoglyph.py`
- Updated docs:
  - `README.md`
  - `docs/MODULES.md`
  - `docs/ARCHITECTURE.md`
  - `docs/ROADMAP.md`
  - `docs/PLAN_REVIEW.md`
  - `PLAN_REVIEW.md`
  - `ROADMAP.md`
  - `src/lsh/modules/homoglyph/README.md`

**Decisions:**
- Chose lightweight offline registrable-domain heuristics instead of adding `tldextract` now.
  - Why: lower dependency/maintenance cost, no PSL update complexity, sufficient accuracy for high-signal initial patterns.
  - Tradeoff: imperfect handling for some country-code edge cases; documented and acceptable for this phase.
- Kept risk levels conservative for new detectors (mostly LOW/MEDIUM) to reduce user alarm fatigue.
- Scoped ASCII lookalike detection to brand-like token matches (not all ambiguous ASCII strings) to reduce false positives.
- Separated IP literal logic into dedicated `NET*` findings and removed misleading homoglyph behavior on IP hosts.

**Open Questions:**
- Should we add optional `tldextract`/PSL-backed parsing behind a feature flag for higher registrable-domain accuracy?
- Should ASCII lookalike detection support user-configurable brand token sets?
- Should summary text become category-aware (e.g., mention URL-structure tricks explicitly) instead of only risk-band text?

**Next:**
- Session 3: redirect-chain expander with strict opt-in network path and timeout/hop guards
- Add allowlist/confidence controls for false-positive management
- Consider CI dependency audit (`pip-audit`)

**Tests:**
- `ruff check src tests` passed
- `mypy src tests` passed
- `pytest -q` passed (30 tests)

## 2026-02-16 11:15 - P1 start: confidence labels and domain allowlist controls

**Agent:** Codex

**Goal:** Start P1 false-positive management by adding confidence labels and a practical allowlist path without changing offline architecture.

**Module(s) Touched:** core, adapters:cli, modules:homoglyph/ascii_lookalike, docs

**Changes:**
- Added `Confidence` enum and `confidence` field on `Finding` in `src/lsh/core/models.py`
- Added `src/lsh/core/allowlist.py` for normalized domain allowlist handling (supports URL/domain inputs and IDNA forms)
- Added CLI option `--allowlist-domain` and metadata wiring in `src/lsh/adapters/cli.py`
- Updated technical CLI rendering to include finding confidence (`confidence=...`)
- Applied allowlist suppression to:
  - `src/lsh/modules/homoglyph/analyzer.py`
  - `src/lsh/modules/ascii_lookalike/analyzer.py`
- Set confidence levels across modules:
  - URL structure, ASCII, NET, HMG findings
- Added tests:
  - `tests/modules/test_homoglyph.py` allowlist coverage
  - `tests/modules/test_ascii_lookalike.py` allowlist coverage
  - `tests/test_smoke.py` CLI allowlist + confidence rendering coverage
- Updated docs:
  - `README.md`
  - `docs/MODULES.md`
  - `docs/ARCHITECTURE.md`
  - `ROADMAP.md`
  - `docs/ROADMAP.md`
  - `PLAN_REVIEW.md`
  - `docs/PLAN_REVIEW.md`

**Decisions:**
- Implemented allowlist as metadata-driven domain suppression first (rather than global config files) because it keeps behavior explicit per invocation and easy to test.
- Scoped allowlist suppression initially to domain-lookalike detectors (`HMG*`, `ASCII*`) to avoid hiding structural/network signals that may still matter.
- Added confidence labels now to improve trust calibration without changing risk-band scoring semantics.

**Open Questions:**
- Should allowlist scope be configurable per finding category/module?
- Should we expose allowlist from file path (`--allowlist-file`) for team workflows?
- Should summary text include confidence-aware phrasing when high-risk findings are low confidence?

**Next:**
- Continue P1 with confidence calibration docs/examples and allowlist granularity controls.
- Begin Session 3 redirect module once P1 core controls settle.

**Tests:**
- `ruff check src tests` passed
- `mypy src tests` passed
- `pytest -q` passed (33 tests)

## 2026-02-16 11:55 - P1 continuation: scoped allowlists, allowlist files, and confidence-aware family summaries

**Agent:** Codex

**Goal:** Implement all remaining P1 suggestions: per-category allowlist control, allowlist file support, and confidence-aware family summary behavior.

**Module(s) Touched:** core, adapters:cli, modules, docs

**Changes:**
- Expanded allowlist engine in `src/lsh/core/allowlist.py`:
  - category-prefix support (`HMG`, `ASCII`, `URL`, `NET`, `ALL`)
  - default suppression scope (`HMG` + `ASCII`)
  - `should_suppress_for_allowlist(...)` helper
- Updated modules to use scoped allowlist suppression:
  - `src/lsh/modules/homoglyph/analyzer.py`
  - `src/lsh/modules/ascii_lookalike/analyzer.py`
  - `src/lsh/modules/url_structure/analyzer.py`
  - `src/lsh/modules/net_ip/analyzer.py`
- Enhanced CLI in `src/lsh/adapters/cli.py`:
  - added `--allowlist-file` (repeatable)
  - added `--allowlist-category` (repeatable)
  - improved allowlist file parsing (comments + UTF-8 BOM resilience)
  - JSON output now uses `ensure_ascii=True` for Windows codepage safety
  - family output now includes `Signal confidence`
- Added confidence-aware summary wording in `src/lsh/core/orchestrator.py` for low-confidence findings
- Added tests:
  - `tests/core/test_allowlist.py`
  - `tests/core/test_orchestrator.py` confidence-summary case
  - `tests/test_smoke.py` CLI scoped allowlist/file/Unicode JSON safety coverage
  - updated module tests remain green
- Updated docs:
  - `README.md`
  - `docs/MODULES.md`
  - `docs/ARCHITECTURE.md`
  - `ROADMAP.md`
  - `docs/ROADMAP.md`
  - `PLAN_REVIEW.md`
  - `docs/PLAN_REVIEW.md`
  - module READMEs under `src/lsh/modules/*/README.md`

**Decisions:**
- Kept default allowlist scope at `HMG` + `ASCII` so structural/network warnings are not silently hidden unless explicitly requested.
- Added `ALL` category escape hatch for advanced users/team workflows where broad suppression is intentional.
- Used ASCII-safe JSON output to avoid Windows terminal encoding crashes for Unicode-heavy outputs.

**Open Questions:**
- Should CLI persist allowlist profiles (for example per-user config file) instead of requiring repeated flags?
- Should summary confidence use only highest-confidence findings or risk-weighted confidence aggregation?
- Should we expose per-rule toggles beyond category prefixes for very fine-grained enterprise tuning?

**Next:**
- Session 3 redirect module (opt-in network path with hop/time limits)
- Optional: add `--allowlist-file` default path support via env var/config
- Optional: publish confidence calibration guidance in user docs with examples

**Tests:**
- `ruff check src tests` passed
- `mypy src tests` passed
- `pytest -q` passed (42 tests)
