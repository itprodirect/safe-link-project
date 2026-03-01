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

## 2026-02-16 12:40 - Session 3: Redirect chain module + continued trust controls

**Agent:** Codex

**Goal:** Complete Session 3 with safe, opt-in redirect-chain analysis and continue quality/documentation updates in the same disciplined workflow.

**Module(s) Touched:** modules:redirect, adapters:cli, core, docs

**Changes:**
- Added new module `src/lsh/modules/redirect/`:
  - `analyzer.py`
  - `__init__.py`
  - `README.md`
- Implemented redirect findings:
  - `RED000_NETWORK_URL_REQUIRED`
  - `RED001_REDIRECT_CHAIN_PRESENT`
  - `RED002_CROSS_DOMAIN_REDIRECT`
  - `RED003_MAX_HOPS_REACHED`
  - `RED004_REDIRECT_LOOP_DETECTED`
  - `RED005_REQUEST_TIMEOUT`
  - `RED006_REQUEST_ERROR`
  - `RED007_NON_HTTP_REDIRECT_TARGET`
- Redirect safety model:
  - analysis runs only when `network_enabled=True`
  - HEAD-only requests
  - explicit hop and timeout controls
  - no body/content fetches for redirect analysis
- Updated CLI `check` command with network controls:
  - `--network`
  - `--max-hops`
  - `--timeout`
- Wired redirect module into URL orchestrator stack in `src/lsh/adapters/cli.py`
- Added redirect-focused tests with mocked network behavior:
  - `tests/modules/test_redirect.py`
  - cases: network-disabled skip, chain + cross-domain, max-hop reached, timeout, invalid URL in network mode
- Added/updated integration and smoke coverage:
  - `tests/core/test_url_stack.py` includes redirect module in stack
  - `tests/test_smoke.py` includes check-help coverage for new network flags
- Continued trust-control hardening from prior pass:
  - keep scoped allowlist/category/file behavior and confidence-aware summaries
  - ensure Unicode-safe JSON output on Windows console (`ensure_ascii=True`)
- Synced docs to new implemented state:
  - `README.md`
  - `CLAUDE.md`
  - `ROADMAP.md`
  - `PLAN_REVIEW.md`
  - `docs/ARCHITECTURE.md`
  - `docs/MODULES.md`
  - `docs/ROADMAP.md`
  - `docs/PLAN_REVIEW.md`

**Decisions:**
- Kept redirect checks opt-in and HEAD-only to respect offline-first posture and reduce side effects.
- Used conservative cumulative scoring for redirect findings to avoid over-alarming users on benign chains.
- Left `RED*` out of allowlist suppression intentionally in this phase to avoid hiding network/path anomalies by default.

**Open Questions:**
- Should `RED*` suppression become optionally configurable for advanced operators, or remain intentionally unsuppressible?
- Should redirect module expose a CLI switch for choosing HEAD vs GET fallback for rare servers that reject HEAD?

**Next:**
- Session 4: email-auth module (SPF/DKIM/DMARC local header analysis)
- Add `pip-audit` target and CI step
- Continue P1 refinement with per-rule allowlist granularity and confidence calibration docs

**Tests:**
- `ruff check src tests` passed
- `mypy src tests` passed
- `pytest -q` passed (48 tests)

## 2026-02-16 13:20 - Session 4: Email auth module and dependency-audit wiring

**Agent:** Codex

**Goal:** Implement local email-header authentication analysis (SPF/DKIM/DMARC) and wire dependency auditing (`pip-audit`) into project tooling and CI.

**Module(s) Touched:** modules:email_auth, adapters:cli, docs/process, ci/tooling

**Changes:**
- Added email auth module:
  - `src/lsh/modules/email_auth/analyzer.py`
  - `src/lsh/modules/email_auth/__init__.py`
  - `src/lsh/modules/email_auth/README.md`
- Implemented deterministic header parsing from local content (`Authentication-Results`, `Received-SPF`) with findings:
  - `EML000_EMPTY_INPUT`
  - `EML001_NO_AUTH_HEADERS`
  - `EML101/102` (SPF fail vs weak/missing)
  - `EML201/202` (DKIM fail vs weak/missing)
  - `EML301/302` (DMARC fail vs weak/missing)
- Wired module exports in `src/lsh/modules/__init__.py`
- Added new CLI command `email-check` in `src/lsh/adapters/cli.py`:
  - `lsh email-check <headers_or_file>`
  - options: `--json`, `--family`, `--file`
  - inline-header or file-path resolution with BOM-aware text loading
  - dedicated email summary builder and technical/family output views
- Added tests:
  - `tests/modules/test_email_auth.py`
  - updated `tests/test_smoke.py` for email command and file-input coverage
- Added dependency audit tooling:
  - `pyproject.toml` dev dependency: `pip-audit>=2.7`
  - `Makefile` target: `audit` (`pip-audit --progress-spinner off`)
  - CI step in `.github/workflows/ci.yml`: dependency audit (informational on Python 3.11)
- Updated docs and roadmap state:
  - `README.md`
  - `CLAUDE.md`
  - `ROADMAP.md`
  - `PLAN_REVIEW.md`
  - `docs/ARCHITECTURE.md`
  - `docs/MODULES.md`
  - `docs/ROADMAP.md`
  - `docs/PLAN_REVIEW.md`

**Decisions:**
- Kept Session 4 email-auth analysis offline and header-only (no DNS/network lookups) for deterministic behavior and low complexity.
- Modeled weak/missing auth states as lower-risk findings to avoid over-alerting on potentially legitimate forwarding scenarios.
- Wired `pip-audit` as informational in CI first (`continue-on-error: true`) to establish visibility without instantly breaking the main pipeline.

**Open Questions:**
- Should `pip-audit` become blocking in CI once a baseline triage pass is complete?
- Should email-auth findings include per-header source-line evidence (raw auth-result snippets) for forensic workflows?

**Next:**
- Session 5: QR decode module and URL pipeline handoff
- Consider tightening `pip-audit` policy from informational to enforced after dependency baseline review
- Continue P1 refinement with per-rule allowlist controls

**Tests:**
- `ruff check src tests` passed
- `mypy src tests` passed
- `pytest -q` passed (55 tests)
- Note: local `pip install -e ".[dev]"` failed in this environment due network/socket restrictions, so `pip-audit` binary could not be executed locally after wiring.

## 2026-02-16 13:44 - Session 4B: Trust-signal hardening pass (review follow-through)

**Agent:** Codex

**Goal:** Resolve review findings by improving registrable-domain accuracy, enforcing strict redirect opt-in parsing, and reducing forwarded-email false positives.

**Module(s) Touched:** core:url_tools/rules, modules:redirect, modules:email_auth, tests, docs

**Changes:**
- Improved registrable-domain extraction heuristics in `src/lsh/core/url_tools.py`:
  - Added generic ccTLD second-level handling (`co`, `com`, `net`, `org`, etc.) so domains like `paypaI.co.in` map to primary label `paypai`.
  - Kept deterministic offline behavior (no network calls).
- Added shared second-level constant in `src/lsh/core/rules.py`:
  - `COMMON_COUNTRY_SECOND_LEVEL_LABELS`
- Hardened redirect opt-in boolean parsing in `src/lsh/modules/redirect/analyzer.py`:
  - String values like `"false"`/`"0"` now stay disabled.
  - Unknown non-boolean values default to disabled.
- Refined email-auth status selection in `src/lsh/modules/email_auth/analyzer.py`:
  - Uses nearest-header precedence for `Authentication-Results`.
  - Uses `Received-SPF` only as SPF fallback when nearest auth-results SPF is missing.
  - Prevents worst-hop aggregation across forwarded paths.
