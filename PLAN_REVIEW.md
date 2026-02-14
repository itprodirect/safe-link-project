# Plan Review: Gaps, Risks & Corrections

This document captures things the original ChatGPT plan got right, got wrong, or didn't address. Read this before building.

## What the plan gets right

- **Modularity-first approach.** Building standalone modules that compose is exactly the right pattern for a security toolbelt.
- **Family Mode as a first-class concern.** Most security tools fail because they scare non-technical users without telling them what to do. Making explainability a core module is a strong call.
- **Python for MVP.** Don't overthink language choice at the start. Python has the best library ecosystem for email parsing, HTTP, and QR decoding.
- **Offline-first for sensitive data.** Scanning email exports locally rather than piping them through a web service is the right trust model.
- **The "5 module starter" recommendation (#1, #2, #5, #7, #10) is solid**, though I'd swap #10 for #9 in the first pass — #10 is the most complex module and you need Family Mode before Inbox Scanner.

## What needs correction

### 1. The scaffold is docs-perfect but will fail CI

This is the most immediate issue. The `pyproject.toml` declares a `lsh` CLI entry point and `src/lsh` package structure, but none of those files exist yet. Running `pip install -e .` will fail, `make check` will fail, and any agent starting a session will be confused by the gap between documentation and reality.

**Fix:** Session 0 (see ROADMAP.md) creates the minimum package skeleton so CI turns green before any real module work begins. This must be the very first coding session.

**Also fixed:** The original `pyproject.toml` used self-referential extras (`phase1 = ["link-safety-hub[homoglyph,qr,email-auth]"]`) which can break in editable installs. The `[dev]` extra now lists all dependencies flat.

### 2. Multi-repo is wrong for this project

The plan implies building modules separately and combining "when the time is right." This creates dependency hell with the shared core engine. **Use a monorepo** with clear internal package boundaries. You can always extract later; combining separate repos is painful.

See [GITHUB_STRATEGY.md](GITHUB_STRATEGY.md) for the full rationale.

### 3. The complexity estimates are optimistic

The "2-6 hours for MVP" estimates assume you already have the core engine, test infrastructure, and CLI wired up. Realistically:

| Item | ChatGPT Estimate | More Realistic |
|------|------------------|----------------|
| Core engine (models, scorer, rules) | Not estimated | 1-2 days |
| Homoglyph detector | 2-6 hrs | 4-8 hrs (Unicode edge cases are gnarly) |
| Redirect expander | 4-10 hrs | 1-2 days (timeout handling, shortener quirks) |
| Email auth checker | 1-2 days | 2-3 days (RFC 2822 parsing is a swamp) |
| Offline inbox scanner | 3-7 days | 1-2 weeks (encoding issues, malformed emails) |

These are still MVP estimates. The core engine is the hidden dependency — nothing works without it, and it wasn't explicitly called out in the original plan.

### 4. "Go later" is probably "Go never" (and that's fine)

The plan suggests porting to Go for single-binary distribution. In practice:

- Docker solves the distribution problem without a rewrite
- The Python ecosystem for email/HTTP/QR is vastly richer than Go's
- A Go rewrite is only justified if you need to ship a binary to machines without Python/Docker (unlikely for your use case)

**Recommendation:** Keep Go in the parking lot. If you need it, you'll know.

### 5. Mojo was mentioned — ignore it entirely

The ChatGPT conversation apparently touched on Mojo. For a security utility project, Mojo adds zero value. It's an immature language with no library ecosystem relevant to your needs. Python, Go, and Rust are the only languages worth considering here.

### 6. The scoring system needs more thought

The plan uses a 1-5 scale per module. That's fine for human comparison, but the actual tool needs a consistent 0-100 scoring system with clear severity bands. More importantly, you need to answer: **what happens when multiple modules flag the same URL?**

Options:
- **Max score wins** (simple, conservative) — recommended for MVP
- **Weighted average** (more nuanced, harder to explain)
- **Compound scoring** (multiple flags increase severity) — best but complex

Start with max-score-wins. It's easy to explain to users and hard to game.

### 7. Rate limiting and abuse potential aren't addressed

If you eventually expose this as a web app, consider:
- Someone could use your redirect expander as a URL scanner/scraper
- The content snapshot module could be abused to probe websites
- Batch inbox scanning could generate heavy DNS lookups

Mitigations: rate limit per IP, require a simple captcha for web access, add request logging (for your own monitoring, not user surveillance).

## What's not addressed at all

### A. Session Logging and Multi-Agent Continuity

The original plan doesn't address how to maintain context across coding sessions, especially when using multiple AI agents (Claude Code, Codex, manual coding). This is a real problem: you start a Claude Code session, build half a module, then come back the next day with Codex and have no idea what state things are in.

**Solution:** The `session-logger` skill (from itprodirect/session-logger, adapted for this project) enforces structured logging at the end of every session. Each entry captures changes, decisions with reasoning, open questions, and next steps. The log lives in `SESSION_LOG.md` at the project root.

Key adaptations for this project:
- Added "Agent" field — tracks which AI tool did the work
- Added "Module(s) Touched" — maps sessions to the modular architecture
- Added "Tests" status — because a security tool without tests is a liability
- Open questions carry forward — unresolved items from past sessions don't get lost

This is a workflow discipline, not just a tool. Every session, every agent, every time.

### B. Testing strategy for security tools

Security tools need adversarial test cases, not just happy-path tests. For each module, you need:
- **Known-bad fixtures:** Real phishing URLs (defanged), spoofed email headers, malicious QR codes
- **Known-good fixtures:** Legitimate URLs with unusual characteristics (new domains, international domains)
- **Evasion tests:** Inputs specifically designed to bypass detection (double-encoding, mixed-case punycode, etc.)

Sources for test fixtures:
- PhishTank (public phishing URL database)
- Your own spam folder (export and sanitize)
- OWASP testing guides for URL manipulation patterns

### C. False positive management

The plan doesn't discuss false positives at all. This matters because:
- New legitimate domains will trigger Domain Risk
- International businesses with IDN domains will trigger Homoglyph
- Small business email without DMARC will trigger Email Auth

You need a way to suppress known-good findings. Options:
- Per-user allowlist (domain or URL pattern)
- Confidence levels on findings ("possible" vs "confirmed")
- "This looks suspicious but could be legitimate" as a distinct output category

### D. Dependency security

You're building a security tool that depends on third-party packages. Those packages could themselves be compromised. Mitigations:
- Pin all dependency versions in a lockfile
- Use `pip-audit` to check for known vulnerabilities
- Minimize dependencies — for the core engine, prefer stdlib over PyPI packages
- Add `pip-audit` to your CI pipeline

### E. Legal considerations for URL scanning

Making HTTP requests to URLs could technically trigger:
- ToS violations on the destination site
- Alerts in the destination site's security monitoring
- Legal issues in some jurisdictions if the URL belongs to a sensitive entity

Mitigations:
- Use a descriptive User-Agent so site operators understand what's happening
- Never bypass authentication or access controls
- HEAD requests only for redirect expansion
- Don't cache or store response content
- Add a clear disclaimer in SECURITY.md (already done)

### F. What "compromised email cleanup" actually involves

The plan mentions this as a use case but underestimates the scope. A real cleanup workflow needs:
1. Export email to .mbox
2. Scan for phishing/malicious content (Module #10)
3. Scan for forwarding rules an attacker may have set (not covered by any module)
4. Check for OAuth app permissions the attacker granted (not covered)
5. Review sent mail for messages the attacker sent from the account (not covered)
6. Account recovery (password, MFA, recovery contacts)

Modules #10 can handle step 2. Steps 3-5 require different tooling (API access to the email provider, not just .mbox parsing). This should be documented as a limitation.

## Recommended changes to the module priority list

Original order: #1, #2, #5, #7, #10

Revised order: **#1, #2, #5, #7, #9** (swap #10 for #9 in Phase 1)

Reasoning:
- #9 (Family Mode) makes every other module useful to non-technical users immediately
- #10 (Inbox Scanner) is the most complex module and benefits from having all other modules stable first
- #10 also benefits from the orchestrator being battle-tested on individual URLs before handling batch processing
