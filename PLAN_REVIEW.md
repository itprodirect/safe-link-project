# Plan Review: Gaps, Risks, and Corrections

Status updated: 2026-02-16

## Resolved Since Initial Plan

1. Scaffold-to-doc mismatch is resolved.
2. Core architecture exists and is testable.
3. Homoglyph detector is implemented and covered by tests.
4. CLI orchestration is now extracted into `core/orchestrator.py`.
5. Family mode output is now a real CLI path (`--family`).
6. Offline URL trust-signal coverage now includes `ASCII*`, `URL*`, and `NET*` findings.

## Remaining Gaps

1. QR module is not implemented yet.
2. False-positive management is in progress (`allowlist_domains`, `--allowlist-file`, scoped categories, confidence labels) but not yet complete.
3. `pip-audit` is wired as informational; enforcement policy is pending.
4. Docs exist in two locations (root + `docs/`) and require discipline to stay in sync.

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

1. Build the QR module with deterministic local decoding and URL handoff.
2. Tighten `pip-audit` from informational to enforced CI policy.
3. Extend allowlist controls with per-rule granularity and clearer operator docs.