- Expanded tests:
  - `tests/modules/test_ascii_lookalike.py`: added `.co.in` ambiguous-glyph case.
  - `tests/modules/test_url_structure.py`: added deceptive subdomain case on `.co.in`.
  - `tests/modules/test_redirect.py`: added string-false opt-in guard.
  - `tests/modules/test_email_auth.py`: added nearest-header precedence and Received-SPF fallback guard.
- Updated docs to reflect heuristic/precedence behavior:
  - `README.md`
  - `docs/ARCHITECTURE.md`
  - `docs/MODULES.md`
  - `src/lsh/modules/url_structure/README.md`
  - `src/lsh/modules/email_auth/README.md`

**Decisions:**
- Chose a dependency-free registrable-domain fix over adding a new library in this pass, so improvements remain fully offline, deterministic, and locally testable.
- Defaulted ambiguous `network_enabled` metadata to disabled to honor explicit opt-in safety for network analysis.
- Prioritized nearest auth headers to lower false positives from legitimate forwarding chains.

**Open Questions:**
- Should we add a larger maintained suffix fixture for uncommon ccTLD patterns beyond the current generic+explicit heuristic?
- Should email-auth expose a strict mode that still reports older-hop failures as low-confidence context?

**Next:**
- Consider confidence calibration pass for new `.co.*` and forwarded-email scenarios using curated fixture sets.
- Add optional “explain status source header index” evidence for email findings if operators want forensic traceability.

**Tests:**
- `ruff check src tests` passed
- `mypy src tests` passed
- `pytest -q` passed (60 tests)

---

## 2026-02-17 - Session 5: URL normalization and adversarial detection hardening

**Agent:** Claude Code (Claude Opus 4.6)

**Goal:** Harden the URL analysis pipeline to catch evasion techniques: integer/octal/hex/abbreviated IPs, localhost aliases, fragment deception, excessive encoding, IPv6-mapped IPv4, and mixed notation. Add canonicalization layer and compound scoring.

**Module(s) Touched:** core (normalizer, models, scorer, orchestrator), modules (net_ip, url_structure), tests, docs

**Changes:**
- Created `src/lsh/core/normalizer.py` with full URL canonicalization pipeline:
  - Iterative percent-decode (max 5 rounds)
  - Cross-platform IP parsing (integer, octal, hex, mixed, abbreviated) without socket.inet_aton
  - Localhost alias resolution
  - IPv6-mapped IPv4 extraction
  - Default port removal, trailing dot stripping, path normalization
- Added `NormalizedURL` model to `src/lsh/core/models.py`
- Added 6 new detection rules in `src/lsh/modules/net_ip/analyzer.py`:
  - `NET003_OBFUSCATED_IP` (integer/octal/hex/abbreviated IP encoding)
  - `NET004_LOCALHOST_ALIAS` (localhost, localhost.localdomain, etc.)
  - `NET005_IPV6_MAPPED_V4` (::ffff:x.x.x.x wrapping)
  - `NET006_MIXED_NOTATION` (mixed hex/octal/decimal in dotted quads)
- Added 2 new detection rules in `src/lsh/modules/url_structure/analyzer.py`:
  - `URL004_FRAGMENT_DECEPTION` (fragment mimicking trusted domain with @ or full URL)
  - `URL005_EXCESSIVE_ENCODING` (encoded hostname, path traversal, double-encoding)
- Updated `src/lsh/core/scorer.py`:
  - Added `confidence_score()` numeric mapping for Confidence enum
  - Added `compute_severity_score()` (risk * confidence)
  - Added `aggregate_findings()` compound scoring (worst-floor + diminishing bonuses at 0.15^i, cap 100)
- Updated `src/lsh/core/orchestrator.py` to use compound aggregation instead of max-score-wins
- Fixed pre-existing `model_dump_json(ensure_ascii=True)` bug in `cli.py` (unsupported in Pydantic 2.11)
- Created `tests/core/test_normalizer.py` (47 unit tests)
- Created `tests/test_adversarial_urls.py` (35 parametrized + targeted tests for 15 adversarial cases)
- Updated `docs/ROADMAP.md` and `docs/PLAN_REVIEW.md` for session scope

**Decisions:**
- Used next-available rule IDs (NET003-NET006, URL004-URL005) instead of the session plan's IDs to avoid collisions with existing NET002_PUBLIC_IP_LITERAL and URL003_NESTED_URL_PARAMETER.
- Kept Severity enum and bands unchanged (INFO/LOW/MEDIUM/HIGH/CRITICAL) to avoid a massive refactor across all modules and tests. The plan's SAFE/INFO/CAUTION/WARNING/DANGER bands can be adopted in a future session.
- Kept Confidence as StrEnum with numeric mapping rather than switching to float, preserving backward compatibility with existing modules and display logic.
- Made IP parsing fully deterministic and cross-platform by not using socket.inet_aton (different octal behavior on Linux vs Windows).
- Broadened URL005_EXCESSIVE_ENCODING to detect encoded hostnames and path traversal (not just round count), since the test cases require catching single-round-but-suspicious patterns.

**Open Questions:**
- Should severity band labels be migrated to the plan's SAFE/INFO/CAUTION/WARNING/DANGER scheme in a dedicated refactor session?
- Should the normalizer be run as a shared pre-processing step (cached on AnalysisInput) instead of per-module?
- Should fragment deception check use a larger brand list or configurable patterns?

**Next:**
- Session 6: QR decode module and URL pipeline handoff
- Optional: detection rules documentation page (docs/DETECTION_RULES.md)
- Optional: severity band label migration

**Tests:**
- `ruff check src tests` passed
- `mypy src tests` passed
- `pytest -v --tb=short` passed (142 tests, up from 60)

---

## 2026-02-22 - Session 5B: Documentation consolidation and repo deep dive

**Agent:** Codex

**Goal:** Reconcile repository documentation with the actual codebase, remove duplicate/stale docs, and capture the highest-leverage next steps for the alpha.

**Module(s) Touched:** docs/process only (`README.md`, `docs/*`, module READMEs, `CLAUDE.md`, `SKILL.md`, `SESSION_LOG.md`)

**Changes:**
- Audited implementation vs docs across CLI, core, modules, tests, and CI wiring.
- Verified current baseline with `pytest -q` (144 passing tests).
- Updated `README.md` to reflect current functionality, adversarial hardening work, and canonical docs layout.
- Updated canonical docs:
  - `docs/ARCHITECTURE.md`
  - `docs/MODULES.md`
  - `docs/ROADMAP.md`
  - `docs/PLAN_REVIEW.md`
  - `docs/GITHUB_STRATEGY.md`
- Updated drifted module docs:
  - `src/lsh/modules/net_ip/README.md` (now includes `NET003`-`NET006`)
  - `src/lsh/modules/url_structure/README.md` (now includes `URL004`/`URL005`)
- Updated agent workflow docs (`CLAUDE.md`, `SKILL.md`) to use canonical planning docs under `docs/`.
- Removed duplicate root planning docs (`ROADMAP.md`, `PLAN_REVIEW.md`).
- Removed stale one-off session plan doc (`claude-code-session-plan-2-17-26.md`).
- Captured current architecture/product gaps in docs (shared `normalize_url(...)` preprocessing not yet wired, QR module still pending, family formatter still in CLI, scoring helper semantics need cleanup).

