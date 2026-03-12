# Link Safety Hub

Modular, local-first security CLI for analyzing suspicious links and email headers and giving clear next steps.
Security-first, practical, and intentionally plain-spoken.

## Run Locally

```bash
# Backend
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash
# source .venv/bin/activate     # macOS / Linux
pip install -e ".[dev]"
uvicorn lsh.adapters.api:app --host 127.0.0.1 --port 8000

# Frontend (separate terminal)
cd ui
npm install
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run dev
# opens http://localhost:3000

# Tests
pytest -q                              # backend (230 tests)
ruff check src tests                   # lint
mypy src                               # type check
cd ui && npm run lint && npm run build  # frontend
```

## Current Functionality

**Backend API** (FastAPI, Python 3.11+):

| Route | Purpose |
|---|---|
| `GET /health` | Liveness probe |
| `POST /api/v1/url/check` | Analyze a URL for homoglyph/IDN tricks, ASCII lookalikes, suspicious structure, IP literals, and optional redirect-chain following |
| `POST /api/v1/email/check` | Analyze raw email authentication headers (SPF/DKIM/DMARC) |
| `POST /api/v1/qr/scan` | Upload a QR image, decode payloads, extract URLs, run URL analysis |
| `POST /api/v2/analyze` | Unified endpoint for URL, email_headers, and email_file input types with family summaries plus URL analyst projections; accepts optional `policy_id` for URL policy-pack application |
| `GET/POST /api/v2/policies` | List and create persisted policy packs |
| `GET/PUT/DELETE /api/v2/policies/{id}` | Read, update (full/partial), and delete one policy pack |

**CLI** (`lsh`): `check`, `email-check`, `qr-scan` commands with `--json`, `--family`, `--network`, and allowlist flags.

**Frontend** (Next.js at `ui/`):

| Page | Purpose |
|---|---|
| `/` | Landing page |
| `/url` | Standalone URL check |
| `/email` | Standalone email header check |
| `/qr` | Standalone QR scan |
| `/analyze` | Unified workspace with URL/Email/QR tabs, Quick mode (verdict-first UX) and URL Analyst mode (domain anatomy, redirect path, suppression trace, evidence panel) |

**Detection modules**: `homoglyph` (Unicode/IDN), `ascii_lookalike` (leet/brand), `url_structure` (deceptive patterns), `net_ip` (IP literals), `redirect` (opt-in redirect chains), `email_auth` (SPF/DKIM/DMARC), `qr_decode` (QR payload extraction).

## Current Status (2026-03-09)

Implemented now:

- Core contracts, scoring, allowlist logic, and URL utilities in `src/lsh/core/`
- Dedicated orchestrator layer in `src/lsh/core/orchestrator.py`
- URL normalization and adversarial parsing helpers in `src/lsh/core/normalizer.py`
- Shared per-analysis URL runtime context/preprocessing cache in `src/lsh/core/context.py`
- Input-aware module routing in orchestrator (`supported_input_types` + orchestrator-side filtering)
- Shared application service layer in `src/lsh/application/analysis_service.py` for adapter reuse
- CLI adapter in `src/lsh/adapters/cli.py`
- Minimal FastAPI adapter in `src/lsh/adapters/api.py` (optional dependency; QR upload route degrades gracefully when `python-multipart` is missing)
- Reusable family formatter layer in `src/lsh/formatters/family.py`
- Reusable structured response wrappers in `src/lsh/formatters/structured.py`
- Unified v2 endpoint (`POST /api/v2/analyze`) plus v1/v2 parity, analyst projections, policy-pack `policy_id` support, and edge-case test coverage
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
- Unified `/analyze` workspace with extracted Quick/Analyst result panels in `ui/app/analyze/`
- URL-first analyst payloads on `/api/v2/analyze` with domain anatomy, redirect path, suppression trace, and evidence rows
- Compare-ready analyst evidence/suppression keys (`finding_key`, `compare_key`, keyed evidence maps) for future history/delta views
- V2 execution artifacts and tracking:
  - blueprint: `docs/V2_BLUEPRINT.md`
  - roadmap/issues tracker: `docs/V2_ROADMAP_ISSUES.md`
  - GitHub epics/milestones: umbrella `#2`, phase epics `#3`-`#10`, child issues `#11`-`#12`

In progress and next:

- Hosted validation closure for Session 9 deployment checklist
- Email/QR analyst-mode parity beyond the current URL-first slice
- Persisted history/compare flows and hardening milestones (tracked in `docs/V2_ROADMAP_ISSUES.md`)

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

Optional CORS override for hosted UI origins:

```bash
LSH_API_CORS_ALLOW_ORIGINS=https://<your-ui-domain> uvicorn lsh.adapters.api:app --host 127.0.0.1 --port 8000
```

