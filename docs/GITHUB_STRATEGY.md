# GitHub Strategy

## Repository Model

Use a single monorepo. The shared core contracts and orchestrator make split repos expensive early.

## Branch Model

- `main`: protected, always releasable
- `feat/*`: one feature per branch (short-lived)
- `fix/*`: bug fixes (short-lived)
- `docs/*`: documentation-only changes (short-lived)

## PR Checklist

Before merging any PR:

1. `ruff check src tests`
2. `mypy src/` (CI parity)
3. `pytest -v --tb=short`
4. docs updated if behavior changed
5. session log updated

Optional stricter local pass:

- `mypy src tests`

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

## CI Scope

Current CI should run:

- lint
- type checks (`mypy src/`)
- dependency audit (`pip-audit`, informational on Python 3.11)
- tests (excluding optional network-marked tests)
- coverage run on Python 3.11

Next CI upgrades:

- tighten `pip-audit` from informational to enforced after baseline review
- consider expanding type-check coverage to tests

## Push Workflow for This Repo

1. Create or switch to feature branch.
2. Commit focused changes.
3. Push branch and open PR to `main`.
4. Merge to `main` only after required checks pass.

## Notes for Agent-Assisted Work

- Read recent session logs first.
- Use `docs/` as the canonical location for roadmap/plan docs.
- Keep one feature/theme per session.
- Do not leave code/docs mismatch at session end.
