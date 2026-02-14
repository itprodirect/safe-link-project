# Roadmap

## Phase 1: Personal CLI Toolbelt

Goal: local-first CLI for link, email, and QR safety checks.

## Session Checkpoint (as of 2026-02-13)

- [x] Session 0: repo green (core models/scorer + CLI skeleton)
- [x] Session 1: Homoglyph / IDN detector vertical slice
- [ ] Session 2: Redirect expander (opt-in network mode)

## Session 2 Scope (Next Session)

Goal: add safe redirect expansion without breaking offline-by-default behavior.

- Add Redirect module scaffold under `src/lsh/modules/redirect/`
- Keep default behavior offline
- Add explicit network opt-in flag for redirect expansion
- Add hop cap and timeout controls
- Return structured findings with evidence and recommendations
- Add focused tests (including mocked chains and timeout case)
- Update CLI summary output to include redirect guidance

Definition of done:

- `lsh check <url>` remains valid offline
- network mode can expand redirect chains safely
- `ruff`, `mypy`, and `pytest` all pass
- `SESSION_LOG.md` appended

## Remaining Phase 1 Build Order

1. Redirect Chain Expander (#2)
2. Email Auth Checker (#5)
3. QR Decoder (#7)
4. Family Mode Explainer (#9)
5. Orchestrator extraction from CLI
6. CLI subcommands and flags parity (`--json`, future `--family`)

## Phase 1 Exit Criteria

- URL checks produce risk score, evidence, and actionable summary
- Redirect analysis is safe and opt-in when network is required
- Email and QR modules are implemented and wired
- Tests and typing/lint checks are green in CI

## Phase 2+

- Phase 2: API + web adapter
- Phase 3: inbox workflows and domain profiling
- Phase 4: hardening and distribution strategy
