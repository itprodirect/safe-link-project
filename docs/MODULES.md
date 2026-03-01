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
- no brand impersonation scoring in this module (ASCII brand checks live in `ascii_lookalike`)
- URL extraction from free text is not implemented

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
- fragment deception (for example `#@brand.com` or full URL in fragment)
- suspicious percent-encoding (multi-round decoding, encoded hostnames, encoded path traversal)
- registrable-domain comparisons use offline heuristics for common suffix structures

Finding codes:

- `URL001_USERINFO_PRESENT`
- `URL002_DECEPTIVE_SUBDOMAIN`
- `URL003_NESTED_URL_PARAMETER`
- `URL004_FRAGMENT_DECEPTION`
- `URL005_EXCESSIVE_ENCODING`

Notes:

- The module uses cumulative risk within the module (`risk_delta` -> `cumulative risk`) before orchestrator aggregation.
- Encoding checks reuse iterative decode helpers from `src/lsh/core/normalizer.py`.

### Module #1D: Net IP Detector

- Path: `src/lsh/modules/net_ip/`
- Input type: `url`
- Network requirement: none (offline)

Detections:

- private/local IP literal hostnames
- public IP literal hostnames
- obfuscated IPv4 formats (integer, octal, hex, abbreviated)
- localhost aliases (for example `localhost.localdomain`)
- IPv6-mapped IPv4 addresses (`::ffff:x.x.x.x`)
- mixed numeric notation in dotted quads (hex + octal + decimal)

Finding codes:

- `NET001_PRIVATE_IP_LITERAL`
- `NET002_PUBLIC_IP_LITERAL`
- `NET003_OBFUSCATED_IP`
- `NET004_LOCALHOST_ALIAS`
- `NET005_IPV6_MAPPED_V4`
- `NET006_MIXED_NOTATION`

Notes:

- Obfuscated IP parsing is deterministic and cross-platform (does not rely on `socket.inet_aton` behavior).
- Some findings can stack (for example obfuscated IP + private/local scope).

### Module #2: Redirect Chain Expander

- Path: `src/lsh/modules/redirect/`
- Input type: `url`
- Network: opt-in only (`--network`)
- Safety controls: hop cap and timeout

Detections:

- redirect chain presence
- cross-domain redirect jumps
- max-hop limit reached
- redirect loops
- timeout/request errors
- non-http(s) redirect targets

Finding codes:

- `RED000_NETWORK_URL_REQUIRED`
- `RED001_REDIRECT_CHAIN_PRESENT`
- `RED002_CROSS_DOMAIN_REDIRECT`
- `RED003_MAX_HOPS_REACHED`
- `RED004_REDIRECT_LOOP_DETECTED`
- `RED005_REQUEST_TIMEOUT`
- `RED006_REQUEST_ERROR`
- `RED007_NON_HTTP_REDIRECT_TARGET`

### Module #5: Email Auth Checker

- Path: `src/lsh/modules/email_auth/`
- Input types: `email_headers`, `email_file`
- Network requirement: none in this phase (header-only analysis)

Detections:

- missing authentication result headers
- SPF fail/weak/missing states
- DKIM fail/weak/missing states
- DMARC fail/weak/missing states
- nearest-header precedence is used to avoid worst-hop aggregation across forwarded paths

Finding codes:

- `EML000_EMPTY_INPUT`
- `EML001_NO_AUTH_HEADERS`
- `EML101_SPF_FAIL`
- `EML102_SPF_WEAK_OR_MISSING`
- `EML201_DKIM_FAIL`
- `EML202_DKIM_WEAK_OR_MISSING`
- `EML301_DMARC_FAIL`
- `EML302_DMARC_WEAK_OR_MISSING`

### Module #7: QR Decoder (URL Handoff Helper)

- Path: `src/lsh/modules/qr_decode/`
- Primary input type: `qr_image` (local file path)
- Network requirement: none (offline)

Detections / helper behavior:

- local QR payload decoding from image files (`Pillow` + `pyzbar`/zbar backend)
- HTTP(S) URL payload extraction (`extract_url_payloads(...)`)
- optional detector findings for decoder-unavailable / image-read-error / no-payload cases (`QRC*`)
- CLI `lsh qr-scan` reuses decoded URL payloads with the existing URL analysis pipeline

Notes:

- Decoder dependencies are optional and handled gracefully at runtime.
- `lsh qr-scan` defaults to analyzing the first decoded URL payload and supports `--all`.

## Planned Next

### Family Formatter (Implemented as Formatter Layer, not Module)

- Path: `src/lsh/formatters/family.py`
- Input: `AnalysisResult`
- Purpose: reusable family-facing structured output and CLI text rendering

### Next Module-Adjacent Work

- Add structured formatter variants for API/web responses

## Shared URL Context Adoption Status

`src/lsh/core/context.py` provides shared runtime URL preprocessing used by URL detectors.

| Module | Input | Uses Shared URL Context? | Notes |
|---|---|---:|---|
| `net_ip` | `url` | Yes | Uses cached hostname/IP parsing helpers and mapped-IP data |
| `url_structure` | `url` | Yes | Uses cached parsed URL + hostname/registrable-domain values |
| `homoglyph` | `url` | Yes | Uses cached URL context host and IDNA forms |
| `ascii_lookalike` | `url` | Yes | Uses cached URL context host/IP-literal parsing |
| `redirect` | `url` | No (optional future) | May benefit from shared hostname/domain context but also performs network calls |
| `email_auth` | `email_headers`/`email_file` | N/A | Non-URL input |
| `qr_decode` | `qr_image` | N/A | Decodes local image payloads before URL handoff |

Future migration targets:

- optional `redirect` enrichment (for cached host/domain context)

## Cross-Module Rules

1. Use shared `Finding` schema.
2. Declare `supported_input_types` so orchestrator-side routing is explicit.
3. Keep behavior deterministic and testable.
4. Emit evidence and recommendations for every non-trivial signal.
5. Avoid storing state in module instances.
6. Set `confidence` intentionally (`LOW`, `MEDIUM`, `HIGH`) for user-calibrated trust.
7. Keep finding code IDs stable once published in docs/tests.

## P1 Controls (Current)

- Domain allowlist support via input metadata (`allowlist_domains`)
- Category-scope support via input metadata (`allowlist_categories`)
- CLI passthrough:
  - `--allowlist-domain`
  - `--allowlist-file`
  - `--allowlist-category`
- Default allowlist suppression scope is `HMG` + `ASCII`
- `--allowlist-category ALL` enables suppression for all categories (`HMG`, `ASCII`, `URL`, `NET`)
- Redirect findings (`RED*`) are intentionally not suppressible via allowlist in this phase
