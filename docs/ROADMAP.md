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
- [ ] Session 7: API/web adapter groundwork (in progress)
  - [x] Input-aware orchestrator routing by module-declared input type support
  - [x] Remaining URL detector migration to shared URL runtime context (`homoglyph`, `ascii_lookalike`)

## Next Session: 7 API / Web UI Groundwork (Remaining)

### Goal

Prepare the tool for a future web UI by adding adapter-ready seams without rewriting the engine.

### Work Items

1. [x] Add input-aware module routing in orchestrator (reduce detector early-return boilerplate).
2. [x] Migrate remaining URL detectors to shared URL runtime context.
3. Define API-ready structured response wrappers for multi-item flows (QR `--all`, batch-ready shapes).
4. Add a minimal Python API adapter (FastAPI) that reuses orchestrator + formatter layers.
5. Draft frontend integration notes for a Next.js UI calling the Python API.
6. Update docs and session log.

### Definition of Done

- API adapter proof-of-concept works without changing detector logic.
- Shared URL runtime context is used by more URL detectors.
- Response shapes for CLI and API remain deterministic and documented.
- `ruff`, `mypy`, and `pytest` pass.
- Docs and session log reflect architecture changes and adapter boundaries.

## Highest-Leverage Alpha Next Steps (Top 5)

- [x] Input-aware orchestrator routing + migrate remaining URL detectors to shared context
  Rationale: removes duplicate parsing paths and makes CLI/API behavior consistent on one preprocessing pipeline.
- [ ] Stable batch/multi-result response wrappers (`qr-scan --all`, future batch scans)
  Rationale: prevents frontend/API contract churn before a web UI starts depending on result shapes.
- [ ] Minimal FastAPI adapter reusing orchestrator + formatter layers
  Rationale: creates the Python backend seam for a future Next.js UI without rewriting detectors.
- [ ] Deployment baseline (Docker + one provider)
  Rationale: makes hosting reproducible early and surfaces environment issues before UI work accelerates.
- [ ] Minimal Next.js UI calling the Python API
  Rationale: validates the end-to-end product loop and UX needs while preserving the Python engine.

## Phase Exit Criteria

Phase 1 is complete when:

- URL checks include module-based findings and clear guidance
- Redirect support is safe and opt-in
- Email and QR commands exist with parity for `--json` and family output
- CI is green on PRs and local check workflow is stable

## Risks and Mitigations

- Risk: network-dependent logic increases flaky tests
  Mitigation: isolate network tests, mock requests by default, and keep network checks opt-in.
- Risk: false positives from internationalized domains
  Mitigation: expand allowlist controls and confidence calibration guidance.
- Risk: docs drift from implementation
  Mitigation: keep `docs/` as the canonical docs location and update docs in the same change as behavior updates.
