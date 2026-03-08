# Roadmap

## Current Progress (2026-03-06)

- [x] Session 0: Package scaffold, core models, scorer, CLI skeleton
- [x] Session 1: Homoglyph / IDN module with focused tests
- [x] Session 2A: Orchestrator extraction and family-mode CLI rendering
- [x] Session 2B: Offline URL trust-signal expansion (`ASCII*`, `URL*`, `NET*`)
- [x] Session 2C: P1 start (`confidence` labels + domain allowlist path)
- [x] Session 2D: P1 continuation (`--allowlist-file`, scoped categories, confidence-aware family summaries)
- [x] Session 3: Redirect chain module (`--network`, `--max-hops`, `--timeout`)
- [x] Session 4: Email auth module + dependency-audit wiring
- [x] Session 5: URL normalization helpers + adversarial detection hardening (`normalizer.py`, `NET003-006`, `URL004-005`, adversarial suite)
- [x] Session 6: Alpha integration pass
  - shared orchestrator URL runtime preprocessing/context cache
  - first detector migrations (`net_ip`, `url_structure`)
  - reusable family formatter extraction
  - scoring policy cleanup (risk-only aggregate, confidence for messaging)
  - QR decode module + `qr-scan` URL handoff
- [x] Session 7: API/web adapter groundwork
  - [x] Input-aware orchestrator routing by module-declared input type support
  - [x] Remaining URL detector migration to shared URL runtime context (`homoglyph`, `ascii_lookalike`)
  - [x] Stable structured wrappers for single/multi result payloads (including QR `--all`)
  - [x] Minimal FastAPI adapter over existing orchestrator + formatter layers
  - [x] API contract + Next.js integration notes
- [x] Session 10: False-positive control completion
  - [x] per-finding allowlist scope (`--allowlist-finding`, API `allowlist_findings`)
  - [x] category `NONE` override for finding-only suppression on allowlisted domains
  - [x] broadened brand/suffix calibration fixtures and operator confidence guidance
- [x] Session 13: Verdict-first UX slice (`VerdictCard`, `WhyPanel`, action-level mapping)

## Session 8: Deployment + UI Validation

### Goal

Ship a reproducible deploy target and validate end-to-end UI integration against the stabilized API contract.

### Work Items

1. [x] Add Docker baseline for API runtime (`Dockerfile`, `.dockerignore`, run docs).
2. [x] Add one deployment profile (for example Render/Fly/Railway) with environment/runbook notes.
3. [x] Scaffold minimal Next.js UI against `/api/v1/*` contract.
4. [x] Add contract-focused smoke tests across deployed API + UI path.
5. [x] Update docs and session log.

### Definition of Done

- API deploys reproducibly from source.
- Frontend can call and render URL/email/QR flows against production-like API.
- Response shapes stay deterministic and versioned.
- `ruff`, `mypy`, and `pytest` pass.
- Docs and session log reflect architecture changes and adapter boundaries.

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

## Phase Exit Criteria

Phase 1 is complete when:

- URL checks include module-based findings and clear guidance
- Redirect support is safe and opt-in
- Email and QR commands exist with parity for `--json` and family output
- CI is green on PRs and local check workflow is stable

## Session 9: Deployment Hardening + Hosted Validation

### Goal

Close the remaining MVP gap between local validation and hosted-safe operation.

### Work Items

1. [x] Replace QR API path input with upload contract (`multipart/form-data`) and align UI integration path.
2. [x] Harden CI beyond static checks (UI type/build in CI, runtime API smoke, container health + contract checks).
3. [ ] Run hosted validation pass (CORS, endpoint reachability, UI contract smoke against deployed API).
   CORS middleware + preflight smoke checks are now implemented; execute against target hosted domains.
   Deployment option research and recommended paths are documented in `docs/DEPLOYMENT_OPTIONS.md`.
4. [x] Tighten API contract enforcement strategy (response model strictness + legacy key deprecation plan).

## Session 11: V2 Execution Kickoff (2026-03-04)

### Goal

Establish V2 execution structure in GitHub and complete the first foundation refactor slice.

### Work Items

1. [x] Publish V2 planning docs (`V2_BLUEPRINT`, `V2_ROADMAP_ISSUES`) and umbrella epic.
2. [x] Create phase milestones (`V2-Phase-1` to `V2-Phase-8`) and phase epic issues (`#3`-`#10`).
3. [x] Complete first E1 refactor slice:
   - add shared application service (`src/lsh/application/analysis_service.py`)
   - remove duplicated URL/email orchestrator wiring from CLI/API adapters
4. [x] Continue E1:
   - introduce `/api/v2/analyze` draft endpoint
   - add application-layer regression tests for shared service behavior and edge inputs
5. [ ] Remaining E1:
   - [x] add non-optional service/formatter snapshot parity suite for v1/v2 overlap
   - [x] add explicit endpoint-level parity tests for v1 and v2 response semantics in hosted/API-enabled lanes (`#11`)
   - [x] finalize E1 docs closeout checklist (`#12`)
6. [x] Create E1 child issues and acceptance criteria for closeout:
   - `#11` parity and snapshot governance
   - `#12` architecture/API docs sync closeout


## Session 12: Unified Analyze Workspace Slice (2026-03-05)

### Goal

Move `/analyze` from a shell into a usable shared workspace for Phase 2.

### Work Items

1. [x] Replace placeholder tabs with working URL, email, and QR forms on `/analyze`.
2. [x] Reuse typed client helpers for `POST /api/v2/analyze` and shared wrapped-response handling.
3. [x] Add type-specific validation plus URL allowlist/network controls in the workspace.
4. [x] Add workspace status states (loading, error, retry) and `Quick` / `Analyst` mode scaffold.
5. [x] Add end-to-end smoke coverage that drives all three flows through the rendered UI.

## Session 13: Verdict-First UX Slice (2026-03-06)

### Goal

Shift Quick mode from a generic summary layout to a decision-first surface.

### Work Items

1. [x] Add `VerdictCard` with explicit action-level mapping (`safe`, `caution`, `avoid`, `block`).
2. [x] Add `WhyPanel` with ranked reasons and ordered next actions.
3. [x] Refresh Quick-mode styling so the primary decision reads at a glance.
4. [x] Complete plain-language copy pass for all major outcomes across flows.
5. [x] Add broader UX/usability validation beyond the current smoke path.

## Session 14: URL Analyst Mode Deep Evidence Slice (2026-03-08)

### Goal

Finish the first shippable URL Analyst Mode surface and make the v2 contract ready for future compare/history work.

### Work Items

1. [x] Add URL-only `item.analyst` payloads on `/api/v2/analyze` with domain anatomy and evidence rows.
2. [x] Add redirect-path projection for network-enabled URL findings.
3. [x] Add suppression-trace visibility from allowlist decisions through API and UI.
4. [x] Add compare-ready evidence keys (`finding_key`, `compare_key`, keyed evidence maps) for future delta views.
5. [x] Sync API/docs/roadmap state with the delivered analyst-mode contract.

## Risks and Mitigations

- Risk: network-dependent logic increases flaky tests
  Mitigation: isolate network tests, mock requests by default, and keep network checks opt-in.
- Risk: vulnerable third-party dependencies slip into main
  Mitigation: enforce `pip-audit` in CI (Python 3.11) and follow `docs/DEPENDENCY_AUDIT.md` exception policy.
- Risk: false positives from internationalized domains
  Mitigation: maintain per-finding allowlist controls, calibration fixtures, and confidence guidance updates.
- Risk: docs drift from implementation
  Mitigation: keep `docs/` as the canonical docs location and update docs in the same change as behavior updates.
