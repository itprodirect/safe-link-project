# Roadmap

## Current Progress (2026-02-16)

- [x] Session 0: Package scaffold, core models, scorer, CLI skeleton
- [x] Session 1: Homoglyph / IDN module with focused tests
- [x] Session 2A: Orchestrator extraction and family-mode CLI rendering
- [x] Session 2B: Offline URL trust-signal expansion (`ASCII*`, `URL*`, `NET*`)
- [x] Session 2C: P1 start (`confidence` labels + domain allowlist path)
- [x] Session 2D: P1 continuation (`--allowlist-file`, scoped categories, confidence-aware family summaries)
- [x] Session 3: Redirect chain module (`--network`, `--max-hops`, `--timeout`)
- [ ] Session 4: Email auth module (next)

## Next Session: 4 Email Auth Checker

### Goal

Add local email-header authentication analysis (SPF/DKIM/DMARC state parsing).

### Work Items

1. Create `src/lsh/modules/email_auth/` with parser and analyzer scaffolding.
2. Add CLI path for email-header input.
3. Emit structured findings for SPF/DKIM/DMARC signal presence and obvious failures.
4. Add unit tests with representative header fixtures.
5. Update docs and session log.

### Definition of Done

- Email auth findings are explainable and deterministic for local header input.
- `ruff`, `mypy`, `pytest` all pass.
- Docs reflect new behavior.

## Near-Term Sequence

1. Email auth checker (#5)
2. QR decoder (#7)
3. Family formatter module (#9)
4. Input-type routing for multi-input orchestrator
5. Dependency auditing in CI (`pip-audit`)

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