**Decisions:**
- Treat `docs/` as the single source of truth for roadmap/plan/architecture docs; no mirrored root copies.
- Document current code behavior (including gaps) rather than leaving aspirational roadmap language in the primary docs.
- Keep process/agent docs in sync when file locations change to avoid future session drift.

**Open Questions:**
- Should shared URL preprocessing + input-aware routing land before QR (for cleaner integration) or immediately after QR (for faster feature parity)?
- Should confidence-weighted aggregation replace the current risk-only aggregate path, or should unused confidence scoring helpers be removed to avoid ambiguity?

**Next:**
- Session 6: QR decode module and URL pipeline handoff.
- Shared URL preprocessing + input-aware routing in orchestrator.
- Family formatter extraction from `cli.py`.
- False-positive controls phase 2 and confidence calibration/operator docs.

**Tests:**
- `pytest -q` passed (144 tests)
- Note: docs-only changes after the baseline test; no code behavior changes were introduced.

---

## 2026-02-23 - Session 6: Alpha integration pass (orchestrator context, formatter extraction, scoring cleanup, QR handoff)

**Agent:** Codex

**Goal:** Ship the highest-alpha integration improvements that make the tool smoother for future web/API adapters without rewriting the detection engine.

**Module(s) Touched:** core, adapters, formatters, modules:qr_decode, tests, docs, session log

**Changes:**
- Added shared per-analysis runtime context and URL preprocessing cache:
  - `src/lsh/core/context.py`
  - runtime context attached to `AnalysisInput` via private attr in `src/lsh/core/models.py`
  - orchestrator now builds context once per analysis (`src/lsh/core/orchestrator.py`)
- Migrated first URL detectors to shared context:
  - `src/lsh/modules/net_ip/analyzer.py`
  - `src/lsh/modules/url_structure/analyzer.py`
- Added focused tests proving URL context caching / single build per analysis:
  - `tests/core/test_context.py`
- Extracted family rendering into reusable formatter layer:
  - `src/lsh/formatters/family.py`
  - `src/lsh/formatters/__init__.py`
  - CLI family output paths now call formatter helpers (`src/lsh/adapters/cli.py`)
  - formatter tests added (`tests/formatters/test_family.py`)
- Resolved scoring ambiguity by clarifying risk-only aggregate policy:
  - removed unused confidence-weighting helpers from `src/lsh/core/scorer.py`
  - documented confidence as informational/user-facing (not aggregate math)
  - added scorer invariant tests (`tests/core/test_scorer.py`)
- Implemented QR decode module + CLI URL handoff:
  - `src/lsh/modules/qr_decode/analyzer.py`
  - `src/lsh/modules/qr_decode/__init__.py`
  - `src/lsh/modules/qr_decode/README.md`
  - new CLI command: `lsh qr-scan <image_path> [--json] [--family] [--all]`
  - decoded HTTP(S) QR payloads are routed through the existing URL orchestrator
  - optional dependency/runtime backend errors are surfaced as friendly CLI errors
  - tests added: `tests/modules/test_qr_decode.py`, QR smoke tests in `tests/test_smoke.py`
- Fixed Windows console JSON output bug discovered during required smoke checks:
  - `check`, `email-check`, and `qr-scan` JSON paths now use `json.dumps(..., ensure_ascii=True)` via shared `_echo_json(...)`
  - updated Unicode JSON smoke assertion in `tests/test_smoke.py`
- Updated canonical docs to reflect the new reality and next steps:
  - `README.md`
  - `docs/ARCHITECTURE.md`
  - `docs/MODULES.md`
  - `docs/ROADMAP.md`
  - `docs/PLAN_REVIEW.md`
  - plus module README docs and agent context docs (`CLAUDE.md`, `SKILL.md`)
- Kept `docs/` as the canonical planning/docs location and retained removal of root duplicate roadmap/plan files.

**Decisions:**
- Introduced runtime context as non-serialized state on `AnalysisInput` to preserve the existing JSON contract while enabling adapter-ready preprocessing.
- Migrated only `net_ip` and `url_structure` first to keep risk low and demonstrate the pattern before touching all URL detectors.
- Chose risk-only aggregate scoring (confidence remains messaging metadata) to avoid behavior churn while eliminating scorer ambiguity.
- Implemented QR support as a thin decode + URL handoff layer instead of a new analysis pipeline.
- Fixed JSON console safety with ASCII-escaped JSON to preserve machine-readability across Windows console encodings.

**Open Questions:**
- Should `homoglyph` / `ascii_lookalike` consume canonical host context or continue to prefer raw hostname views for some checks?
- What should the first API adapter response shape be for multi-result flows (`qr-scan --all`, future batch scans) to stay stable for a Next.js frontend?

**Next:**
- Add input-aware module routing in orchestrator and migrate remaining URL detectors to shared runtime context.
- Add a minimal Python API adapter (FastAPI) reusing orchestrator + `lsh.formatters.family`.
- Add structured multi-item response wrappers for QR/batch workflows.
- Continue false-positive controls phase 2 (per-rule allowlists + operator docs).
- Tighten `pip-audit` CI policy after dependency baseline review.

**Tests / Verification:**
- `python -m pytest -q` passed (155 tests)
- `ruff check .` passed
- `mypy .` passed
- `python -m lsh.adapters.cli check --json "http://google.com:80@evil.com"` passed (JSON output, `URL001_USERINFO_PRESENT` present)
- `python -m lsh.adapters.cli check --json "https://ｅxample.com"` passed after JSON console-safety fix (Unicode escaped as `\uff45`)
- `python -m lsh.adapters.cli qr-scan .tmp-blank-qr-test.png` returned friendly error on blank image (`No QR payloads were decoded from the image.`), confirming command/runtime behavior with local QR dependencies available

---

## 2026-02-23 - Session 6B: Wrap-up docs, roadmap alignment, and repo hygiene

**Agent:** Codex

**Branch:** `feat/orchestrator-preprocess-and-qr`

**Related Commits (feature stack):**
- `9ee24ce` `feat(core): add shared URL runtime context`
- `6a4edd6` `refactor(cli): extract reusable family formatter`
- `5e34c95` `refactor(core): clarify aggregate scoring policy`
- `02dd5e7` `feat(cli): add qr-scan URL handoff flow`
- `6e0e460` `fix(cli): make json output console-safe`
- `5557289` `docs: sync architecture roadmap and session log`
- `88cbe65` `chore: ignore local claude settings`
- `e51c549` `docs: add seamless quickstart and context roadmap notes`

**Goal:** Finish the session with push-ready documentation and session records that clearly explain what shipped, what broke, why decisions were made, and what the next session should do.

**What Shipped (Wrap-up Summary):**
- Canonical docs refreshed to match the shipped alpha integration work:
  - shared URL runtime context in orchestrator (`src/lsh/core/context.py`)
  - initial module migrations (`net_ip`, `url_structure`)
  - reusable family formatter extraction (`src/lsh/formatters/family.py`)
  - risk-only aggregate scoring policy clarification (`src/lsh/core/scorer.py`)
  - QR decode module + `lsh qr-scan` URL handoff
- `README.md` now includes a clearer golden path quickstart:
  - install commands for PowerShell + Git Bash/macOS/Linux
  - URL/email/QR examples
  - Windows-safe JSON note (ASCII-escaped Unicode)
  - common issues section (Windows `make`, QR backend, `--network`, JSON escaping)
