# Architecture

## Design Principle

Modules detect. Core orchestrates and scores. Adapters render.

## Implemented Architecture (2026-03-01)

### Core Layer (`src/lsh/core/`)

- `models.py`: canonical data contracts (`AnalysisInput`, `Finding`, `AnalysisResult`, `NormalizedURL`)
- `allowlist.py`: normalized domain allowlist helpers with category-prefix scoping
- `url_tools.py`: shared URL parsing and registrable-domain extraction (offline heuristics)
- `context.py`: shared runtime context/preprocessing cache for one analysis run (URL-focused today)
- `normalizer.py`: deterministic URL normalization helpers (percent-decoding, obfuscated IP parsing, localhost aliases, IPv6-mapped IPv4, path normalization)
- `scorer.py`: severity mapping, finding normalization, and compound aggregate risk calculation (`risk_score`-based; confidence is informational)
- `orchestrator.py`: module execution + aggregate result construction + confidence-aware summary text
- `rules.py`: shared detection constants for brand tokens, URL-parameter keys, suffix heuristics, and ASCII lookalikes

### Module Layer (`src/lsh/modules/`)

- `homoglyph/`: IDN/homoglyph risk detector (offline)
- `ascii_lookalike/`: ASCII glyph/leet brand lookalike detector (offline)
- `url_structure/`: URL deception-pattern detector (offline; includes fragment/encoding checks)
- `net_ip/`: IP literal and obfuscated-IP detector (offline)
- `redirect/`: opt-in redirect chain detector (HEAD-only network checks)
- `email_auth/`: local email header auth analyzer (SPF/DKIM/DMARC parsing)
- `qr_decode/`: local QR payload decode helpers + optional detector (used by CLI `qr-scan` URL handoff)

### Adapter Layer (`src/lsh/adapters/`)

- `cli.py`: command parsing and view rendering (technical and family modes) for:
  - `lsh check <url>`
  - `lsh email-check <headers_or_file>`
  - `lsh qr-scan <image_path>`

### Formatter Layer (`src/lsh/formatters/`)

- `family.py`: reusable family-facing formatter used by the CLI and ready for future web/API adapters

## Runtime Flow

1. CLI parses input and options.
2. CLI builds `AnalysisInput` and metadata (allowlist + network options).
3. CLI routes to a URL orchestrator or email orchestrator (and `qr-scan` decodes payloads before URL routing).
4. Orchestrator builds runtime context once (for URL inputs), runs modules, then normalizes and aggregates findings.
5. Orchestrator returns `AnalysisResult` with summary wording influenced by overall risk and confidence.
6. CLI renders technical, family, or JSON output (family rendering now calls the shared formatter layer).

## Current URL Processing Reality (Important)

- Orchestrator now builds one shared URL runtime context per analysis, including normalized/canonical URL data.
- `net_ip`, `url_structure`, `homoglyph`, and `ascii_lookalike` use the shared context.
- Orchestrator now routes modules by declared `supported_input_types` before execution.
- The runtime context is internal and attached to `AnalysisInput` as non-serialized runtime state, so JSON output contracts stay stable.

## Runtime URL Context (Current Shape)

Created in:

- `AnalysisOrchestrator.analyze(...)` via `src/lsh/core/context.py`

Contains (URL inputs):

- raw parsed URL (`raw_parsed`)
- normalized URL model from `normalize_url(...)` (`normalized_url`)
- canonical parsed URL (`canonical_parsed`)
- raw + canonical hostname and registrable-domain values
- IDNA ASCII/Unicode hostname forms (best effort)
- parsed literal-IP / obfuscated-IP / IPv6-mapped-IPv4 helpers

Why non-serialized runtime state:

- keeps the public `AnalysisResult` / CLI JSON contract unchanged
- avoids leaking internal preprocessing details into downstream consumers before the API schema is intentionally designed
- allows gradual detector migration without a breaking model change

## Contract Requirements

Every module must:

1. Implement `ModuleInterface`.
2. Declare `supported_input_types` for orchestrator routing.
3. Accept `AnalysisInput`.
4. Return `list[Finding]`.
5. Remain stateless across calls.
6. Avoid hidden side effects.

## Near-Term Architecture Moves

1. Formalize structured formatter outputs for API/web adapters beyond CLI text rendering.
2. Add a Python API adapter (FastAPI) on top of the existing orchestrator + formatter layers.
3. Keep adapters focused on I/O only.

## Testing Requirements

- Unit tests per module for known-good and known-bad inputs
- Orchestrator tests for aggregate semantics and summary behavior
- CLI tests for output mode behavior and flag interactions
- Adversarial URL regression tests for obfuscated/encoded evasion patterns
