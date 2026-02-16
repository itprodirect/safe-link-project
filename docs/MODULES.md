# Module Specifications

Each module lives under `src/lsh/modules/<name>/` and implements `ModuleInterface`.

## Implemented

### Module #1: Homoglyph / IDN Detector

- Path: `src/lsh/modules/homoglyph/`
- Input type: `url`
- Network requirement: none (offline)

Detections:

- hostname extraction
- non-ASCII character signal
- punycode visibility (`xn--`)
- mixed-script labels
- confusable character checks

Finding codes:

- `HMG000_INVALID_URL`
- `HMG001_NON_ASCII_HOSTNAME`
- `HMG002_PUNYCODE_VISIBILITY`
- `HMG003_MIXED_SCRIPT_HOSTNAME`
- `HMG004_CONFUSABLE_CHARACTERS`

Known limitations:

- no allowlist support yet
- no brand impersonation scoring yet
- URL extraction from free text not implemented

## Planned Next

### Module #2: Redirect Chain Expander

- Path: `src/lsh/modules/redirect/` (planned)
- Input type: `url`
- Network: opt-in only
- Key controls: hop cap, timeout, safe request policy

### Module #5: Email Auth Checker

- Path: `src/lsh/modules/email_auth/` (planned)
- Input types: `email_headers`, `email_file`

### Module #7: QR Decoder

- Path: `src/lsh/modules/qr_decode/` (planned)
- Input type: `qr_image`

### Module #9: Family Explainer

- Path: `src/lsh/modules/family_mode/` (planned)
- Input: findings and result summary

## Cross-Module Rules

1. Use shared `Finding` schema.
2. Keep behavior deterministic and testable.
3. Emit evidence and recommendations for every non-info signal.
4. Avoid storing state in module instances.
