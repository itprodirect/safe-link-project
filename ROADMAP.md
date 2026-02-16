# Roadmap

## Snapshot (2026-02-16)

Completed:

- Session 0: repo green and core scaffold
- Session 1: Homoglyph / IDN detector
- Session 2A: orchestrator extraction + CLI family mode + stronger tests
- Session 2B: offline URL trust-signal expansion (`ASCII*`, `URL*`, `NET*`)

In progress:

- Session 3: redirect-chain expansion (network opt-in)

## Session Plan (Immediate)

### Session 3 - Redirect Module

Goal: support safe redirect expansion without breaking offline defaults.

Scope:

- Add `src/lsh/modules/redirect/` scaffold
- Keep offline default behavior
- Add `--network`, `--max-hops`, and timeout controls
- Emit structured findings and recommendations
- Add unit tests with mocked chains and timeout case

Definition of done:

- `lsh check <url>` remains offline and works as before
- `lsh check <url> --network` shows redirect chain analysis
- `ruff`, `mypy`, and `pytest` all pass
- docs and session log updated

### Session 3 - Email Auth Module

Goal: parse email headers and evaluate SPF, DKIM, DMARC state.

### Session 4 - QR Decode Module

Goal: decode QR payload and pass URL into analysis pipeline.

### Session 5 - Family Formatter Module

Goal: move plain-language rendering out of CLI adapter into reusable layer.

## Phase Plan

### Phase 1: CLI MVP

- URL analysis with modular findings
- Redirect analysis with explicit opt-in
- Email and QR analysis basics
- Family + JSON output parity
- Reliable CI and repeatable local checks

### Phase 2: API and Web Adapter

- FastAPI adapter on top of orchestrator
- Lightweight frontend for family use

### Phase 3: Inbox Workflows

- Batch scanner for email exports
- Triaging and review workflow output

### Phase 4: Hardening and Distribution

- Dependency/security hardening
- Packaging and distribution improvements
