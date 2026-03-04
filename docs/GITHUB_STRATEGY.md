# GitHub Strategy

## Repository Model

Use a single monorepo. The shared core contracts and orchestrator make split repos expensive early.

## Roadmap Tracking Model

V2 execution now uses GitHub milestones and epics:

- umbrella epic: `#2`
- phase epics: `#3`-`#10`
- child issues: created under each phase as work is pulled
- milestones: `V2-Phase-1` through `V2-Phase-8`

Keep `docs/V2_ROADMAP_ISSUES.md` and issue status in sync at phase boundaries.

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

Practical rule:

- prefer small, focused commits that each explain one coherent change
- include test/doc updates in the same commit when they are part of the behavior change

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
- dependency audit (`pip-audit`, enforced on Python 3.11)
- tests (excluding optional network-marked tests)
- coverage run on Python 3.11
- UI build + type checks (`ui`: `npm run build`, `npm run typecheck`)
- container runtime smoke check:
  - build API image
  - boot container
  - verify `/health`
  - run `ui` contract smoke against running container

Next CI upgrades:

- consider expanding type-check coverage to tests
- keep dependency-audit exception usage time-bound and issue-tracked (`docs/DEPENDENCY_AUDIT.md`)

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
