# CLAUDE.md - Agent Context for Link Safety Hub

## Project Summary

Link Safety Hub (LSH) is a modular Python security toolbelt. Modules analyze one threat vector each (for example lookalike domains, redirect chains, or email authentication issues) and produce structured findings with risk scores plus plain-language guidance.

## Current State (2026-02-23)

Implemented:

- Core contracts in `src/lsh/core/models.py`
- Scoring normalization and compound aggregation in `src/lsh/core/scorer.py`
- Dedicated orchestration layer in `src/lsh/core/orchestrator.py`
- URL normalization/adversarial parsing helpers in `src/lsh/core/normalizer.py`
- Shared URL runtime preprocessing context in `src/lsh/core/context.py` (initial detector migration)
- CLI adapter in `src/lsh/adapters/cli.py`
- Reusable family formatter in `src/lsh/formatters/family.py`
- URL modules in `src/lsh/modules/`:
  - `homoglyph`
  - `ascii_lookalike`
  - `url_structure`
  - `net_ip`
  - `redirect` (opt-in network mode)
- `email_auth` module for local SPF/DKIM/DMARC header analysis
- `qr_decode` module helpers and `lsh qr-scan` CLI URL handoff
- Family output mode (`lsh check <url> --family`)
- Adversarial URL regression coverage (obfuscated IPs, fragment deception, encoding evasion)

Not implemented yet:

- Full migration of all URL detectors to shared runtime context (currently `net_ip` + `url_structure`)
- Input-aware orchestrator routing by `input_type`
- Python API adapter for future web UI integration

## Tech Stack

- Python 3.11+
- Click (CLI)
- Pydantic v2 (models)
- pytest
- ruff
- mypy (strict)

## Core Architecture Rules

1. Every detector module implements `ModuleInterface`.
2. Modules are stateless and side-effect free.
3. Scoring semantics live in core, not in adapters.
4. Adapter code handles parsing, command flags, and rendering only.
5. Family messaging is presentation logic, not detection logic.
6. No dynamic code execution in analysis modules.
7. Network behavior is opt-in for modules that require it.

## Session Start Checklist

1. Read the last 2-3 entries in `SESSION_LOG.md`.
2. Read `docs/ROADMAP.md` and `docs/PLAN_REVIEW.md`.
3. Confirm whether the session is feature, refactor, or docs/process.
4. Make one scoped plan with a clear definition of done.

## Definition of Done (Every Session)

- `ruff check src tests` passes
- `mypy src tests` passes
- `pytest -v --tb=short` passes
- `SESSION_LOG.md` has a new entry with reasoning and next steps

## Working Conventions

- Prefer small, focused commits
- Keep module boundaries strict
- Keep CLI behavior deterministic and testable
- Do not leave roadmap/docs out of sync with implementation
- If architecture changes, update docs in the same session

## Current Build Priority

1. Shared URL runtime context migration for remaining detectors + input-aware orchestrator routing
2. Python API adapter for future Next.js UI (reuse orchestrator + formatter)
3. False-positive controls phase 2 (per-rule allowlist granularity + operator docs)
4. Structured multi-item response wrappers (QR `--all`, batch flows)
5. Dependency audit policy hardening (`pip-audit` enforcement workflow)

## What Not To Do

- Do not add a web server yet
- Do not add DB dependencies
- Do not run dynamic malware detonation
- Do not make network calls by default
- Do not skip session logging
