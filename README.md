# Link Safety Hub

Modular, local-first security CLI for analyzing suspicious links and giving clear next steps.

## Current Status (2026-02-16)

Implemented now:

- Core models and scoring in `src/lsh/core/`
- Dedicated orchestrator layer in `src/lsh/core/orchestrator.py`
- CLI adapter in `src/lsh/adapters/cli.py`
- URL-focused offline modules:
  - `homoglyph` (Unicode/IDN spoofing)
  - `ascii_lookalike` (ASCII glyph and leet brand lookalikes)
  - `url_structure` (`@` userinfo tricks, deceptive subdomains, nested URL params)
  - `net_ip` (private/public IP literal host detection)
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
lsh check <url> [--json] [--family] [--allowlist-domain DOMAIN ...] [--allowlist-file FILE ...] [--allowlist-category {HMG,ASCII,URL,NET,ALL} ...]
```

Examples:

```bash
# Technical output
lsh check https://xn--pple-43d.com

# Plain-language output
lsh check https://xn--pple-43d.com --family

# JSON output
lsh check https://xn--pple-43d.com --json

# URL structure trick
lsh check "http://google.com:80@evil.com"

# Nested redirect-style query param
lsh check "https://example.com/redirect?url=https://google.com"

# Suppress expected lookalike findings for trusted domains
lsh check "https://paypaI.com" --allowlist-domain paypai.com

# Load allowlist domains from file (one domain per line; # comments supported)
lsh check "https://paypaI.com" --allowlist-file allowlist.txt

# Suppress only selected categories for allowlisted domains
lsh check "https://paypaI.com" --allowlist-domain paypai.com --allowlist-category HMG
```

## Detection Categories (Current)

- `HMG*`: Unicode/IDN homoglyph risk signals
- `ASCII*`: ASCII lookalike brand-style signals
- `URL*`: URL-structure deception signals
- `NET*`: IP literal network-scope signals

## P1 False-Positive Controls

- `confidence` label on each finding (`LOW`, `MEDIUM`, `HIGH`)
- `--allowlist-domain` to suppress domain-lookalike findings for known-safe domains
- `--allowlist-file` for shared/team allowlist inputs
- `--allowlist-category` for scoped suppression (`HMG`, `ASCII`, `URL`, `NET`, `ALL`)
- Family mode now prints `Signal confidence` and uses confidence-aware summary wording

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
      ascii_lookalike/
      homoglyph/
      net_ip/
      url_structure/
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