- `docs/ARCHITECTURE.md` now documents runtime URL context creation, contents, migration status, and why context is non-serialized runtime state.
- `docs/MODULES.md` now includes a shared URL context adoption status table (module -> Yes/No/N/A) plus future migration targets.
- `docs/ROADMAP.md` and `docs/PLAN_REVIEW.md` now share the same top-5 alpha next steps checklist (with rationale) to reduce drift.
- Repo hygiene improved:
  - `.claude/settings.local.json` is no longer tracked
  - `.gitignore` now explicitly ignores `.claude/settings.local.json`

**Verification Commands + Outcomes:**
- `python -m pytest -q` -> passed (`155 passed`)
- `ruff check .` -> passed
- `mypy .` -> passed
- `python -m lsh.adapters.cli check --json "http://google.com:80@evil.com"` -> passed (`URL001_USERINFO_PRESENT` present in JSON)
- `python -m lsh.adapters.cli check --json "https://ｅxample.com"` -> passed (Unicode safely escaped in JSON as `\uff45`)
- `python -m lsh.adapters.cli qr-scan .tmp-blank-qr-test.png` -> friendly error (`No QR payloads were decoded from the image.`) after creating a temporary blank image for smoke verification

**Issue Hit During Verification:**
- Windows console (`cp1252`) raised `UnicodeEncodeError` when printing JSON output containing non-ASCII characters (`python -m lsh.adapters.cli check --json "https://ｅxample.com"`).

**Fix + Rationale:**
- Switched CLI JSON output paths (`check`, `email-check`, `qr-scan`) to a shared `_echo_json(...)` helper using `json.dumps(..., ensure_ascii=True)`.
- Rationale: preserves valid machine-readable JSON while avoiding terminal encoding crashes on non-UTF Windows consoles.

**Known Risks + Mitigations:**
- Partial shared-context migration:
  - Risk: some URL detectors still parse raw input directly.
  - Mitigation: documented current migration status and added explicit next-step checklist to migrate remaining detectors.
- Runtime context semantics:
  - Risk: confusion about what is serialized vs runtime-only.
  - Mitigation: docs now state that context is non-serialized internal state to preserve public JSON contracts.
- QR dependencies (`Pillow` / `pyzbar` / `zbar`):
  - Risk: QR scanning may be unavailable on some systems.
  - Mitigation: `qr-scan` has a friendly error path; README common-issues section documents this without impacting URL/email usage.

**Next Session Priorities (Top 5):**
- [ ] Input-aware orchestrator routing + migrate remaining URL detectors to shared context
  Rationale: removes duplicate parsing paths and makes CLI/API behavior consistent on one preprocessing pipeline.
- [ ] Stable batch/multi-result response wrappers (`qr-scan --all`, future batch scans)
  Rationale: prevents frontend/API contract churn before a web UI starts depending on result shapes.
- [ ] Minimal FastAPI adapter reusing orchestrator + formatter layers
  Rationale: creates the Python backend seam for a future Next.js UI without rewriting detectors.
- [ ] Deployment baseline (Docker + one provider)
  Rationale: makes hosting reproducible early and surfaces environment issues before UI work accelerates.
- [ ] Minimal Next.js UI calling the Python API
  Rationale: validates the end-to-end product loop and UX needs while preserving the Python engine.

---

## 2026-03-01 - Session 7A: Phase 1 branch/CI cleanup and QR payload parsing hardening

**Agent:** Codex

**Branch:** `main`

**Goal:** Execute Phase 1 stabilization work in one pass: clean branch state, align CI/workflow branch policy, fix QR payload parsing edge case, and run targeted regression checks.

**Module(s) Touched:** workflow/docs, qr_decode module, tests, session log

**Changes:**
- Branch cleanup:
  - fast-forwarded local `main` to `origin/main`.
  - removed stale local branch `feat/orchestrator-preprocess-and-qr` after merge.
  - current branch state is now clean (`main` tracking `origin/main`).
- CI/workflow alignment:
  - updated `.github/workflows/ci.yml` triggers from `[main, dev]` to `[main]` for both `push` and `pull_request`.
  - updated `docs/GITHUB_STRATEGY.md` to reflect the actual trunk workflow:
    - removed `dev` integration-branch assumptions
    - clarified short-lived feature/fix/docs branches
    - changed push workflow to PRs targeting `main`.
- QR parsing fix:
  - in `src/lsh/modules/qr_decode/analyzer.py`, `extract_url_payloads(...)` now parses the trimmed candidate (`candidate`) rather than raw payload text.
  - this fixes false negatives for payloads containing leading/trailing whitespace.
- Targeted regression tests:
  - added `test_extract_url_payloads_accepts_whitespace_wrapped_urls` in `tests/modules/test_qr_decode.py`.

**Decisions:**
- Chose to align docs and CI with current repo reality (PRs to `main`) instead of preserving a `dev` branch workflow that is not currently in use.
- Kept QR fix minimal and deterministic: only changed parsing to use already-trimmed candidate values.

**Open Questions:**
- Should we keep the local backup branch (`backup/pre-rebase-20260215-2303`) for history or prune it in a later cleanup pass?
- Should CI run on pushes to `feat/*` in addition to PRs, or stay restricted to `main` push + PR to `main`?

**Next:**
- Start Session 7 API/web groundwork:
  1. input-aware orchestrator routing
  2. remaining URL detector migration to shared context
  3. stable batch response wrappers

**Tests / Verification:**
- `.venv\Scripts\python.exe -m pytest tests/modules/test_qr_decode.py tests/test_smoke.py -q` passed (`26 passed`)
- `.venv\Scripts\python.exe -m ruff check .` passed
- `.venv\Scripts\python.exe -m mypy .` passed
- `.venv\Scripts\python.exe -m pytest -q` passed (`156 passed`)

---

## 2026-03-01 - Session 7B: Phase 2 routing and full offline URL-context migration

**Agent:** Codex

**Branch:** `main`

**Goal:** Execute Phase 2 work: add input-aware orchestrator routing, migrate remaining offline URL detectors to shared runtime context, and keep docs/tests in sync.

**Module(s) Touched:** core models/orchestrator, modules (`homoglyph`, `ascii_lookalike`, module contracts), tests, docs

**Changes:**
- Added module input-type contract support:
  - `src/lsh/core/models.py` now defines `AnalysisInputType` and a default `ModuleInterface.supported_input_types` property.
- Added orchestrator-side input routing:
  - `src/lsh/core/orchestrator.py` now filters module execution by `analysis_input.input_type in module.supported_input_types`.
- Declared explicit supported input types per module:
  - URL modules: `homoglyph`, `ascii_lookalike`, `url_structure`, `net_ip`, `redirect` -> `{"url"}`
  - Email module: `email_auth` -> `{"email_headers", "email_file"}`
  - QR module: `qr_decode` -> `{"qr_image"}`
- Migrated remaining offline URL detectors to shared runtime context:
  - `src/lsh/modules/homoglyph/analyzer.py`
    - now uses `url_context_for_input(...)` for hostname and IDNA forms
    - uses cached literal-IP signal from context
  - `src/lsh/modules/ascii_lookalike/analyzer.py`
    - now uses `url_context_for_input(...)` for hostname/IP-literal handling
- Strengthened orchestrator tests:
  - `tests/core/test_orchestrator.py`
    - replaced stale max-score assumption with `aggregate_findings(...)` policy assertion
    - added explicit routing test (`test_orchestrator_routes_modules_by_supported_input_type`)
- Synced docs to new architecture status:
  - `README.md`
  - `docs/ARCHITECTURE.md`
  - `docs/MODULES.md`
  - `docs/ROADMAP.md`
  - `docs/PLAN_REVIEW.md`

