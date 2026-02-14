# Link Safety Hub

A modular security toolbelt for inspecting links, messages, emails, and QR codes. Built for personal use, family protection, and small business security hygiene.

Each module works standalone via CLI, but shares a common core engine so they compose into a unified web app, browser extension, or inbox scanner as the project matures.

## Why This Exists

Normal people get compromised through everyday vectors: shortened links in texts, spoofed emails, QR codes at restaurants, and old inboxes full of phishing. Enterprise tools don't help individuals or family businesses. This project fills that gap with plain-English explanations and practical "what to do next" advice.

## Quick Start

```bash
# Clone and install
git clone https://github.com/YOUR_USERNAME/link-safety-hub.git
cd link-safety-hub
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"

# Check a URL
lsh check https://suspicious-link.example.com

# Check an email header file
lsh email-check headers.txt

# Scan a QR code image
lsh qr-scan screenshot.png
```

## Modules

| # | Module | Status | Description |
|---|--------|--------|-------------|
| 1 | **Homoglyph / IDN Detector** | 🟡 MVP | Detects lookalike characters and punycode tricks |
| 2 | **Redirect Chain Expander** | 🟡 MVP | Safely unwinds shortened URLs, shows every hop |
| 3 | **Domain Risk Profiler** | ⚪ Planned | Age, TLD, DNS, typosquat detection |
| 4 | **Content Snapshot Analyzer** | ⚪ Planned | Safe headless fetch, fake login form detection |
| 5 | **Email Auth Checker** | 🟡 MVP | SPF/DKIM/DMARC validation from headers |
| 6 | **Attachment Triage** | ⚪ Planned | Static file analysis, hash, macro detection |
| 7 | **QR / Smishing Decoder** | 🟡 MVP | Extract links from QR codes, run through pipeline |
| 8 | **Password Hygiene** | ⚪ Planned | Local-only strength and reuse checks |
| 9 | **Family Mode Explainer** | 🟡 MVP | Plain-English risk explanations and action steps |
| 10 | **Offline Inbox Scanner** | ⚪ Planned | Batch scan exported .mbox/.eml files |

## Project Structure

```
link-safety-hub/
├── .claude/
│   └── skills/
│       └── session-logger/       # Session logging skill for Claude Code
│           ├── SKILL.md
│           └── assets/
│               └── entry.template.md
├── src/
│   └── lsh/
│       ├── core/              # Shared engine: scoring, parsing, rules
│       │   ├── __init__.py
│       │   ├── models.py      # Pydantic models for findings, risk scores
│       │   ├── scorer.py      # Risk scoring engine
│       │   └── rules.py       # Shared detection rules
│       ├── modules/           # Each module is a self-contained package
│       │   ├── homoglyph/
│       │   ├── redirect/
│       │   ├── domain_risk/
│       │   ├── content_snapshot/
│       │   ├── email_auth/
│       │   ├── attachment/
│       │   ├── qr_decode/
│       │   ├── password/
│       │   ├── family_mode/
│       │   └── inbox_scanner/
│       ├── adapters/          # Interface adapters (CLI, API, etc.)
│       │   ├── cli.py
│       │   ├── api.py
│       │   └── web.py
│       └── __init__.py
├── tests/
│   ├── core/
│   ├── modules/
│   └── fixtures/              # Sample emails, URLs, QR images for testing
├── docs/
│   ├── ARCHITECTURE.md
│   ├── MODULES.md
│   ├── GITHUB_STRATEGY.md
│   └── SECURITY.md
├── CLAUDE.md                  # Agent context for Claude Code / Codex
├── SESSION_LOG.md             # Structured development session history
├── pyproject.toml
├── Makefile
└── README.md
```

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full design, including the core engine, module interface contract, and adapter pattern.

## Development

```bash
# Run tests
make test

# Run linting
make lint

# Run a single module's tests
pytest tests/modules/test_homoglyph.py -v

# Type checking
make typecheck
```

## Session Logging

This project uses structured session logging to maintain continuity across multiple developers and AI coding agents (Claude Code, Codex, etc.). Every session appends an entry to `SESSION_LOG.md` with changes, decisions (with reasoning), open questions, and next steps.

To log a session in Claude Code: type `/session-logger` or say "log this session".

See `.claude/skills/session-logger/SKILL.md` for the full format and conventions.

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md) for the phased build plan.

## Ethics & Legal

This tool is for **defensive security only**. Never scan accounts, emails, or devices you don't own or have explicit written permission to analyze. See [docs/SECURITY.md](docs/SECURITY.md) for responsible use guidelines.

## License

MIT
