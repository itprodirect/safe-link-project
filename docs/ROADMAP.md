# Roadmap

## Current Progress (2026-02-17)

- [x] Session 0: Package scaffold, core models, scorer, CLI skeleton
- [x] Session 1: Homoglyph / IDN module with focused tests
- [x] Session 2A: Orchestrator extraction and family-mode CLI rendering
- [x] Session 2B: Offline URL trust-signal expansion (`ASCII*`, `URL*`, `NET*`)
- [x] Session 2C: P1 start (`confidence` labels + domain allowlist path)
- [x] Session 2D: P1 continuation (`--allowlist-file`, scoped categories, confidence-aware family summaries)
- [x] Session 3: Redirect chain module (`--network`, `--max-hops`, `--timeout`)
- [x] Session 4: Email auth module + dependency-audit wiring
- [ ] Session 5: URL normalization and adversarial detection hardening (current)
- [ ] Session 6: QR decode module

## Next Session: 5 URL Normalization & Adversarial Detection

### Goal

Harden the URL analysis pipeline to catch evasion techniques that bypass current detection: integer IPs, octal notation, localhost, fragment deception, excessive encoding, and IPv6-mapped IPv4. Add a canonicalization layer and compound scoring.

### Work Items

1. Create `src/lsh/core/normalizer.py` with two-phase canonicalization pipeline.
2. Add `NormalizedURL` model to `models.py`.
3. Add 6 new detection rules: `NET002_OBFUSCATED_IP`, `NET003_LOCALHOST_ALIAS`, `URL003_FRAGMENT_DECEPTION`, `URL004_EXCESSIVE_ENCODING`, `URL005_MIXED_NOTATION`, `NET004_IPV6_MAPPED_V4`.
4. Update scoring: numeric confidence, computed severity, compound aggregation.
5. Write adversarial test suite (15 parametrized cases) and normalizer unit tests.
6. Integration smoke test and validation.

### Definition of Done

- Normalizer canonicalizes integer/octal/hex/abbreviated IPs, localhost, IPv6-mapped IPv4.
- All 15 adversarial test cases pass.
- Compound scoring replaces max-score-wins.
- `ruff`, `mypy`, `pytest` all pass.
- Docs and session log reflect new behavior.

## Near-Term Sequence

1. URL normalization & adversarial detection (Session 5, current)
2. QR decoder (#7)
3. Family formatter module (#9)
4. Input-type routing for multi-input orchestrator
5. Tighten dependency-audit policy in CI (`pip-audit`)

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
