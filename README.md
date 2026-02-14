# Link Safety Hub

Modular security toolbelt for inspecting links, messages, emails, and QR codes.

## Current Status (2026-02-13)

Implemented now:

- Core models and scorer (`src/lsh/core/`)
- CLI entrypoint with URL analysis (`lsh check <url>`)
- Module #1 Homoglyph / IDN detector (`src/lsh/modules/homoglyph/`)
- Family-friendly summary and actionable guidance in CLI output
- Focused tests for Homoglyph/IDN scenarios

Planned next:

- Module #2 Redirect Chain Expander (Session 2)
- Email Auth checker, QR decoder, Family Mode pipeline layer
- Dedicated orchestrator component (instead of CLI-local orchestration)

## Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/link-safety-hub.git
cd link-safety-hub
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# URL safety check (offline)
lsh check https://example.com

# JSON output
lsh check https://xn--pple-43d.com --json
```

## Current CLI Commands

- `lsh check <url>`

Note: `email-check`, `qr-scan`, and `inbox-scan` are planned but not implemented yet.

## Modules

| # | Module | Status | Description |
|---|--------|--------|-------------|
| 1 | Homoglyph / IDN Detector | Implemented (MVP) | Detects lookalike Unicode and punycode hostname risks |
| 2 | Redirect Chain Expander | Planned | Safely unwinds shortened URLs |
| 3 | Domain Risk Profiler | Planned | Age, TLD, DNS, typosquat detection |
| 4 | Content Snapshot Analyzer | Planned | Safe headless fetch, fake login detection |
| 5 | Email Auth Checker | Planned | SPF/DKIM/DMARC validation |
| 6 | Attachment Triage | Planned | Static file analysis and URL extraction |
| 7 | QR / Smishing Decoder | Planned | Decode QR payloads and re-analyze URLs |
| 8 | Password Hygiene | Planned | Local strength and reuse checks |
| 9 | Family Mode Explainer | Planned | Plain-language explanation layer |
| 10 | Offline Inbox Scanner | Planned | Batch scan exported mailbox data |

## Project Structure

```text
link-safety-hub/
  src/lsh/
    core/
    adapters/
    modules/
      homoglyph/
  tests/
    modules/
  docs/
  SESSION_LOG.md
```

## Development

```bash
# Lint
ruff check src/ tests/

# Type check
mypy src/

# Tests
pytest -v --tb=short
```

## Session Logging

Every coding session appends an entry to `SESSION_LOG.md` with:

- goal
- files touched
- decisions with reasoning
- open questions
- next steps

## Documentation

- Architecture: `docs/ARCHITECTURE.md`
- Module specs: `docs/MODULES.md`
- Build plan: `docs/ROADMAP.md`
- Security guidance: `docs/SECURITY.md`

## License

MIT
