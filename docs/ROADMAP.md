# Roadmap

## Current Progress (2026-02-16)

- [x] Session 0: Package scaffold, core models, scorer, CLI skeleton
- [x] Session 1: Homoglyph / IDN module with focused tests
- [x] Session 2A: Orchestrator extraction and family-mode CLI rendering
- [x] Session 2B: Offline URL trust-signal expansion (`ASCII*`, `URL*`, `NET*`)
- [x] Session 2C: P1 start (`confidence` labels + domain allowlist path)
- [x] Session 2D: P1 continuation (`--allowlist-file`, scoped categories, confidence-aware family summaries)
- [ ] Session 3: Redirect chain module (next)

## Next Session: 3 Redirect Chain Expansion

### Goal

Add safe redirect-chain analysis with explicit network opt-in.

### Work Items

1. Create `src/lsh/modules/redirect/` with `analyzer.py`, `__init__.py`, `README.md`.
2. Add CLI flags:
   - `--network` (default false)
   - `--max-hops` (default sensible cap)
   - timeout option
3. Ensure offline mode remains default.
4. Add tests for:
   - no redirect
   - redirect chain
   - loop / max-hop guard
   - timeout handling
5. Update architecture and module docs.
6. Append session log.

### Definition of Done

- Redirect analysis only runs when `--network` is present.
- Redirect findings are explainable and consistent with scoring model.
- `ruff`, `mypy`, `pytest` all pass.
- Docs reflect new behavior.

## Near-Term Sequence

1. Redirect chain module (#2)
2. Email auth checker (#5)
3. QR decoder (#7)
4. Family formatter module (#9)
5. Input-type routing for multi-input orchestrator

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
