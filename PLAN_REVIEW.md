# Plan Review: Gaps, Risks, and Corrections

Status updated: 2026-02-16

## Resolved Since Initial Plan

1. Scaffold-to-doc mismatch is resolved.
2. Core architecture exists and is testable.
3. Homoglyph detector is implemented and covered by tests.
4. CLI orchestration is now extracted into `core/orchestrator.py`.
5. Family mode output is now a real CLI path (`--family`).

## Remaining Gaps

1. Redirect module is not implemented yet.
2. Email auth and QR modules are not implemented yet.
3. False-positive management (allowlist, confidence levels) is not implemented.
4. Dependency security gate (`pip-audit`) is not in CI yet.
5. Docs exist in two locations (root + `docs/`) and require discipline to stay in sync.

## Current Risks

### Architecture Risk

As more modules are added, scoring and summary semantics can drift unless all modules follow the same finding contract.

Mitigation:

- Keep all module outputs on `Finding` model
- Normalize through one scorer path
- Add module contract tests for each new module

### Process Risk

Agent sessions can diverge if session logs and roadmap are not updated immediately.

Mitigation:

- Session log update is required for every coding session
- Roadmap update required when priorities change

### UX Risk

Technical output can overwhelm non-technical users.

Mitigation:

- Keep `--family` output available and stable
- Move family explanation into a dedicated module in next sessions

## Recommendations for Next 2 Sessions

1. Build redirect module with strict guardrails and mocked tests.
2. Add `pip-audit` target and wire it into CI for vulnerability checks.
3. Introduce known-safe allowlist config for IDN false positives.
