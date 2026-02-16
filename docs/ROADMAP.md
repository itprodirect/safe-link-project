# Roadmap

## Current Progress (2026-02-16)

- [x] Session 0: Package scaffold, core models, scorer, CLI skeleton
- [x] Session 1: Homoglyph / IDN module with focused tests
- [x] Session 2A: Orchestrator extraction and family-mode CLI rendering
- [x] Session 2B: Offline URL trust-signal expansion (`ASCII*`, `URL*`, `NET*`)
- [x] Session 2C: P1 start (`confidence` labels + domain allowlist path)
- [x] Session 2D: P1 continuation (`--allowlist-file`, scoped categories, confidence-aware family summaries)
- [x] Session 3: Redirect chain module (`--network`, `--max-hops`, `--timeout`)
- [x] Session 4: Email auth module + dependency-audit wiring
- [ ] Session 5: QR decode module (next)

## Next Session: 5 QR Decoder

### Goal

Add local QR decode analysis and route decoded URLs into existing URL safety pipeline.

### Work Items

1. Create `src/lsh/modules/qr_decode/` with decode + extraction flow.
2. Add CLI path for QR image input.
3. Run decoded URLs through existing URL module pipeline.
4. Add fixtures and deterministic tests.
5. Update docs and session log.

### Definition of Done

- QR results are deterministic for local image inputs.
- `ruff`, `mypy`, `pytest` all pass.
- Docs reflect new behavior.

## Near-Term Sequence

1. QR decoder (#7)
2. Family formatter module (#9)
3. Input-type routing for multi-input orchestrator
4. Tighten dependency-audit policy in CI (`pip-audit`)

## Phase Exit Criteria

Phase 1 is complete when:

- URL checks include module-based findings and clear guidance
- Redirect support is safe and opt-in
- Email and QR commands exist with parity for `--json` and family output
- CI is green on PRs and local make/check workflow is stable

## Risks and Mitigations

- Risk: network-dependent logic increases flaky tests  
  Mitigation: isolate network tests and mock external calls by default.
- Risk: false positives from internationalized domains  
  Mitigation: keep expanding allowlist controls and confidence calibration guidance.
- Risk: docs drift from implementation  
  Mitigation: update docs in the same PR/commit as behavior changes.