Optional QR legacy-key control for API integrations:

```bash
LSH_API_INCLUDE_QR_LEGACY_KEYS=false uvicorn lsh.adapters.api:app --host 127.0.0.1 --port 8000
```

Optional policy-store path override for persisted policy packs:

```bash
LSH_POLICY_STORE_DIR=.lsh uvicorn lsh.adapters.api:app --host 127.0.0.1 --port 8000
```

Current endpoints:

- `GET /health`
- `POST /api/v1/url/check`
- `POST /api/v1/email/check`
- `POST /api/v1/qr/scan` (`multipart/form-data` with uploaded file)
- `POST /api/v2/analyze` (unified single-item analyze endpoint; URL input accepts optional `policy_id`)
- `GET /api/v2/policies`
- `POST /api/v2/policies`
- `GET /api/v2/policies/{id}`
- `PUT /api/v2/policies/{id}`
- `DELETE /api/v2/policies/{id}`

Contract and integration notes: `docs/API_INTEGRATION.md`

### Container Baseline

```bash
# Build API image
docker build -t link-safety-hub-api:local .

# Run API container
docker run --rm -p 8000:8000 link-safety-hub-api:local
```

Deployment runbook: `docs/DEPLOYMENT.md`

### Current Next.js UI (Validation Surface)

```bash
cd ui
npm install
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

Contract smoke path:

```bash
cd ui
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 NEXT_PUBLIC_UI_ORIGIN=http://127.0.0.1:3000 npm run smoke:api
```

Browser smoke path for the unified `/analyze` workspace:

```bash
cd ui
npx playwright install chromium
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 NEXT_PUBLIC_UI_ORIGIN=http://127.0.0.1:3000 npm run build
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 NEXT_PUBLIC_UI_ORIGIN=http://127.0.0.1:3000 npm run start:smoke
# in another shell
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 NEXT_PUBLIC_UI_ORIGIN=http://127.0.0.1:3000 npm run smoke:e2e
```

Roadmap note: the current `ui/` app is a contract-validation surface, not the final product UX.
The full v2 experience plan lives in `docs/V2_BLUEPRINT.md`.

### Quick Smoke Examples

```powershell
lsh check https://example.com
lsh check https://xn--pple-43d.com --family
```

## CLI Usage

```bash
lsh check <url> [--json] [--family] [--network] [--max-hops N] [--timeout SECONDS] [--allowlist-domain DOMAIN ...] [--allowlist-file FILE ...] [--allowlist-category {HMG,ASCII,URL,NET,ALL,NONE} ...] [--allowlist-finding FINDING_CODE ...]
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

# Suppress only one finding code for an allowlisted domain
lsh check "https://xn--pple-43d.com" --allowlist-domain xn--pple-43d.com --allowlist-category NONE --allowlist-finding HMG002_PUNYCODE_VISIBILITY

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
- `--allowlist-category` for scoped suppression (`HMG`, `ASCII`, `URL`, `NET`, `ALL`, `NONE`)
- `--allowlist-finding` for per-rule suppression on allowlisted domains (exact code, stem, or `*` prefix match)
- Redirect findings (`RED*`) are intentionally not suppressed by allowlist in this phase
- Family mode now prints `Signal confidence` and uses confidence-aware summary wording

Confidence interpretation guide:

- `HIGH`: strong phishing-style signal; escalate review if unexpected.
- `MEDIUM`: suspicious pattern that needs source/context verification.
- `LOW`: weak/heuristic signal; useful for triage but higher false-positive likelihood.

## Project Structure

```text
safe-link-project/
  ui/
    app/
    lib/
    scripts/
  src/lsh/
    application/
      analysis_service.py
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
- CI runs Python checks (`ruff`, `mypy src/`, `pytest -m "not network"`), enforced dependency audit (`pip freeze --exclude-editable` + strict `pip-audit` on Python 3.11), UI checks (`npm run build`, `npm run typecheck`), and a Docker runtime smoke (`/health` + UI contract smoke against the running API container).

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
- Deployment options research: `docs/DEPLOYMENT_OPTIONS.md`
- Dependency-audit policy: `docs/DEPENDENCY_AUDIT.md`
- Next.js validation checklist: `docs/NEXTJS_UI_VALIDATION.md`
- Roadmap: `docs/ROADMAP.md`
- V2 blueprint: `docs/V2_BLUEPRINT.md`
- V2 roadmap and issue tracker: `docs/V2_ROADMAP_ISSUES.md`
- Plan review and risks: `docs/PLAN_REVIEW.md`
- Security and responsible use: `docs/SECURITY.md`
- GitHub workflow strategy: `docs/GITHUB_STRATEGY.md`

Agent workflow docs:

- `CLAUDE.md`
- `SKILL.md`

## License

MIT

