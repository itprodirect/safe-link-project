# CLAUDE.md - Agent Context for Link Safety Hub

## Project Summary

Link Safety Hub (LSH) is a modular, local-first security toolbelt for URL, email-header, and QR-linked analysis.
It targets clear risk decisions first, with technical evidence available when needed.

## Current State (2026-03-04)

Implemented:

- Core contracts/scoring/orchestration in `src/lsh/core/`
- Shared URL runtime context and normalization hardening
- Offline URL modules (`homoglyph`, `ascii_lookalike`, `url_structure`, `net_ip`)
- Opt-in redirect module (`redirect`)
- Email auth module (`email_auth`)
- QR decode helpers and `qr-scan` flow
- CLI + FastAPI adapters
- Shared application service layer in `src/lsh/application/analysis_service.py`
- Draft v2 endpoint: `POST /api/v2/analyze`
- Contract wrappers and family formatter
- Expanded regression coverage:
  - adversarial URL tests
  - v1/v2 parity and edge-case matrix tests
  - snapshot parity fixtures in `tests/fixtures/contracts/`
- V2 execution structure in GitHub:
  - umbrella epic `#2`
  - phase epics `#3`-`#10`
  - E1 child issues `#11` and `#12`

Open priorities:

1. Close E1 endpoint-level parity in API-enabled lanes (`#11`).
2. Close E1 docs sync checklist (`#12`).
3. Start E2 unified `/analyze` workspace shell (`#4`).
4. Complete hosted validation pass from Session 9 roadmap item 3.

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
