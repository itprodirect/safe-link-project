# Homoglyph / IDN Detector

Offline detector for lookalike domain risks in URL hostnames.

## What It Checks

- hostname extraction from URL input
- Unicode vs IDNA punycode representation
- non-ASCII hostname signal
- mixed-script labels (for example Latin + Cyrillic in one label)
- confusable Unicode character mappings via `confusables`

## Finding Codes

- `HMG000_INVALID_URL`
- `HMG001_NON_ASCII_HOSTNAME`
- `HMG002_PUNYCODE_VISIBILITY`
- `HMG003_MIXED_SCRIPT_HOSTNAME`
- `HMG004_CONFUSABLE_CHARACTERS`

## Evidence Model

Findings include:

- hostname views (Unicode and IDNA)
- incremental score context (`Risk Delta`, `Cumulative Risk`)
- signal-specific evidence for explainability

## Current Limitations

- allowlist support is domain-level only (no per-rule granularity yet)
- no brand impersonation dictionary yet
- confidence labels are coarse and may be recalibrated as modules expand

## Notes

- IP literal hostnames are intentionally skipped; they are handled by `net_ip`.
- ASCII-only lookalikes are intentionally handled by `ascii_lookalike`.