**Decisions:**
- Kept module-level input guards where they already existed for defense in depth, but made orchestrator routing the primary execution control.
- Limited Phase 2 migration scope to offline URL detectors (`homoglyph`, `ascii_lookalike`), leaving `redirect` context-enrichment optional as planned.

**Open Questions:**
- Should we remove remaining module-side input guards now that orchestrator routing is authoritative, or keep them permanently as fail-safe checks?
- Should `redirect` consume shared hostname/domain context for evidence consistency, or remain network-trace-focused only?

**Next:**
- Phase 3: structured multi-result response wrappers (`qr-scan --all`, batch-ready API shape) and minimal FastAPI adapter.

**Tests / Verification:**
- `.venv\Scripts\python.exe -m pytest tests/core/test_orchestrator.py tests/modules/test_homoglyph.py tests/modules/test_ascii_lookalike.py -q` passed (`18 passed`)
- `.venv\Scripts\python.exe -m ruff check .` passed
- `.venv\Scripts\python.exe -m mypy .` passed
- `.venv\Scripts\python.exe -m pytest -q` passed (`157 passed`)

---

## 2026-03-01 - Session 7C: Phase 3 structured wrappers and minimal FastAPI adapter

**Agent:** Codex

**Branch:** `main`

**Goal:** Deliver Phase 3 backend groundwork by adding stable single/multi response wrappers and a minimal API adapter that reuses the existing orchestrator/formatter stack.

**Module(s) Touched:** adapters (CLI + API), formatters, tests, docs, packaging metadata

**Changes:**
- Added reusable structured payload builders in `src/lsh/formatters/structured.py`:
  - `build_single_result_payload(...)`
  - `build_multi_result_payload(...)`
  - `build_qr_scan_payload(...)`
- Updated formatter exports in `src/lsh/formatters/__init__.py`.
- Wired CLI QR JSON output to shared structured wrapper logic:
  - `src/lsh/adapters/cli.py` now routes `_qr_json_payload(...)` through `build_qr_scan_payload(...)`.
  - kept legacy keys (`selected_url`, `result`, `results`) for backward compatibility while adding stable wrapper keys (`schema_version`, `mode`, `item_count`, `item/items`).
- Added minimal optional FastAPI adapter in `src/lsh/adapters/api.py`:
  - `GET /health`
  - `POST /api/v1/url/check`
  - `POST /api/v1/email/check`
  - `POST /api/v1/qr/scan`
  - uses shared orchestrator + structured formatter payloads
  - handles QR dependency/runtime errors with HTTP status mapping.
- Added optional API dependencies in `pyproject.toml` (`api` extra and dev inclusion):
  - `fastapi`
  - `uvicorn`
- Added/updated tests:
  - `tests/formatters/test_structured.py` (wrapper payload shape stability)
  - `tests/adapters/test_api.py` (FastAPI smoke; auto-skips when FastAPI unavailable)
  - updated QR JSON smoke assertion in `tests/test_smoke.py` for wrapper metadata.
- Updated docs for API/wrapper reality:
  - `README.md`
  - `docs/ARCHITECTURE.md`
  - `docs/ROADMAP.md`
  - `docs/PLAN_REVIEW.md`

**Decisions:**
- Introduced `schema_version: "1.0"` wrapper metadata now to reduce future API/CLI JSON contract churn.
- Preserved existing CLI QR JSON keys to avoid breaking current consumers while layering the new stable wrapper structure.
- Kept API adapter optional at runtime so core CLI usage remains lightweight when API deps are not installed.

**Open Questions:**
- Should next API iteration add explicit OpenAPI response models per endpoint for stricter contract enforcement?
- Should we promote wrapper usage to URL/email CLI JSON output as a versioned opt-in (`--json-v2`) before changing defaults?

**Next:**
- Draft frontend integration notes for Next.js against `/api/v1/*` response shapes.
- Add deployment baseline (Dockerfile + simple ASGI run profile).

**Tests / Verification:**
- `.venv\Scripts\python.exe -m ruff check .` passed
- `.venv\Scripts\python.exe -m mypy .` passed
- `.venv\Scripts\python.exe -m pytest -q` passed (`161 passed, 1 skipped`)

---

## 2026-03-01 - Session 7D: API contract documentation and frontend integration notes

**Agent:** Codex

**Branch:** `main`

**Goal:** Complete Session 1 API-consumer work by documenting a stable API contract, tightening endpoint error shape consistency, and adding contract-level tests for integration safety.

**Module(s) Touched:** API adapter, API adapter tests, docs (`API_INTEGRATION`, roadmap/plan/README), session log

**Changes:**
- Added `docs/API_INTEGRATION.md` as API integration source of truth:
  - endpoint inventory
  - request payload contracts
  - success wrapper contracts (`single`/`multi`)
  - QR compatibility keys and wrapper-first guidance
  - explicit API error envelope and known error codes
  - versioning policy (`schema_version`)
  - Next.js integration notes with TypeScript starter types and fetch helper sketch
- Tightened API error consistency in `src/lsh/adapters/api.py`:
  - added `_api_error(...)` helper for endpoint-generated errors
  - QR error paths now return structured `detail` envelope with code/message/status
  - added schema version in error envelope
- Expanded API contract tests in `tests/adapters/test_api.py`:
  - URL family payload presence
  - email endpoint wrapped response shape
  - QR single and multi wrapped response shapes
  - QR structured error envelope checks for:
    - decoder unavailable
    - no URL payloads
    - no payloads
- Updated docs to reflect contract/integration completion:
  - `README.md` now links `docs/API_INTEGRATION.md`
  - `docs/ROADMAP.md` marks Session 7 complete and transitions next milestone to deployment/UI validation
  - `docs/PLAN_REVIEW.md` includes API contract docs status and follow-up guidance

**Decisions:**
- Kept FastAPI validation (`422`) responses as framework-default format and documented that separately from contracted endpoint error envelope.
- Preserved wrapper contract as primary integration surface while retaining QR legacy keys for compatibility.

**Open Questions:**
- Should we add explicit FastAPI response models for full OpenAPI contract strictness, or keep schema enforcement test-driven for now?
- Should URL/email CLI `--json` outputs also move to wrapped contract shapes under an opt-in flag before any default change?

**Next:**
- Session 8: deployment baseline (Docker + hosting runbook) and minimal Next.js UI validation loop.

**Tests / Verification:**
- `.venv\Scripts\python.exe -m ruff check .` passed
- `.venv\Scripts\python.exe -m mypy .` passed
- `.venv\Scripts\python.exe -m pytest -q` passed (`161 passed, 1 skipped`)

---

## 2026-03-01 - Session 8A: Deployment baseline and UI validation runbook kickoff

**Agent:** Codex

**Branch:** `main`

**Goal:** Start Session 8 by shipping a reproducible deployment baseline (container artifacts + runbook), align CI/docs, and add a concrete Next.js UI validation checklist tied to the API contract.

**Module(s) Touched:** deployment artifacts, CI workflow/docs, roadmap/plan docs, session log

**Changes:**
- Added container deployment artifacts:
  - `Dockerfile` (FastAPI runtime with `.[api,qr]` install and `/health` healthcheck)
  - `.dockerignore` (keeps image context small and deterministic)
  - `docker-compose.yml` (local baseline service run)
- Added deployment runbook:
  - `docs/DEPLOYMENT.md`
  - includes local Docker/Compose commands and one hosted profile example (Render)
- Added frontend integration execution checklist:
  - `docs/NEXTJS_UI_VALIDATION.md`
  - defines required URL/email/QR UI assertions against `schema_version=1.0` contract
- Updated CI for deployment artifact safety:
  - `.github/workflows/ci.yml` now includes a `docker-build` job (`docker build -t lsh-api:ci .`)
