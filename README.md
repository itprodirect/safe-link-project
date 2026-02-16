# Link Safety Hub

Modular, local-first security CLI for analyzing suspicious links and giving clear next steps.

## Current Status (2026-02-16)

Implemented now:

- Core models and scoring in `src/lsh/core/`
- Dedicated orchestrator layer in `src/lsh/core/orchestrator.py`
- CLI adapter in `src/lsh/adapters/cli.py`
- Module #1 Homoglyph / IDN detector in `src/lsh/modules/homoglyph/`
- Two output modes:
  - Technical (default): finding codes, evidence-driven categories
  - Family (`--family`): plain-language summary and safer actions
- JSON output for machine-readable integrations (`--json`)
- Automated checks: `ruff`, `mypy`, `pytest`

Planned next:

- Module #2 Redirect chain expansion with explicit network opt-in
- Module #5 Email auth checks (SPF/DKIM/DMARC)
- Module #7 QR decode pipeline
- Module #9 Family mode as a reusable formatter layer

## Quick Start

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
lsh check https://example.com
lsh check https://xn--pple-43d.com --family
```

### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
lsh check https://example.com
lsh check https://xn--pple-43d.com --family
```

## CLI Usage

```bash
lsh check <url> [--json] [--family]
```

Examples:

```bash
# Technical output
lsh check https://xn--pple-43d.com

# Plain-language output
lsh check https://xn--pple-43d.com --family

# JSON output
lsh check https://xn--pple-43d.com --json
```

## Project Structure

```text
safe-link-project/
  src/lsh/
    adapters/
      cli.py
    core/
      models.py
      orchestrator.py
      scorer.py
    modules/
      homoglyph/
  tests/
    core/
    modules/
  docs/
  SESSION_LOG.md
```

## Development

```bash
# Lint
ruff check src tests

# Type check
mypy src tests

# Run tests
pytest -v --tb=short

# One command gate
make check
```

## Session Logging Process

Every coding session must append to `SESSION_LOG.md` with:

- goal
- files touched
- decisions with reasoning
- open questions
- next steps
- tests run and status

Before starting a new session, read the last 2-3 entries.

## Documentation Index

- Architecture: `docs/ARCHITECTURE.md`
- Module specs: `docs/MODULES.md`
- Roadmap: `docs/ROADMAP.md`
- Plan review and risks: `docs/PLAN_REVIEW.md`
- Security and responsible use: `docs/SECURITY.md`
- GitHub workflow strategy: `docs/GITHUB_STRATEGY.md`

## License

MIT
