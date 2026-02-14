# Architecture

## Design Principle

Modules are independent analyzers. Shared contracts live in `lsh.core`. Adapters handle input/output only.

## Current Implementation (2026-02-13)

Implemented components:

- Core models: `src/lsh/core/models.py`
- Scorer and severity mapping: `src/lsh/core/scorer.py`
- CLI adapter: `src/lsh/adapters/cli.py`
- Homoglyph module: `src/lsh/modules/homoglyph/analyzer.py`

Current flow:

1. CLI receives `lsh check <url>`
2. CLI builds `AnalysisInput(input_type="url", content=<url>)`
3. CLI runs enabled URL modules (currently Homoglyph only)
4. Findings are normalized via scorer
5. CLI computes overall risk/severity and prints summary + actions

## Target Architecture (Phase 1 completion)

Planned near-term refactor:

- Extract orchestration from CLI into a dedicated orchestrator layer
- Route by `input_type` to relevant modules
- Keep modules stateless and side-effect free

Target flow:

1. Adapter parses user input
2. Orchestrator selects modules
3. Modules return `Finding` lists
4. Scorer normalizes severity
5. Family mode (or adapter view) formats plain-language output

## Contracts

Key models:

- `AnalysisInput`
- `Finding`
- `Evidence`
- `AnalysisResult`
- `Severity`
- `ModuleInterface`

Every module must:

1. Implement `ModuleInterface`
2. Accept `AnalysisInput`
3. Return `list[Finding]`
4. Avoid persistent state
5. Handle errors gracefully

## CLI Notes

Implemented command:

- `lsh check <url>`

Planned commands:

- `lsh email-check <headers_or_file>`
- `lsh qr-scan <image>`
- `lsh inbox-scan <mbox_or_eml>`
