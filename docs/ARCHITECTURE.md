# Architecture

## Design Principle

Modules detect. Core orchestrates and scores. Application services compose. Adapters render.

## Implemented Architecture (2026-03-08)

### Core Layer (`src/lsh/core/`)

- `models.py`: canonical data contracts (`AnalysisInput`, `Finding`, `AnalysisResult`, `NormalizedURL`)
- `allowlist.py`: normalized domain allowlist helpers with category-prefix scoping plus runtime suppression-trace capture
- `url_tools.py`: shared URL parsing and registrable-domain extraction (offline heuristics)
- `context.py`: shared runtime context/preprocessing cache for one analysis run (URL-focused today), including analyst-only suppression events
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

### Application Layer (`src/lsh/application/`)

- `analysis_service.py`: shared URL/email analysis entrypoints used by both CLI and API adapters
  - centralizes orchestrator construction
  - removes duplicated adapter wiring and summary-builder definitions
  - keeps adapter responsibilities focused on input/output transport

### Adapter Layer (`src/lsh/adapters/`)

- `cli.py`: command parsing and view rendering (technical and family modes) for:
  - `lsh check <url>`
  - `lsh email-check <headers_or_file>`
  - `lsh qr-scan <image_path>`
- `api.py`: minimal FastAPI adapter with endpoint parity for URL, email, and QR flows plus draft unified v2 analyze endpoint (`POST /api/v2/analyze`)
  - when `python-multipart` is unavailable, `/api/v1/qr/scan` returns a structured unavailable envelope while URL/email/v2 endpoints remain available

### Formatter Layer (`src/lsh/formatters/`)

- `family.py`: reusable family-facing formatter used by the CLI and ready for future web/API adapters
- `structured.py`: stable single/multi-item response wrappers shared by CLI JSON and API responses, including v2 URL analyst projections and compare-ready evidence keys

## Runtime Flow

1. CLI/API adapters parse transport input and options.
2. Adapters call shared application services (`analyze_url`, `analyze_email`).
3. Application service routes to shared orchestrators (URL or email).
4. Orchestrator builds runtime context once (for URL inputs), runs modules, then normalizes and aggregates findings.
5. Orchestrator returns `AnalysisResult` with summary wording influenced by overall risk and confidence.
6. Structured formatters can project analyst-only URL views (domain anatomy, redirects, suppression rows) from runtime context without changing the base `AnalysisResult` model.
7. Adapters render technical/family/structured outputs using shared formatter helpers.

## Current URL Processing Reality (Important)

- Orchestrator now builds one shared URL runtime context per analysis, including normalized/canonical URL data.
- `net_ip`, `url_structure`, `homoglyph`, and `ascii_lookalike` use the shared context.
- Orchestrator now routes modules by declared `supported_input_types` before execution.
- The runtime context is internal and attached to `AnalysisInput` as non-serialized runtime state, so base JSON contracts stay stable while v2 analyst projections can still expose selected derived fields.

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
- structured suppression-trace events recorded when allowlist rules suppress URL findings

Why non-serialized runtime state:

- keeps the public `AnalysisResult` / CLI JSON contract unchanged
- avoids leaking internal preprocessing details into downstream consumers before the API schema is intentionally designed
- allows additive v2 analyst projections (including suppression traces) without a breaking model change
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

1. Keep structured response wrappers versioned and backward compatible for API consumers.
2. Expand API surface carefully (batch endpoints, auth/rate limits as needed).
3. Keep adapters focused on I/O only.

## Testing Requirements

- Unit tests per module for known-good and known-bad inputs
- Orchestrator tests for aggregate semantics and summary behavior
- CLI tests for output mode behavior and flag interactions
- Adversarial URL regression tests for obfuscated/encoded evasion patterns

