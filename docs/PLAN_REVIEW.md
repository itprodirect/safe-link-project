# Plan Review: Gaps, Risks, and Corrections

Status note: updated on 2026-03-01 after Session 7 contract docs and API integration guidance.

## What Is Working Well

- Modular contract-first design is holding up.
- URL coverage is materially stronger after adversarial hardening (`NET003-006`, `URL004-005`).
- Core normalizer helpers are deterministic and well covered by tests.
- Orchestrator now provides shared URL runtime preprocessing context (first migration path in place).
- Orchestrator keeps the CLI adapter thin and easy to evolve.
- Family-mode output and confidence labels improve non-technical usability.
- Family formatting is now reusable outside the CLI (`src/lsh/formatters/family.py`).
- QR decode URL handoff is implemented (`lsh qr-scan`) without changing detector logic.

## What Still Needs Work

### 1. Shared URL Preprocessing + Routing Baseline Is Implemented

`src/lsh/core/context.py` now builds shared URL runtime context once per analysis, and orchestrator routes modules by declared `supported_input_types` before execution.

Why this matters:

- reduces repeated parsing/normalization work
- creates a stable path for raw + canonical URL semantics across detectors
- improves adapter readiness for future API/web entry points

Current state:

- all offline URL detectors now consume shared context (`net_ip`, `url_structure`, `homoglyph`, `ascii_lookalike`)
- `redirect` remains optional for future context enrichment
- module routing no longer relies on per-module early-return checks alone

Recommended follow-up:

- document raw-vs-canonical semantics per rule family in a dedicated detection reference

### 2. Scoring Ambiguity Was Resolved (Risk-Only Aggregate)

`src/lsh/core/scorer.py` now clearly documents the policy and removes the unused confidence-weighting helpers.

Current policy:

- overall risk aggregation uses finding `risk_score` values only
- `confidence` remains user-facing trust calibration metadata (summary/formatter behavior)

Follow-up:

- continue calibration work on individual detector `risk_score` values and confidence labels

### 3. QR Path Is Implemented (Local-Only, Optional Dependencies)

`src/lsh/modules/qr_decode/` and `lsh qr-scan` now exist.

Current behavior:

- decodes local QR payloads via optional `Pillow` + `pyzbar`/zbar backend
- filters HTTP(S) URL payloads
- routes decoded URL payloads into the existing URL orchestrator
- handles missing QR backend dependencies with friendly errors

Follow-up:

- structured multi-result shapes are now implemented for QR single/all flows
- add fixture-based decode tests when a stable cross-platform fixture path is chosen

### 4. Family Rendering Extraction Is Complete (Next: API/Web Variants)

Family rendering now uses `src/lsh/formatters/family.py`.

Recommended follow-up:

- extend API/web-oriented structured formatter outputs as UI needs stabilize
- keep CLI focused on parsing and transport only

### 5. API Contract Documentation Is Now In Place

`docs/API_INTEGRATION.md` now defines endpoint payloads, wrapper semantics, error handling, and Next.js integration patterns.
FastAPI endpoints now also use explicit response models for success payloads and QR structured error envelopes.

Recommended follow-up:

- keep examples in lockstep with adapter behavior whenever payload fields evolve
- keep QR legacy-key migration/deprecation timeline visible to integrators
- keep `LSH_API_CORS_ALLOW_ORIGINS` settings explicit in deployment environments and validate preflight during hosted smoke checks

### 6. False Positive Strategy Is Now Operational

Current controls are a good start:

- `confidence` labels
- domain allowlist (`--allowlist-domain`, `--allowlist-file`)
- scoped allowlist categories (`--allowlist-category`, including `NONE`)
- per-rule allowlist tokens (`--allowlist-finding`, API `allowlist_findings`)
- confidence-aware family summary wording
- broader brand/suffix calibration fixtures in module tests (`co.uk`, `com.au`, `co.jp`)

Operator guidance now in docs:

- confidence interpretation bands in README (`HIGH`/`MEDIUM`/`LOW`)
- API contract notes for allowlist category and per-finding behavior

### 7. CI Security Checks Are Enforced

CI now runs:

- Python quality gates (`ruff`, `mypy`, `pytest`, coverage on 3.11)
- UI gates (`npm run build`, `npm run typecheck`)
- container runtime smoke (build + boot + `/health` + API contract smoke via `ui/scripts/api-contract-smoke.mjs`)
- `pip-audit` is enforced on Python 3.11

Recommended follow-up:

- keep dependency exceptions time-bound and issue-tracked per `docs/DEPENDENCY_AUDIT.md`
- maintain monthly dependency refresh cadence and weekly review for active exceptions

## Documentation Sync Risk (Reduced, Not Gone)

The duplicate root planning docs were removed in favor of canonical copies under `docs/`, which reduces drift.

Remaining risk:

- implementation changes still need same-session doc updates

Recommended practice:

- treat docs updates as part of the definition of done for behavior changes
- use `docs/` as the single source of truth for architecture/roadmap/plan docs

## Immediate Corrections Applied in This Session

- Refreshed README and canonical `docs/` pages to match current code state
- Updated module docs for `net_ip` and `url_structure` to include newer finding codes
- Consolidated planning docs to `docs/` only (removed duplicate root copies)
- Removed stale one-off session plan doc (`claude-code-session-plan-2-17-26.md`)
- Updated agent workflow docs (`CLAUDE.md`, `SKILL.md`) to reference canonical planning docs

## Highest-Leverage Alpha Next Steps (Top 5)

- [x] Input-aware orchestrator routing + migrate remaining URL detectors to shared context
  Rationale: removes duplicate parsing paths and makes CLI/API behavior consistent on one preprocessing pipeline.
- [x] Stable batch/multi-result response wrappers (`qr-scan --all`, future batch scans)
  Rationale: prevents frontend/API contract churn before a web UI starts depending on result shapes.
- [x] Minimal FastAPI adapter reusing orchestrator + formatter layers
  Rationale: creates the Python backend seam for a future Next.js UI without rewriting detectors.
- [x] Deployment baseline (Docker + one provider)
  Rationale: makes hosting reproducible early and surfaces environment issues before UI work accelerates.
- [x] Minimal Next.js UI calling the Python API
  Rationale: validates the end-to-end product loop and UX needs while preserving the Python engine.
