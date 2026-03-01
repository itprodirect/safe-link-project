# Link Safety Hub

Modular, local-first security CLI for analyzing suspicious links and email headers and giving clear next steps.

## Current Status (2026-03-01)

Implemented now:

- Core contracts, scoring, allowlist logic, and URL utilities in `src/lsh/core/`
- Dedicated orchestrator layer in `src/lsh/core/orchestrator.py`
- URL normalization and adversarial parsing helpers in `src/lsh/core/normalizer.py`
- Shared per-analysis URL runtime context/preprocessing cache in `src/lsh/core/context.py`
- Input-aware module routing in orchestrator (`supported_input_types` + orchestrator-side filtering)
- CLI adapter in `src/lsh/adapters/cli.py`
- Minimal FastAPI adapter in `src/lsh/adapters/api.py` (optional dependency)
- Reusable family formatter layer in `src/lsh/formatters/family.py`
- Reusable structured response wrappers in `src/lsh/formatters/structured.py`
- URL-focused offline modules:
  - `homoglyph` (Unicode/IDN spoofing)
  - `ascii_lookalike` (ASCII glyph and leet brand lookalikes)
  - `url_structure` (`@` userinfo, deceptive subdomains, nested URLs, fragment deception, suspicious encoding)
  - `net_ip` (private/public IP literals plus obfuscated IP formats, localhost aliases, IPv6-mapped IPv4)
- Opt-in network module:
  - `redirect` (HEAD-only redirect chain analysis with hop/timeout safeguards)
- Email-auth module:
  - `email_auth` (local SPF/DKIM/DMARC header signal analysis)
- QR decode module + CLI handoff:
  - `qr_decode` helpers for local QR payload decoding
  - `lsh qr-scan <image>` to decode and run decoded URLs through the existing URL pipeline
- Two output modes:
  - Technical (default): finding codes, evidence-driven categories
  - Family (`--family`): plain-language summary and safer actions
- JSON output for machine-readable integrations (`--json`)
- Adversarial regression coverage (obfuscated IPs, fragment deception, encoding evasion)
- Aggregate scoring policy clarified: overall risk is `risk_score`-based; `confidence` is for trust-calibration messaging

Not implemented yet:

- Production deployment validation on a hosted environment
- Frontend UI implementation

## Quick Start

### Install (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

### Install (Git Bash on Windows / macOS / Linux)

```bash
python -m venv .venv
source .venv/Scripts/activate  # Git Bash on Windows
# source .venv/bin/activate    # macOS / Linux
python -m pip install -e ".[dev]"
```

## Golden Path

```bash
# URL checks (technical)
lsh check "http://google.com:80@evil.com"

# JSON output (Windows-safe: Unicode is ASCII-escaped)
lsh check --json "https://ｅxample.com"

# Email header file analysis (CLI uses positional path + --file; no --headers-file flag)
lsh email-check headers.txt --file --json

# QR scan -> analyze first decoded URL payload
lsh qr-scan suspicious-qr.png --json

# Analyze all decoded URL payloads
lsh qr-scan suspicious-qr.png --all --family
```

### Optional API Adapter

```bash
# Install API extras
python -m pip install -e ".[api]"

# Run local API
uvicorn lsh.adapters.api:app --host 127.0.0.1 --port 8000
```

Current endpoints:

- `GET /health`
- `POST /api/v1/url/check`
- `POST /api/v1/email/check`
- `POST /api/v1/qr/scan`

Contract and integration notes: `docs/API_INTEGRATION.md`

### Container Baseline

```bash
# Build API image
docker build -t link-safety-hub-api:local .

# Run API container
docker run --rm -p 8000:8000 link-safety-hub-api:local
```

Deployment runbook: `docs/DEPLOYMENT.md`

### Quick Smoke Examples

```powershell
lsh check https://example.com
lsh check https://xn--pple-43d.com --family
```

## CLI Usage