- Updated strategy/docs alignment:
  - `docs/GITHUB_STRATEGY.md` CI scope now includes container build smoke check
  - `README.md` includes container baseline commands and links to deployment/validation docs
  - `docs/ROADMAP.md` marks Session 8 as in progress with deployment baseline + provider profile done
  - `docs/PLAN_REVIEW.md` marks deployment baseline as complete in top-5 progression

**Decisions:**
- Installed `.[api,qr]` in container to keep QR endpoint behavior consistent with API contract and avoid surprise `503` due missing optional deps.
- Kept Session 8 frontend scope as validation-first (checklist + contract assertions) before adding a full Next.js scaffold in a follow-on step.

**Open Questions:**
- Should we commit a minimal Next.js scaffold in-repo (`ui/`) or keep frontend in a separate repo once UI work starts?
- Should we add an integration smoke workflow that runs container + `/health` HTTP probe in CI, beyond build-only verification?

**Next:**
- Session 8B: minimal Next.js UI scaffold and contract-focused end-to-end smoke path against local API.

**Tests / Verification:**
- `.venv\Scripts\python.exe -m ruff check .` passed
- `.venv\Scripts\python.exe -m mypy .` passed
- `.venv\Scripts\python.exe -m pytest -q` passed (`161 passed, 1 skipped`)
- `docker --version` passed
- `docker build -t lsh-api:local .` passed
- `docker run -d -p 8000:8000 --name lsh-api-test lsh-api:local` passed
- `Invoke-RestMethod http://127.0.0.1:8000/health` returned `{"status":"ok"}`
- `docker rm -f lsh-api-test` passed

---

## 2026-03-01 - Session 8B: Minimal Next.js scaffold and contract smoke path

**Agent:** Codex

**Branch:** `main`

**Goal:** Complete Session 8 UI validation work by adding a minimal Next.js scaffold that exercises URL/email/QR contract flows and a repeatable contract-focused smoke path.

**Module(s) Touched:** `ui/` scaffold, docs (`README`, deployment/UI validation, roadmap/plan), gitignore, session log

**Changes:**
- Added minimal Next.js TypeScript scaffold under `ui/`:
  - `ui/package.json`, `ui/package-lock.json`, `ui/tsconfig.json`, `ui/next.config.mjs`, `ui/next-env.d.ts`
  - app routes:
    - `ui/app/page.tsx` (overview)
    - `ui/app/url/page.tsx`
    - `ui/app/email/page.tsx`
    - `ui/app/qr/page.tsx`
  - shared client helper:
    - `ui/lib/api.ts` (typed wrapper parsing + structured API error handling)
  - UI styling and local instructions:
    - `ui/app/globals.css`
    - `ui/README.md`
- Added contract-focused smoke script from frontend runtime perspective:
  - `ui/scripts/api-contract-smoke.mjs`
  - validates:
    - `/health`
    - URL wrapped single response
    - email wrapped single response
    - QR structured error envelope (`QRC_IMAGE_READ_ERROR`)
- Updated repository/docs alignment:
  - `README.md` now includes UI scaffold run commands and smoke command
  - `docs/NEXTJS_UI_VALIDATION.md` now reflects implemented scaffold + script
  - `docs/DEPLOYMENT.md` includes UI smoke companion step
  - `docs/ROADMAP.md` marks Session 8 UI scaffold and contract smoke items complete
  - `docs/PLAN_REVIEW.md` marks minimal Next.js UI milestone complete
- Repo hygiene:
  - `.gitignore` now ignores `*.tsbuildinfo`
  - removed generated `ui/tsconfig.tsbuildinfo`

**Decisions:**
- Kept UI intentionally minimal and contract-first (wrapper fields + structured errors) rather than spending effort on production styling now.
- Used Node-native smoke script under `ui/scripts/` instead of introducing a heavier E2E framework at this stage.

**Open Questions:**
- Should we add Playwright-based browser E2E in a follow-up session, or keep contract smoke script + unit/integration checks as the short-term gate?
- Should QR UI path move from server-local image paths to upload flow in Session 9 to align with hosted use cases?

**Next:**
- Session 9: deployment hardening + hosted validation pass (provider config, operational checks, and CI policy tightening).

**Tests / Verification:**
- `.venv\Scripts\python.exe -m ruff check .` passed
- `.venv\Scripts\python.exe -m mypy .` passed
- `.venv\Scripts\python.exe -m pytest -q` passed (`161 passed, 1 skipped`)
- `npm run typecheck` in `ui/` passed
- `npm run build` in `ui/` passed (Next.js static build succeeded)
- `docker run -d -p 8000:8000 --name lsh-api-test lsh-api:local` passed
- `npm run smoke:api` in `ui/` passed (`health`, `url`, `email`, `qr error envelope`)
- `docker rm -f lsh-api-test` passed

---

## 2026-03-01 - Session 9A: QR API upload contract (multipart) + UI integration

**Agent:** Codex

**Branch:** `main`

**Goal:** Replace QR API path-based input with hosted-safe upload flow, update integration/UI contracts, and keep wrappers/error envelopes stable.

**Module(s) Touched:** API adapter, QR decode helpers, structured formatter metadata, API tests, Next.js UI client/page, smoke script, docs

**Changes:**
- API upload contract:
  - `POST /api/v1/qr/scan` now accepts `multipart/form-data`.
  - required field: `file` (`UploadFile`)
  - optional form fields: `analyze_all`, `family`
  - endpoint now decodes uploaded bytes using a new helper (`decode_qr_payloads_from_bytes`).
- QR decode helper:
  - added `decode_qr_payloads_from_bytes(image_bytes, image_name=...)` in `src/lsh/modules/qr_decode/analyzer.py`.
  - exported via `src/lsh/modules/qr_decode/__init__.py`.
- Structured response metadata:
  - QR payloads now include `image_name` (uploaded filename when available).
  - legacy `image_path` key retained for compatibility.
- API tests:
  - `tests/adapters/test_api.py` switched QR endpoint calls to multipart uploads (`files=...`, `data=...`).
  - added coverage for missing upload file (`422`).
- UI integration:
  - `ui/app/qr/page.tsx` now uses file input upload instead of path input.
  - `ui/lib/api.ts` now includes `postApiForm(...)` for FormData requests.
  - `ui/scripts/api-contract-smoke.mjs` now submits a multipart file and validates structured QR error envelope.
- Docs updates:
  - `docs/API_INTEGRATION.md` QR request contract updated to multipart form fields + curl example.
  - `docs/NEXTJS_UI_VALIDATION.md` updated to upload-based QR validation.
  - `docs/DEPLOYMENT.md` notes QR smoke now uses multipart upload (no server-local path).
  - `ui/README.md` and `README.md` updated for QR API contract wording.

**Decisions:**
- Kept response wrapper schema version at `1.0` and preserved QR legacy keys (`image_path`, `selected_url`, `result`, `results`) to avoid breaking existing consumers while migrating request input semantics.
- Kept CLI `lsh qr-scan <image_path>` unchanged; upload migration is API-specific to support hosted environments.

**Open Questions:**
- Should we set a formal deprecation window for QR legacy response keys now that `image_name` + wrapper keys are established?
- Do we want to add explicit FastAPI response models in Session 9B to enforce OpenAPI-level contract strictness?

**Next:**
- Session 9B: CI hardening (UI checks in CI, Docker runtime contract smoke, and dependency audit enforcement policy).

