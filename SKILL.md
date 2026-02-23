---
name: session-progress-loop
description: Execute one focused implementation session with code, tests, docs, and session logging.
disable-model-invocation: false
---

# Session Progress Loop

Use this workflow for any feature or refactor session in this repo.

## Step 1: Read Context

- last 2-3 entries in `SESSION_LOG.md`
- `docs/ROADMAP.md`
- `docs/PLAN_REVIEW.md`

## Step 2: Define Session Scope

- one clear goal
- concrete definition of done
- explicit files expected to change

## Step 3: Implement

- keep module boundaries clean
- keep adapter logic thin
- add/adjust tests with each behavior change

## Step 4: Verify

Run:

```bash
ruff check src tests
mypy src tests
pytest -v --tb=short
```

## Step 5: Sync Documentation

If behavior/architecture changed, update:

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/MODULES.md`
- `docs/ROADMAP.md` / `docs/PLAN_REVIEW.md` as needed

## Step 6: Log Session

Append to `SESSION_LOG.md`:

- agent
- goal
- modules touched
- changes
- decisions and reasoning
- open questions
- next steps
- tests
