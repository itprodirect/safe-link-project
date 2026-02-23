# Architecture

## Design Principle

Modules detect. Core orchestrates and scores. Adapters render.

## Implemented Architecture (2026-02-23)

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
- `net_ip` and `url_structure` use the shared context today.
- `homoglyph` and `ascii_lookalike` still parse from raw input directly (migration path remains).
- The runtime context is internal and attached to `AnalysisInput` as non-serialized runtime state, so JSON output contracts stay stable.

## Contract Requirements

Every module must:

1. Implement `ModuleInterface`.
2. Accept `AnalysisInput`.
3. Return `list[Finding]`.
4. Remain stateless across calls.
5. Avoid hidden side effects.

## Near-Term Architecture Moves

1. Migrate remaining URL detectors (`homoglyph`, `ascii_lookalike`, optionally `redirect`) to the shared URL context.
2. Add input-aware module routing in orchestrator (by `input_type`) instead of relying on each module to early-return.
3. Formalize structured formatter outputs for API/web adapters beyond CLI text rendering.
4. Add a Python API adapter (FastAPI) on top of the existing orchestrator + formatter layers.
5. Keep adapters focused on I/O only.

## Testing Requirements

- Unit tests per module for known-good and known-bad inputs
- Orchestrator tests for aggregate semantics and summary behavior
- CLI tests for output mode behavior and flag interactions
- Adversarial URL regression tests for obfuscated/encoded evasion patterns
