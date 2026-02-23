# URL Structure Detector

Offline detector for classic URL-format deception patterns.

## Signals

- `URL001_USERINFO_PRESENT`: userinfo appears before `@`, so displayed text can hide the true host
- `URL002_DECEPTIVE_SUBDOMAIN`: trusted-looking token appears in subdomain prefix but registrable domain differs
- `URL003_NESTED_URL_PARAMETER`: query contains a full nested URL (possible redirect wrapper/open redirect pattern)
- `URL004_FRAGMENT_DECEPTION`: fragment (`#...`) mimics a trusted destination or contains a full URL
- `URL005_EXCESSIVE_ENCODING`: suspicious percent-encoding (multi-round decode, encoded host, encoded traversal)

## Scope

- URL input only
- Uses `urllib.parse` plus offline hostname/registrable-domain heuristics
- Reuses iterative decode helpers from `src/lsh/core/normalizer.py` for encoding checks
- No network lookups
- Can be allowlist-suppressed only when `URL` (or `ALL`) is explicitly selected in allowlist categories
