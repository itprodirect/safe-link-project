---
name: session-0-green-ci
description: Bootstrap the package skeleton so CI passes and the CLI runs. Use this for the very first coding session.
disable-model-invocation: true
---

# Session 0: Get the Repo Green

You are working in the Link Safety Hub repo. The docs and architecture are done. Now implement the minimum code so CI passes and the CLI runs.

## Non-negotiables

- Keep the existing architecture contract described in CLAUDE.md
- Create `src/lsh/` package skeleton matching the structure in README.md
- Every module directory gets `__init__.py` (even if empty for now)
- Implement core Pydantic models in `src/lsh/core/models.py` matching the contract in `docs/ARCHITECTURE.md`
- Implement a stub scorer in `src/lsh/core/scorer.py`
- Implement a minimal CLI entry point using Click in `src/lsh/adapters/cli.py`
- Add `tests/test_smoke.py` with basic assertions
- Do NOT implement any real detection logic yet — stubs only

## Specific files to create

```
src/lsh/__init__.py
src/lsh/core/__init__.py
src/lsh/core/models.py          # AnalysisInput, Finding, Evidence, AnalysisResult, Severity enum
src/lsh/core/scorer.py           # Stub: normalize() returns findings unchanged
src/lsh/core/rules.py            # Empty for now, just __all__ = []
src/lsh/modules/__init__.py
src/lsh/adapters/__init__.py
src/lsh/adapters/cli.py          # Click CLI: lsh --help, lsh check <url>
tests/__init__.py
tests/test_smoke.py              # CLI runs, models validate, scorer returns
```

## Definition of done

- `pip install -e ".[dev]"` works without errors
- `make check` passes (ruff + mypy + pytest)
- `lsh --help` prints help text
- `lsh check https://example.com` returns a structured stub result
- Append a session log entry to `SESSION_LOG.md`

## What NOT to do

- Don't implement real detection logic
- Don't add FastAPI or any web server
- Don't add database dependencies
- Don't create module analyzer files yet (just __init__.py placeholders)
- Don't skip the session log entry
