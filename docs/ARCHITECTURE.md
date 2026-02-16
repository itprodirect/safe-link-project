# Architecture

## Design Principle

Modules detect. Core orchestrates and scores. Adapters render.

## Implemented Architecture (2026-02-16)

### Core Layer (`src/lsh/core/`)

- `models.py`: canonical data contracts (`AnalysisInput`, `Finding`, `AnalysisResult`)
- `allowlist.py`: normalized domain allowlist helpers with category-prefix scoping
- `scorer.py`: severity mapping and finding normalization
- `orchestrator.py`: module execution + aggregate result construction + confidence-aware summary text
- `rules.py`: shared detection constants for brand, URL-parameter, and ASCII heuristics

### Module Layer (`src/lsh/modules/`)

- `homoglyph/`: IDN/homoglyph risk detector (offline)
- `ascii_lookalike/`: ASCII glyph/leet brand lookalike detector (offline)
- `url_structure/`: URL deception-pattern detector (offline)
- `net_ip/`: IP literal classifier (offline)
- `redirect/`: opt-in redirect chain detector (HEAD-only network checks)
- `email_auth/`: local email header auth analyzer (SPF/DKIM/DMARC parsing)

### Adapter Layer (`src/lsh/adapters/`)

- `cli.py`: command parsing and view rendering (technical and family modes)

## Runtime Flow

1. CLI parses input (`lsh check <url>` or `lsh email-check <headers_or_file>`).
2. CLI creates `AnalysisInput`.
3. CLI calls `AnalysisOrchestrator.analyze(...)`.
4. Orchestrator runs each module and normalizes findings.
5. Orchestrator returns `AnalysisResult` with risk/severity and summary wording influenced by finding confidence.
6. CLI renders technical, family, or JSON output.

## Contract Requirements

Every module must:

1. Implement `ModuleInterface`.
2. Accept `AnalysisInput`.
3. Return `list[Finding]`.
4. Remain stateless across calls.
5. Avoid hidden side effects.

## Near-Term Architecture Moves

1. Add input-aware module routing in orchestrator (by `input_type`).
2. Move family explainer logic into a dedicated module layer component.
3. Add QR adapter flows while keeping core contracts stable.
4. Keep adapters focused on I/O only.

## Testing Requirements

- Unit tests per module for known-good and known-bad inputs
- Orchestrator tests for aggregate semantics
- CLI tests for output mode behavior
