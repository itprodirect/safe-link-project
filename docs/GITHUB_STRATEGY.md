# GitHub Strategy

## Repository Model

Use a single monorepo. The shared core contracts and orchestrator make split repos expensive early.

## Branch Model

- `main`: protected, always releasable
- `dev`: integration branch
- `feat/*`: one feature per branch
- `fix/*`: bug fixes
- `docs/*`: documentation-only changes

## PR Checklist

Before merging any PR:

1. `ruff check src tests`
2. `mypy src tests`
3. `pytest -v --tb=short`
4. docs updated if behavior changed
5. session log updated

## Commit Conventions

Use conventional commits:

- `feat(core): ...`
- `feat(homoglyph): ...`
- `fix(cli): ...`
- `docs(roadmap): ...`
- `test(core): ...`
- `log(session): ...`

## Recommended Branch Protections

For `main`:

- require PR
- require status checks
- require linear history
- block force push

For `dev`:

- require status checks

## CI Scope

Current CI should run:

- lint
- type checks
- tests (excluding optional network-marked tests)

Next CI upgrade:

- add dependency scan (`pip-audit`)

## Push Workflow for This Repo

1. Create or switch to feature branch.
2. Commit focused changes.
3. Push branch and open PR to `dev`.
4. Merge `dev` to `main` only when stable.

## Notes for Agent-Assisted Work

- Read recent session logs first.
- Keep one feature/theme per session.
- Do not leave code/docs mismatch at session end.
