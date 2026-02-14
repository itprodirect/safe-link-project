# Architecture

## Design Philosophy

**Core principle:** Every component is useful alone, but they compose cleanly.

This means no module should import from another module. Modules only depend on `lsh.core`. The adapters (CLI, API, web) orchestrate modules — modules never orchestrate each other.

```
┌─────────────────────────────────────────────────┐
│                  ADAPTERS                         │
│   CLI  │  Web API  │  Browser Ext  │  Share Sheet │
└────────┬────────────┬──────────────┬─────────────┘
         │            │              │
         ▼            ▼              ▼
┌─────────────────────────────────────────────────┐
│               ORCHESTRATOR                       │
│  Routes input → relevant modules → merges output │
└────────┬────────────────────────────────────────┘
         │
    ┌────┴────┬────────┬────────┬────────┐
    ▼         ▼        ▼        ▼        ▼
┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐
│Homoglyph││Redirect││Email   ││QR      ││ ...    │
│Detector ││Expander││Auth    ││Decoder ││        │
└────┬───┘└───┬────┘└───┬────┘└───┬────┘└───┬────┘
     │        │         │         │          │
     ▼        ▼         ▼         ▼          ▼
┌─────────────────────────────────────────────────┐
│                 CORE ENGINE                      │
│  Models  │  Scorer  │  Rules  │  Explanations    │
└─────────────────────────────────────────────────┘
```

## Core Engine

### Models (`src/lsh/core/models.py`)

All data flows through Pydantic models. This is non-negotiable — it keeps every module's output structured and serializable.

```python
class AnalysisInput(BaseModel):
    """What goes into a module."""
    input_type: Literal["url", "email_headers", "email_file", "qr_image", "text"]
    content: str           # The raw input (URL string, file path, header text, etc.)
    metadata: dict = {}    # Optional context (source app, timestamp, etc.)

class Finding(BaseModel):
    """What comes out of a module."""
    module: str            # Which module produced this
    category: str          # e.g., "homoglyph", "redirect", "spf_fail"
    severity: Severity     # CRITICAL, HIGH, MEDIUM, LOW, INFO
    risk_score: int        # 0-100, normalized by scorer
    title: str             # One-line summary
    explanation: str       # Technical explanation
    family_explanation: str # Plain-English version (filled by Family Mode or module)
    evidence: list[Evidence] = []
    recommendations: list[str] = []

class Evidence(BaseModel):
    """Supporting data for a finding."""
    label: str             # e.g., "Punycode decoded"
    value: str             # e.g., "xn--pple-43d.com → аpple.com"

class AnalysisResult(BaseModel):
    """Aggregated output from the orchestrator."""
    input: AnalysisInput
    findings: list[Finding]
    overall_risk: int      # Highest individual score (not averaged)
    overall_severity: Severity
    summary: str           # One-paragraph summary
    analyzed_at: datetime
```

### Scorer (`src/lsh/core/scorer.py`)

The scorer normalizes raw module signals into the 0-100 scale. Modules can suggest a score, but the scorer has final say. This prevents score inflation from aggressive modules.

Severity mapping: 0-20 INFO, 21-40 LOW, 41-60 MEDIUM, 61-80 HIGH, 81-100 CRITICAL.

### Rules (`src/lsh/core/rules.py`)

Shared detection patterns used by multiple modules. Examples: known phishing TLDs, brand name lists for impersonation detection, common redirect services.

## Module Contract

Every module must:

1. Implement `ModuleInterface` (see CLAUDE.md for the ABC)
2. Accept `AnalysisInput` and return `list[Finding]`
3. Have zero side effects (no writing files, no storing state)
4. Handle its own errors gracefully (return a Finding with `category="error"` rather than raising)
5. Include a `README.md` describing what it detects and its limitations
6. Be independently testable with no network access required (use fixtures)

## Orchestrator

The orchestrator is the "smart router." Given an input, it decides which modules are relevant and runs them.

```python
# Pseudocode
def analyze(input: AnalysisInput) -> AnalysisResult:
    relevant = select_modules(input.input_type)
    findings = []
    for module in relevant:
        findings.extend(module.analyze(input))
    findings = scorer.normalize(findings)
    findings = family_mode.enrich(findings)  # Add plain-English explanations
    return AnalysisResult(findings=findings, ...)
```

Input type → module routing:

| Input Type | Modules Run |
|-----------|-------------|
| `url` | #1 Homoglyph, #2 Redirect, #3 Domain Risk, #4 Content Snapshot |
| `email_headers` | #5 Email Auth |
| `email_file` | #5 Email Auth, #6 Attachment Triage, #1 Homoglyph (on links in body) |
| `qr_image` | #7 QR Decode → then re-analyze extracted URL as `url` type |
| `text` | #1 Homoglyph (on any URLs found), #2 Redirect (on any URLs found) |

## Adapter Pattern

Adapters are thin wrappers. They handle I/O (terminal, HTTP, browser message passing) and delegate everything to the orchestrator. An adapter should never contain detection logic.

### CLI Adapter (Phase 1)

```
lsh check <url>                    # Analyze a URL
lsh email-check <headers_file>     # Check email authentication
lsh qr-scan <image_file>           # Decode and analyze QR code
lsh inbox-scan <mbox_file>         # Batch scan exported mailbox
lsh check <url> --json             # Machine-readable output
lsh check <url> --family           # Family-friendly output only
```

### API Adapter (Phase 2)

Simple REST API (FastAPI) with the same input/output models. Enables the web app and browser extension.

### Web Adapter (Phase 2)

Next.js frontend that calls the API adapter. "Paste a link, drop a QR screenshot, or upload email headers."

## Data Flow Example: Checking a Shortened URL

```
User pastes: https://bit.ly/3xF4k3

1. CLI adapter creates AnalysisInput(type="url", content="https://bit.ly/3xF4k3")
2. Orchestrator selects: Homoglyph, Redirect, Domain Risk
3. Redirect module follows chain:
   bit.ly/3xF4k3 → tracking.evil.com/redir → login-paypa1.com/secure
4. Homoglyph module checks final URL: "paypa1" uses digit "1" for letter "l"
5. Domain Risk module checks: login-paypa1.com registered 2 days ago
6. Scorer normalizes: Redirect=INFO, Homoglyph=HIGH(75), Domain=CRITICAL(90)
7. Family Mode enriches: "This link pretends to be PayPal but isn't.
   The website was created 2 days ago. Do NOT enter any information.
   If you think it's real, open PayPal directly from your browser."
8. CLI adapter displays formatted output
```

## Future: Go Port Strategy

The ChatGPT plan mentions porting to Go for distribution. The recommended approach:

1. Keep Python as the "research and prototyping" layer permanently
2. Port only the core engine + high-traffic modules to Go when there's a real distribution need (single binary for non-technical users)
3. Use the same Pydantic models as the Go struct definitions (generate Go structs from JSON Schema)
4. Don't port until Phase 2 is stable — premature optimization of language choice is a trap