```bash
lsh check <url> [--json] [--family] [--network] [--max-hops N] [--timeout SECONDS] [--allowlist-domain DOMAIN ...] [--allowlist-file FILE ...] [--allowlist-category {HMG,ASCII,URL,NET,ALL} ...]
lsh email-check <headers_or_file> [--json] [--family] [--file]
lsh qr-scan <image_path> [--json] [--family] [--all]
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

# Opt-in redirect-chain checks (HEAD only)
lsh check "https://bit.ly/example" --network --max-hops 5 --timeout 3.0

# Email header authentication analysis
lsh email-check headers.txt --file --json

# QR scan -> URL analysis (first decoded URL payload by default)
lsh qr-scan suspicious-qr.png --json

# Analyze every decoded URL payload in the image
lsh qr-scan suspicious-qr.png --all --family
```

## Detection Categories (Current)

- `HMG*`: Unicode/IDN homoglyph risk signals
- `ASCII*`: ASCII lookalike brand-style signals
- `URL*`: URL-structure deception signals (`URL001`-`URL005`)
- `NET*`: IP literal and obfuscated-IP network-scope signals (`NET001`-`NET006`)
- `RED*`: opt-in redirect-chain signals
- `EML*`: email authentication header signals (SPF/DKIM/DMARC)

Notes:

- Registrable-domain checks use offline heuristics for common country-code suffix patterns.
- URL hardening helpers live in `src/lsh/core/normalizer.py`.
- Orchestrator now builds one shared URL runtime context per analysis (including normalized/canonical URL data); all URL detectors use it (`net_ip`, `url_structure`, `ascii_lookalike`, `homoglyph`).
- Overall risk aggregation uses finding `risk_score` values only; `confidence` is shown to users and used for messaging, not aggregate math.

## Common Issues

- `make: command not found` (common on Windows):
  - Use direct commands instead: `python -m pytest -q`, `ruff check .`, `mypy .`
- Redirect checks did not run:
  - Network checks are off by default. Enable redirect analysis with `--network`.
- `qr-scan` says the QR decoder/backend is unavailable:
  - QR scanning depends on `Pillow` + `pyzbar`, and `pyzbar` also requires a system `zbar` backend.
  - The CLI returns a friendly error; URL and email commands still work normally.
- JSON output shows escaped Unicode (for example `\uff45`) on Windows:
  - This is intentional for console safety on non-UTF terminals (such as `cp1252`) and still produces valid JSON.

## P1 False-Positive Controls

- `confidence` label on each finding (`LOW`, `MEDIUM`, `HIGH`)
- `--allowlist-domain` to suppress domain-lookalike findings for known-safe domains
- `--allowlist-file` for shared/team allowlist inputs
- `--allowlist-category` for scoped suppression (`HMG`, `ASCII`, `URL`, `NET`, `ALL`)
- Redirect findings (`RED*`) are intentionally not suppressed by allowlist in this phase
- Family mode now prints `Signal confidence` and uses confidence-aware summary wording

## Project Structure

```text
safe-link-project/
  src/lsh/
    adapters/
      cli.py
    core/
      allowlist.py
      context.py
      models.py
      normalizer.py
      orchestrator.py
      rules.py
      scorer.py
      url_tools.py
    formatters/
      family.py
    modules/
      ascii_lookalike/
      email_auth/
      homoglyph/
      net_ip/
      qr_decode/
      redirect/
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

# Type check (stricter local pass)
mypy src tests

# Run tests
pytest -v --tb=short

# One command gate
make check

# Dependency audit
make audit
```

Notes:

- `make` targets are Unix-style; on Windows PowerShell, run the underlying `ruff` / `mypy` / `pytest` commands directly unless using WSL/Git Bash.
- CI currently type-checks `src/` and runs tests with `-m "not network"`.

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

Canonical project docs live under `docs/` (planning docs were de-duplicated from the repo root).

- Architecture: `docs/ARCHITECTURE.md`
- Module specs: `docs/MODULES.md`
- API integration contract: `docs/API_INTEGRATION.md`
- Deployment baseline: `docs/DEPLOYMENT.md`
- Next.js validation checklist: `docs/NEXTJS_UI_VALIDATION.md`
- Roadmap: `docs/ROADMAP.md`
- Plan review and risks: `docs/PLAN_REVIEW.md`
- Security and responsible use: `docs/SECURITY.md`
- GitHub workflow strategy: `docs/GITHUB_STRATEGY.md`

Agent workflow docs:

- `CLAUDE.md`
- `SKILL.md`

## License

MIT
