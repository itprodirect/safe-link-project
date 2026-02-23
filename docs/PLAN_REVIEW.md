# Plan Review: Gaps, Risks, and Corrections

Status note: updated on 2026-02-23 after the alpha integration pass (shared URL runtime context, formatter extraction, QR handoff, scoring cleanup).

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

### 1. Shared URL Preprocessing Is Partially Implemented (Migration In Progress)

`src/lsh/core/context.py` now builds a shared URL runtime context once per analysis and attaches it to `AnalysisInput` as non-serialized runtime state.

Why this matters:

- reduces repeated parsing/normalization work
- creates a stable path for raw + canonical URL semantics across detectors
- improves adapter readiness for future API/web entry points

Recommended follow-up:

- migrate remaining URL detectors (`homoglyph`, `ascii_lookalike`, optionally `redirect`) to the shared context
- document which checks run on raw vs canonical forms

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

- consider structured multi-result API shapes for batch/web use
- add fixture-based decode tests when a stable cross-platform fixture path is chosen

### 4. Family Rendering Extraction Is Complete (Next: API/Web Variants)

Family rendering now uses `src/lsh/formatters/family.py`.

Recommended follow-up:

- add API/web-oriented structured formatter outputs and response wrappers
- keep CLI focused on parsing and transport only

### 5. False Positive Strategy Is In Progress

Current controls are a good start:

- `confidence` labels
- domain allowlist (`--allowlist-domain`, `--allowlist-file`)
- scoped allowlist categories (`--allowlist-category`)
- confidence-aware family summary wording

What still remains:

- per-rule allowlist granularity
- clearer operator documentation on confidence interpretation and expected false positives
- broader brand/suffix fixtures for calibration

### 6. CI Security Checks Are Started (Not Yet Enforced)

`ruff`, `mypy`, and `pytest` run in CI. `pip-audit` is wired as informational.

Recommended follow-up:

- tighten `pip-audit` from informational to enforced once dependency baseline is triaged
- add a dependency refresh cadence and triage notes

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
