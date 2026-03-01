# Roadmap

## Current Progress (2026-03-01)

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
4. [x] Tighten API contract enforcement strategy (response model strictness + legacy key deprecation plan).

## Risks and Mitigations

- Risk: network-dependent logic increases flaky tests
  Mitigation: isolate network tests, mock requests by default, and keep network checks opt-in.
- Risk: false positives from internationalized domains
  Mitigation: expand allowlist controls and confidence calibration guidance.
- Risk: docs drift from implementation
  Mitigation: keep `docs/` as the canonical docs location and update docs in the same change as behavior updates.
