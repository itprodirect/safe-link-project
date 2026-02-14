# Module Specifications

Each module lives under `src/lsh/modules/<name>/` and implements `ModuleInterface`.

## Module #1: Homoglyph / IDN Detector (Implemented)

- Directory: `src/lsh/modules/homoglyph/`
- Input types currently supported: `url`
- Network required: No (offline only)

Implemented detections:

- Hostname extraction from URL
- Non-ASCII hostname detection
- IDNA/punycode visibility (`unicode` and `xn--...` forms)
- Mixed-script label detection (for example Latin + Cyrillic)
- Confusable character analysis using `confusables`

Finding codes emitted:

- `HMG000_INVALID_URL`
- `HMG001_NON_ASCII_HOSTNAME`
- `HMG002_PUNYCODE_VISIBILITY`
- `HMG003_MIXED_SCRIPT_HOSTNAME`
- `HMG004_CONFUSABLE_CHARACTERS`

Evidence behavior:

- Includes hostname views, signal-specific context, and explainable scoring fields:
  - `Risk Delta`
  - `Cumulative Risk`

Known limitations:

- No allowlist for known-safe IDN domains yet
- No brand impersonation matching yet
- No `text` input URL extraction yet

## Module #2: Redirect Chain Expander (Planned, Next)

- Directory: `src/lsh/modules/redirect/`
- Input types: `url`
- Network: Yes (opt-in)
- Planned output: hop-by-hop findings with explicit safety limits

## Module #5: Email Auth Checker (Planned)

- Directory: `src/lsh/modules/email_auth/`
- Input types: `email_headers`, `email_file`
- Network: optional for DNS verification

## Module #7: QR Decoder (Planned)

- Directory: `src/lsh/modules/qr_decode/`
- Input types: `qr_image`
- Network: no (decode), optional for downstream URL analysis

## Module #9: Family Mode Explainer (Planned)

- Directory: `src/lsh/modules/family_mode/`
- Input: `Finding` objects
- Network: No

## Other Planned Modules

- #3 Domain Risk Profiler
- #4 Content Snapshot Analyzer
- #6 Attachment Triage
- #8 Password Hygiene
- #10 Offline Inbox Scanner