**Tests / Verification:**
- `.venv\Scripts\python.exe -m ruff check .` passed
- `.venv\Scripts\python.exe -m mypy .` passed
- `.venv\Scripts\python.exe -m pytest -q` passed (`161 passed, 1 skipped`)
- `npm run build` in `ui/` passed
- `npm run typecheck` in `ui/` passed (after `.next/types` generation by build)

---

## 2026-03-01 - Session 9B: CI hardening (UI + runtime smoke) and multipart dependency fix

**Agent:** Codex

**Branch:** `main`

**Goal:** Move CI from static-only validation to runtime behavior validation, and resolve FastAPI multipart dependency gaps introduced by QR upload contract.

**Module(s) Touched:** CI workflow, packaging metadata, roadmap/strategy docs, session log

**Changes:**
- CI workflow hardening in `.github/workflows/ci.yml`:
  - added `ui-check` job:
    - `npm ci`
    - `npm run build`
    - `npm run typecheck`
  - upgraded container job from build-only to runtime smoke (`docker-smoke`):
    - build image
    - run API container
    - wait for `/health`
    - run `ui` contract smoke (`npm run smoke:api`) against live container
    - print container logs on failure and always clean up container
- Multipart dependency fix:
  - added `python-multipart>=0.0.9` to `api` and `dev` extras in `pyproject.toml`.
  - this resolves CI/test and container startup failures after introducing FastAPI `UploadFile`/`Form` inputs for `/api/v1/qr/scan`.
- Documentation updates:
  - `README.md` CI scope now reflects Python + UI + runtime container smoke gates
  - `docs/GITHUB_STRATEGY.md` CI scope updated to include UI and runtime smoke steps
  - `docs/DEPLOYMENT.md` CI recommendation updated from build-only to runtime smoke flow
  - `docs/PLAN_REVIEW.md` CI status updated with current gate coverage
  - `docs/ROADMAP.md` marks Session 9 work item #2 complete

**Decisions:**
- Kept `pip-audit` informational for now to avoid blocking merges before a vulnerability triage baseline is established.
- Chose runtime smoke in CI (container boot + API contract probe) as the fastest reliability multiplier before hosted validation.

**Open Questions:**
- Should `pip-audit` be made required once a baseline suppression/triage policy file is defined?
- Should we split smoke checks into separate fail-fast steps for health vs contract for clearer CI failure diagnostics?

**Next:**
- Session 9C: hosted validation pass (CORS + deployed endpoint checks + UI smoke against hosted API).
- Session 9D: API response-model strictness and QR legacy key deprecation plan.

**Tests / Verification:**
- `.venv\Scripts\python.exe -m ruff check .` passed
- `.venv\Scripts\python.exe -m mypy .` passed
- `.venv\Scripts\python.exe -m pytest -q` passed (`161 passed, 1 skipped`)
- `npm run build` in `ui/` passed
- `npm run typecheck` in `ui/` passed
- Local runtime smoke:
  - `docker build -t lsh-api:ci-local .` passed
  - `docker run -d -p 8000:8000 --name lsh-api-ci-local lsh-api:ci-local` passed
  - `/health` probe passed
  - `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run smoke:api` in `ui/` passed
  - container cleanup passed

---

## 2026-03-01 - Session 9C: Hosted-validation readiness (CORS config + preflight smoke)

**Agent:** Codex

**Branch:** `main`

**Goal:** Execute Session 9C by making hosted UI/API integration explicit and testable: CORS configuration, preflight verification, and runbook-driven hosted smoke flow.

**Module(s) Touched:** API adapter, CI smoke script, adapter tests, deployment/API docs, roadmap/plan docs

**Changes:**
- Added API CORS middleware wiring in `src/lsh/adapters/api.py`:
  - env var: `LSH_API_CORS_ALLOW_ORIGINS`
  - default allowlist when env is unset:
    - `http://127.0.0.1:3000`
    - `http://localhost:3000`
  - supports comma-separated custom origins for hosted deployments.
- Added CORS preflight tests in `tests/adapters/test_api.py`:
  - default local origin allowed
  - env override respected and unlisted origin denied
- Expanded `ui/scripts/api-contract-smoke.mjs`:
  - new `NEXT_PUBLIC_UI_ORIGIN` support
  - OPTIONS preflight check for `/api/v1/url/check`
  - verifies `access-control-allow-origin` before API contract checks
- Updated CI smoke environment in `.github/workflows/ci.yml`:
  - passes `NEXT_PUBLIC_UI_ORIGIN=http://127.0.0.1:3000` in docker-smoke contract step
- Updated docs/runbooks:
  - `docs/API_INTEGRATION.md` adds CORS contract section and env policy
  - `docs/DEPLOYMENT.md` adds hosted validation sequence (reachability + preflight + smoke)
  - `docs/NEXTJS_UI_VALIDATION.md` adds CORS/reachability assertions
  - `ui/README.md` smoke scope now includes CORS preflight
  - `README.md` updated smoke command envs and optional API CORS override
  - `docs/PLAN_REVIEW.md` follow-up notes CORS env + preflight validation
  - `docs/ROADMAP.md` Session 9 item 3 annotated with current state

**Decisions:**
- Defaulted API CORS to localhost UI origins when unset to keep local UI workflow friction low while requiring explicit origin config in hosted environments.
- Kept hosted-validation checklist explicit in docs so the same smoke script is reusable across local and deployed URLs.

**Open Questions:**
- Which exact hosted UI/API domains should be used for the first real external validation run to fully close Session 9 item 3?
- Should we allow wildcard CORS (`*`) in non-production only, and enforce explicit origins in production profiles?

**Next:**
- Run final hosted validation commands against real deployed API/UI domains and capture outcomes in session log.
- Then proceed to Session 9D (response-model strictness + legacy key deprecation plan).

**Tests / Verification:**
- `.venv\Scripts\python.exe -m ruff check .` passed
- `.venv\Scripts\python.exe -m mypy .` passed
- `.venv\Scripts\python.exe -m pytest -q` passed (`161 passed, 1 skipped`)
  - note: FastAPI adapter test module remains skipped locally in this env
- `npm run build` in `ui/` passed
- `npm run typecheck` in `ui/` passed
- runtime smoke against container:
  - `docker build -t lsh-api:session9c .` passed
  - `docker run -d -p 8000:8000 --name lsh-api-9c lsh-api:session9c` passed
  - `/health` probe passed
  - `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 NEXT_PUBLIC_UI_ORIGIN=http://127.0.0.1:3000 npm run smoke:api` passed
  - container cleanup passed

---

## 2026-03-01 - Session 9D: API contract enforcement + QR legacy-key deprecation controls

**Agent:** Codex

**Branch:** `main`

**Goal:** Tighten API contract enforcement with explicit response models and establish an executable migration path for QR legacy response keys.

**Module(s) Touched:** API adapter, API response model definitions, structured formatter controls, adapter/formatter tests, roadmap/plan/docs, session log

**Changes:**
- Added typed API contract models in `src/lsh/adapters/api_models.py`:
  - strict success wrappers for URL/email/QR flows
  - strict QR single/multi union response model (`mode`-discriminated)
  - strict structured error envelope model for QR endpoint error docs
- Enforced response models in FastAPI adapter (`src/lsh/adapters/api.py`):
  - `response_model` now declared on URL/email/QR endpoints
  - explicit QR endpoint error response docs (`400`/`503`) now reference typed error envelope model
- Added QR legacy-key deprecation control path:
  - new env var: `LSH_API_INCLUDE_QR_LEGACY_KEYS` (default: enabled)
  - when enabled, QR responses keep legacy keys and emit header:
    - `X-LSH-QR-Legacy-Keys: included; sunset=2026-06-01; use=item/items`
  - when disabled, QR legacy keys are omitted and header becomes `disabled`
