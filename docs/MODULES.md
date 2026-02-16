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
- confusable character checks (Unicode-focused; IP literals are skipped)

Finding codes:

- `HMG000_INVALID_URL`
- `HMG001_NON_ASCII_HOSTNAME`
- `HMG002_PUNYCODE_VISIBILITY`
- `HMG003_MIXED_SCRIPT_HOSTNAME`
- `HMG004_CONFUSABLE_CHARACTERS`

Known limitations:

- allowlist support is first-pass (domain-level only, no per-rule granularity)
- no brand impersonation scoring yet
- URL extraction from free text not implemented

### Module #1B: ASCII Lookalike Detector

- Path: `src/lsh/modules/ascii_lookalike/`
- Input type: `url`
- Network requirement: none (offline)

Detections:

- visually ambiguous ASCII glyph swaps (for example `i/l/1`)
- leet substitutions (for example `0/o`, `1/l`) that normalize to known brand tokens

Finding codes:

- `ASCII001_AMBIGUOUS_GLYPHS`
- `ASCII002_LEET_SUBSTITUTION`

### Module #1C: URL Structure Detector

- Path: `src/lsh/modules/url_structure/`
- Input type: `url`
- Network requirement: none (offline)

Detections:

- userinfo before `@` (`user:pass@host`) with explicit true-host evidence
- deceptive subdomain prefixes like `login.google.com.evil.com`
- nested URL parameters such as `?url=https://...`

Finding codes:

- `URL001_USERINFO_PRESENT`
- `URL002_DECEPTIVE_SUBDOMAIN`
- `URL003_NESTED_URL_PARAMETER`

### Module #1D: Net IP Detector

- Path: `src/lsh/modules/net_ip/`
- Input type: `url`
- Network requirement: none (offline)

Detections:

- private/local IP literal hostnames
- public IP literal hostnames

Finding codes:

- `NET001_PRIVATE_IP_LITERAL`
- `NET002_PUBLIC_IP_LITERAL`

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
5. Set `confidence` intentionally (`LOW`, `MEDIUM`, `HIGH`) for user-calibrated trust.

## P1 Controls (Started)

- Domain allowlist support via input metadata (`allowlist_domains`)
- Category-scope support via input metadata (`allowlist_categories`)
- CLI passthrough:
  - `--allowlist-domain`
  - `--allowlist-file`
  - `--allowlist-category`
- Default allowlist suppression scope is `HMG` + `ASCII`
- `--allowlist-category ALL` enables suppression for all categories (`HMG`, `ASCII`, `URL`, `NET`)
