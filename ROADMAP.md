# Roadmap

## Phase 1: Personal CLI Toolbelt (Target: 2-3 weeks)

The goal is a working `lsh` CLI that you can use on your own machine to check links, decode QR codes, and verify email headers. Everything runs locally with no server.

### Quickstart: First 3 Sessions

These are the first three coding sessions. Each has a clear goal and definition of done. Do them in order.

**Session 0 — "Repo turns green"**

Goal: CI passes with a working CLI skeleton. No real detection yet.

- Create `src/lsh/__init__.py` and full package skeleton
- Create `src/lsh/adapters/cli.py` with Click: `lsh --help` and `lsh check <url>` (stub)
- Create `src/lsh/core/models.py` (Pydantic models: `AnalysisInput`, `Finding`, `Evidence`, `AnalysisResult`)
- Create `src/lsh/core/scorer.py` (stub that returns "no findings yet")
- Add `tests/test_smoke.py` (assert CLI runs, models validate, basic output)
- Write first real session log entry in `SESSION_LOG.md`

Definition of done: `pip install -e ".[dev]"` works, `make check` passes, `lsh --help` prints help, `lsh check https://example.com` returns a structured (stub) result.

**Session 1 — Homoglyph/IDN detector vertical slice**

Goal: `lsh check` flags obvious IDN/homoglyph risks without any network calls.

- Implement `src/lsh/modules/homoglyph/analyzer.py` with punycode visibility + Unicode script analysis
- Output: score, severity, family explanation, evidence
- 5 tests: 2 known-bad (defanged phishing domains), 2 known-good (normal domains), 1 edge case (mixed scripts)

Definition of done: `lsh check "https://xn--pple-43d.com"` produces a HIGH/CRITICAL finding with evidence.

**Session 2 — Redirect expander with strict safety**

Goal: `lsh check --network` expands redirects (HEAD only) and shows the chain.

- Default behavior: no network (offline analysis only)
- Add `--network` flag, `--max-hops`, timeouts
- Mark tests `@pytest.mark.network` and skip in CI
- 5 tests: 2 with mocked redirect chains, 2 direct URLs, 1 timeout edge case

Definition of done: `lsh check "https://bit.ly/example" --network` shows the full redirect chain with risk assessment.

### Remaining Build Order

```
Week 1: Foundation (Sessions 0-2 above)
├── Session logger installed and first entry committed
├── Core engine: models.py, scorer.py, rules.py
├── Module #1: Homoglyph / IDN Detector
├── Module #2: Redirect Chain Expander
└── Tests + fixtures for both

Week 2: Email + QR
├── Module #5: Email Auth Checker (SPF/DKIM/DMARC)
├── Module #7: QR Code Decoder (image → URL → pipeline)
├── Module #9: Family Mode Explainer (presentation layer)
└── CLI adapter enhancements (new subcommands)

Week 3: Polish
├── Integration tests (full pipeline: URL in → explanation out)
├── README examples with real output
├── CI pipeline on GitHub Actions
└── Tag v0.1.0
```

### Definition of Done (Phase 1)

- [ ] `lsh check <url>` produces a risk score + explanation
- [ ] `lsh email-check <file>` validates SPF/DKIM/DMARC from headers
- [ ] `lsh qr-scan <image>` extracts URL and runs it through the pipeline
- [ ] `--family` flag produces plain-English output on all commands
- [ ] `--json` flag produces machine-readable output on all commands
- [ ] All modules have >80% test coverage
- [ ] CI passes on every PR

## Phase 2: Family Web App (Target: 3-4 weeks after Phase 1)

Wrap the same core in a mobile-friendly web interface. This is where "normal people" will actually use it.

### Scope

- FastAPI backend exposing the orchestrator
- Next.js frontend with three input modes: paste URL, upload QR screenshot, paste email headers
- Family Mode is the default view (technical details available on toggle)
- No authentication required (it's a tool, not a service)
- Deploy on a VPS or Railway for family/small-biz access

### Build Order

```
Week 1: API
├── FastAPI adapter wrapping the orchestrator
├── OpenAPI spec auto-generated from Pydantic models
└── API tests

Week 2-3: Frontend
├── Next.js app with input forms
├── Results display with risk visualization
├── Mobile-responsive design
└── QR scanner via camera (optional, webcam API)

Week 4: Deploy
├── Docker Compose (API + frontend)
├── Basic rate limiting
├── Deploy to staging
└── Tag v0.2.0
```

## Phase 3: Inbox + QR Workflows (Target: 3-4 weeks after Phase 2)

### Scope

- Module #10: Offline Inbox Scanner (mbox/eml parsing → batch analysis → cleanup queue)
- Module #7 enhancement: Live camera QR scanning in web app
- Module #3: Domain Risk Profiler (WHOIS, DNS, age checks)
- Batch processing mode for the CLI

### Key Risk

Inbox scanning is the highest-value but most complex module. It needs to handle malformed emails, encodings, and large files gracefully. Budget extra time here.

## Phase 4: Harden + Distribute (Target: ongoing after Phase 3)

### Scope

- Module #4: Content Snapshot Analyzer
- Module #6: Attachment Triage
- Module #8: Password Hygiene
- Go port of core engine for single-binary distribution (evaluate need first)
- Browser extension adapter
- Documentation site

### Decision Gate

Before starting Go port, answer: "Do I actually need a single binary, or is a Docker container sufficient for my distribution needs?" If Docker is fine, skip the Go port and invest that time in features.

## Parking Lot (Ideas to evaluate later)

- Threat intelligence feed integration (PhishTank, URLhaus)
- VirusTotal API integration for attachment hashes
- Browser extension that checks links before you click
- Slack/Discord bot adapter
- Integration with Have I Been Pwned API for breach checks
- LLM-powered explanation generation (instead of template-based Family Mode)
