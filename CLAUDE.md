# CLAUDE.md - Agent Context for Link Safety Hub

## Project Summary

Link Safety Hub (LSH) is a modular, local-first security toolbelt for URL, email-header, and QR-linked analysis.
It targets clear risk decisions first, with technical evidence available when needed.

## Current State (2026-03-09)

Implemented:

- Core contracts/scoring/orchestration in `src/lsh/core/`
- Shared URL runtime context and normalization hardening
- Offline URL modules (`homoglyph`, `ascii_lookalike`, `url_structure`, `net_ip`)
- Opt-in redirect module (`redirect`)
- Email auth module (`email_auth`)
- QR decode helpers and `qr-scan` flow
- CLI + FastAPI adapters (v1 and v2 endpoints)
- Shared application service layer in `src/lsh/application/analysis_service.py`
- V2 endpoint: `POST /api/v2/analyze` with analyst payloads
- Contract wrappers and family formatter
- Next.js UI with unified `/analyze` workspace (Quick + Analyst modes)
- Verdict-first UX (`VerdictCard`, `WhyPanel`, action-level mapping)
- URL Analyst Mode with domain anatomy, redirect path, suppression traces, compare-ready evidence keys
- Docker deployment baseline
- Expanded regression coverage (223 tests):
  - adversarial URL tests
  - v1/v2 parity and edge-case matrix tests
  - snapshot parity fixtures in `tests/fixtures/contracts/`
  - browser smoke tests for unified workspace and verdict UX
- V2 phases E1-E4 complete (epics `#3`-`#6` closed)

Open priorities:

1. Complete hosted validation pass (Session 9 roadmap item 3).
2. Start E5: Policy Packs and suppression management (`#7`).
3. Continue with E6-E8 per V2 roadmap.

## Tech Stack

- Python 3.11+
- Click
- FastAPI (optional extra)
- Pydantic v2
- pytest, ruff, mypy
- Next.js (UI validation surface)

## Architecture Rules

1. Modules detect; core orchestrates/scales risk; application services compose; adapters handle transport.
2. Modules remain stateless and deterministic.
3. Keep scoring semantics in core/application, not in adapter presentation logic.
4. Keep network checks explicit and opt-in.
5. Keep docs and tests in lockstep with behavior changes.

## Session Start Checklist

1. Read last 2-3 entries in `SESSION_LOG.md`.
2. Read `docs/ROADMAP.md` and `docs/V2_ROADMAP_ISSUES.md`.
3. Check active GitHub issues for the current phase before coding.
4. Define one scoped goal with explicit acceptance criteria.

## Definition of Done (Per Session)

- `ruff check src tests` passes
- `mypy src tests` passes
- relevant `pytest` suites pass
- docs updated for architecture/contract changes
- `SESSION_LOG.md` appended with decisions, tests, and next steps

## Working Conventions

- Prefer small commits with descriptive conventional messages.
- Keep one theme per commit and per issue update.
- Update roadmap/issue tracker when milestones or phase status moves.
- Leave concrete breadcrumbs for the next session.

## What Not To Do

- Do not enable network behavior by default.
- Do not introduce hidden side effects in modules.
- Do not ship behavior changes without test coverage.
- Do not leave docs stale after architecture or contract changes.
