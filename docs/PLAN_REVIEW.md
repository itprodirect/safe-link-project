# Plan Review: Gaps, Risks, and Corrections

Status note: updated on 2026-02-16 after scoped allowlist + confidence UX upgrades.

## What Is Working Well

- Modular contract-first design is holding up.
- Core scorer and result shape are stable.
- Homoglyph detector provides actionable findings with evidence.
- New orchestrator keeps CLI adapter thinner and easier to evolve.
- Family-mode output reduces technical overload for non-technical users.

## What Still Needs Work

### 1. Redirect Safety Layer (resolved in Session 3)

The roadmap expected redirect expansion and now has an implemented module with explicit controls.

Implemented guardrails:

- network must be opt-in
- max-hop cap
- tight timeouts
- HEAD-only requests
- no content fetching beyond what is needed for redirect resolution

### 2. False Positive Strategy Is In Progress

Current Unicode checks can flag legitimate international domains, and brand-token heuristics are intentionally conservative.

What changed:

- Added initial `confidence` labels on findings
- Added initial domain allowlist flow (`allowlist_domains` / `--allowlist-domain`)
- Added scoped allowlist categories (`--allowlist-category`)
- Added allowlist file support (`--allowlist-file`)
- Added confidence-aware family summary wording and confidence visibility

What still remains:

- per-rule allowlist granularity
- explicit confidence calibration guidance in docs for end users

Recommended follow-up:

- allowlist support by hostname/domain pattern
- confidence labels on findings
- explicit "suspicious but could be legitimate" language path

### 3. CI Security Checks Are Started (Not Yet Enforced)

`ruff`, `mypy`, and `pytest` are in place. `pip-audit` is now wired in local tooling and CI as informational.

Recommended:

- tighten CI policy from informational to enforced once baseline is stable
- add periodic dependency refresh cadence

### 4. Documentation Sync Risk

Root docs and `docs/` docs are both used. Without strict discipline, they can drift.

Recommended:

- always update root and docs mirror files in same change
- treat stale docs as a release blocker

## Immediate Corrections Applied in This Session

- Orchestrator extraction completed
- Family-mode CLI output added
- Strict typing improvements in tests
- Core model defaults switched to `Field(default_factory=...)`
- Added offline URL-structure checks (`URL001`-`URL003`)
- Added IP literal checks (`NET001`/`NET002`)
- Added ASCII lookalike checks (`ASCII001`/`ASCII002`)
- Prevented homoglyph confusable logic on IP literals and ASCII-only spoof cases
- Added opt-in redirect-chain checks with hop/timeout guardrails (`RED*`)
- Added local email-auth checks (`EML*`) for SPF/DKIM/DMARC header signals
- Added `pip-audit` target and informational CI step

## Next Session Priority

1. QR decode module implementation and URL pipeline handoff.
2. Tighten `pip-audit` CI policy after baseline review.
3. Continue false-positive controls with per-rule allowlist granularity.