- Extended structured formatter (`src/lsh/formatters/structured.py`):
  - `build_qr_scan_payload(..., include_legacy_keys=True)`
  - legacy keys can now be omitted while preserving wrapper contract
- Tests expanded:
  - `tests/adapters/test_api.py`:
    - OpenAPI schema test ensures typed response model wiring is active
    - QR legacy header assertions
    - env-driven legacy-key disable behavior (keys absent when disabled)
  - `tests/formatters/test_structured.py`:
    - added single/multi tests for `include_legacy_keys=False`
- Docs synced:
  - `docs/API_INTEGRATION.md`: response-model enforcement and QR legacy-key control/deprecation policy
  - `docs/ROADMAP.md`: Session 9 item #4 marked complete
  - `docs/PLAN_REVIEW.md`: API strictness follow-up adjusted to reflect response-model completion
  - `docs/DEPLOYMENT.md` and `README.md`: new `LSH_API_INCLUDE_QR_LEGACY_KEYS` env option

**Decisions:**
- Kept `schema_version` at `1.0`; enforcement and migration controls were added without a breaking contract bump.
- Used env-gated legacy keys rather than immediate removal to allow staged client migration.

**Open Questions:**
- Do we want to set a hard release date for defaulting `LSH_API_INCLUDE_QR_LEGACY_KEYS=false` prior to `2.0`?
- Should URL/email legacy-key strategy be explicitly declared as “none planned” to avoid ambiguity for integrators?

**Next:**
- Complete hosted validation against real deployed API/UI domains (Session 9 item #3).
- After hosted validation, decide on default legacy-key behavior timeline and publish migration notice.

**Tests / Verification:**
- `.venv\Scripts\python.exe -m ruff check .` passed
- `.venv\Scripts\python.exe -m mypy .` passed
- `.venv\Scripts\python.exe -m pytest -q` passed (`163 passed, 1 skipped`)

---

## 2026-03-01 - Session 10A: Enforce dependency audit gate + triage policy

**Agent:** Codex

**Branch:** `main`

**Goal:** Promote dependency security from informational checks to an enforced CI gate and document an actionable triage/exception policy.

**Module(s) Touched:** CI workflow, build tooling, security/process docs, roadmap, session log

**Changes:**
- CI enforcement:
  - `.github/workflows/ci.yml`
    - changed dependency step from informational to enforced:
      - removed `continue-on-error: true`
      - command now: `pip-audit --progress-spinner off --strict`
      - still scoped to Python `3.11` matrix lane
- Local tooling alignment:
  - `Makefile` `audit` target now uses `--strict`
- Added dependency security policy doc:
  - `docs/DEPENDENCY_AUDIT.md`
  - covers:
    - CI enforcement behavior
    - local run commands
    - triage workflow
    - temporary exception controls (issue-required, expiry-required)
    - review cadence
- Documentation sync:
  - `docs/GITHUB_STRATEGY.md` updated CI scope to mark `pip-audit` enforced
  - `docs/PLAN_REVIEW.md` section 7 updated from "not yet enforced" to enforced state + follow-up guidance
  - `docs/ROADMAP.md` risk mitigation now includes enforced dependency-audit gate
  - `README.md` development notes now call out enforced dependency audit and links `docs/DEPENDENCY_AUDIT.md`

**Decisions:**
- Kept enforcement on Python `3.11` only (existing matrix pattern) to avoid duplicate audit runtime while retaining consistent gate behavior.
- Chose issue-tracked, time-bound temporary exceptions instead of silent ignores.

**Open Questions:**
- Do we want to enforce dependency audit on both Python versions in CI, or keep the single-lane approach for runtime/cost efficiency?
- Should we add a dedicated exceptions registry file in-repo if temporary ignores are ever needed?

**Next:**
- Run hosted-domain validation when available to close the final open Session 9 roadmap item.
- Optionally add per-rule allowlist granularity / calibration fixtures as the next product-improvement session.

**Tests / Verification:**
- `.venv\Scripts\python.exe -m ruff check .` passed
- `.venv\Scripts\python.exe -m mypy .` passed
- `.venv\Scripts\python.exe -m pytest -q` passed (`163 passed, 1 skipped`)
- Verified recent GitHub Actions dependency-audit step baseline was successful before enforcement.
- Local `pip-audit` execution in this environment is network-restricted; CI remains the source of truth for live advisory resolution.

---

## 2026-03-01 - Session 10B: Fix strict dependency-audit false failure on local package

**Agent:** Codex

**Branch:** `main`

**Goal:** Resolve GitHub Actions dependency-audit failures caused by strict audit of the local editable project package (`link-safety-hub`) while keeping third-party vulnerability gating enforced.

**Module(s) Touched:** CI workflow, local build tooling, dependency-audit docs, README, session log

**Changes:**
- Updated dependency-audit command to skip editable/local package resolution:
  - `.github/workflows/ci.yml`: `pip-audit --progress-spinner off --strict --skip-editable`
  - `Makefile` `audit` target: `pip-audit --progress-spinner off --strict --skip-editable`
- Updated policy and developer docs for command parity:
  - `docs/DEPENDENCY_AUDIT.md`
  - `README.md`
- Expanded dependency-audit triage guidance to explicitly distinguish local package resolution errors from real third-party advisories.

**Decisions:**
- Kept `--strict` in place to preserve blocking behavior for real dependency risk.
- Added `--skip-editable` rather than weakening the gate, so only unauditable local editable metadata is excluded.

**Open Questions:**
- Should the install step move from editable (`-e`) to non-editable in CI to simplify package-audit semantics further?

**Next:**
- Re-run GitHub Actions and confirm `check (3.11)` dependency-audit now progresses to vulnerability evaluation instead of failing on `link-safety-hub`.

**Tests / Verification:**
- `python -m ruff check src tests` passed.
- Local `pip-audit` binary is not installed in this shell environment, so direct local audit execution was not verified here.

---

## 2026-03-01 - Session 10C: Make dependency-audit gate version-robust in CI

**Agent:** Codex

**Branch:** `main`

**Goal:** Fix remaining CI dependency-audit failures after Session 10B by removing reliance on a potentially unsupported `pip-audit` CLI flag and keeping strict vulnerability enforcement.

**Module(s) Touched:** CI workflow, Makefile audit target, dependency-audit docs, README, session log

**Changes:**
- Replaced direct `pip-audit --skip-editable` usage with a two-step audit flow:
  - `python -m pip freeze --exclude-editable > .pip-audit-requirements.txt`
  - `python -m pip_audit --progress-spinner off --strict -r .pip-audit-requirements.txt`
- Applied this flow in:
  - `.github/workflows/ci.yml` (`check` job, Python 3.11 dependency audit step)
  - `Makefile` (`audit` target)
- Updated docs to reflect new enforced behavior:
  - `docs/DEPENDENCY_AUDIT.md`
  - `README.md`

**Decisions:**
- Kept strict audit semantics and blocking CI behavior unchanged.
- Used snapshot-based auditing to avoid editable/local package resolution edge cases and CLI version flag drift.

**Open Questions:**
- Should we add a cleanup step for `.pip-audit-requirements.txt` in local `make audit`, or keep it for troubleshooting reproducibility?

**Next:**
- Confirm GitHub Actions `check (3.11)` dependency-audit step is green on the new run, then resume planned roadmap work.

**Tests / Verification:**
- `python -m ruff check src tests` passed.
