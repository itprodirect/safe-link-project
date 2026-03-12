# API Integration Contract

## Status

Current stable contract: `1.0` (`/api/v1/*`)
Current draft contract: `2.0` (`/api/v2/analyze`, `/api/v2/policies`)
Updated: `2026-03-11` (E5 policy CRUD + analyze policy-id integration)

This document is the integration source of truth for backend consumers (Next.js UI, scripts, and service callers).

## Base URL

Local default:

```text
http://127.0.0.1:8000
```

Endpoints:

- `GET /health`
- `POST /api/v1/url/check`
- `POST /api/v1/email/check`
- `POST /api/v1/qr/scan`
- `POST /api/v2/analyze` (draft v2 unified endpoint)
- `GET /api/v2/policies`
- `POST /api/v2/policies`
- `GET /api/v2/policies/{id}`
- `PUT /api/v2/policies/{id}`
- `DELETE /api/v2/policies/{id}`

## CORS Contract

API CORS behavior is controlled by `LSH_API_CORS_ALLOW_ORIGINS`.

- default (when env var is unset): `http://127.0.0.1:3000,http://localhost:3000`
- value format: comma-separated list of allowed origins
- set to an empty string to disable CORS headers entirely

Hosted example:

```text
LSH_API_CORS_ALLOW_ORIGINS=https://safe-link-ui.example.com
```

## Request Contracts

### POST `/api/v2/analyze` (Draft)

```json
{
  "input_type": "url",
  "content": "https://example.com",
  "subject": "optional display label",
  "family": false,
  "policy_id": "optional-policy-id",
  "allowlist_domains": ["trusted.example"],
  "allowlist_categories": ["HMG", "ASCII"],
  "allowlist_findings": ["HMG002_PUNYCODE_VISIBILITY"],
  "network_enabled": false,
  "network_max_hops": 5,
  "network_timeout": 3.0
}
```

Notes:

- `input_type` supports: `url`, `email_headers`, `email_file`.
- `content` is the raw value to analyze for the declared `input_type`.
- URL-only controls (`allowlist_*`, `network_*`) are applied when `input_type="url"`.
- `policy_id` is optional and applies only to `input_type="url"`; policy rules are merged with inline metadata using union semantics.
- Missing `policy_id` returns structured `404` (`POLICY_NOT_FOUND`).
- `subject` overrides display label in wrapped response output.
- Current v2 implementation returns wrapped `single` mode responses only.

### GET `/api/v2/policies`

Returns persisted policy packs.

Success shape:

```json
{
  "schema_version": "2.0",
  "flow": "policies_list",
  "item_count": 1,
  "items": [
    {
      "id": "uuid",
      "name": "corp-safe",
      "description": "Trusted suppression profile",
      "allowlist_domains": ["trusted.example"],
      "allowlist_categories": ["NONE"],
      "allowlist_findings": ["HMG002_PUNYCODE_VISIBILITY"],
      "input_types": ["url"],
      "enabled": true,
      "created_at": "2026-03-11T22:00:00+00:00",
      "updated_at": "2026-03-11T22:00:00+00:00",
      "tags": ["prod"]
    }
  ]
}
```

### POST `/api/v2/policies`

Create a policy pack.

```json
{
  "name": "corp-safe",
  "description": "Trusted suppression profile",
  "allowlist_domains": ["trusted.example"],
  "allowlist_categories": ["NONE"],
  "allowlist_findings": ["HMG002_PUNYCODE_VISIBILITY"],
  "input_types": ["url"],
  "enabled": true,
  "tags": ["prod"]
}
```

### GET `/api/v2/policies/{id}`

Returns one policy pack by ID.

### PUT `/api/v2/policies/{id}`

Applies full/partial validated updates. At least one mutable field is required.

### DELETE `/api/v2/policies/{id}`

Deterministic delete shape:

```json
{
  "schema_version": "2.0",
  "flow": "policies_delete",
  "id": "uuid",
  "deleted": true
}
```

### POST `/api/v1/url/check`

```json
{
  "url": "https://example.com",
  "family": false,
  "allowlist_domains": ["trusted.example"],
  "allowlist_categories": ["HMG", "ASCII"],
  "allowlist_findings": ["HMG002_PUNYCODE_VISIBILITY"],
  "network_enabled": false,
  "network_max_hops": 5,
  "network_timeout": 3.0
}
```

Notes:

- `url` is required.
- `allowlist_categories` values are normalized to uppercase server-side (`NONE` disables default category suppression).
- `allowlist_findings` enables per-rule suppression for allowlisted hostnames (exact code, stem, or `*` prefix).
- `network_*` options control redirect module behavior only when `network_enabled=true`.

### POST `/api/v1/email/check`

```json
{
  "headers": "Authentication-Results: mx; spf=pass; dkim=pass; dmarc=pass",
  "source_label": "inline headers",
  "family": false
}
```

Notes:

- `headers` is the raw header text input.
- `source_label` is a display label echoed back as `item.subject`.

### POST `/api/v1/qr/scan`

`multipart/form-data` fields:

- `file` (required): uploaded QR image bytes
- `analyze_all` (optional, default `false`)
- `family` (optional, default `false`)

Example:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/qr/scan" \
  -F "file=@./code.png" \
  -F "analyze_all=false" \
  -F "family=false"
```

Notes:

- `file` is required and must be an image payload readable by the QR decoder.
- if `python-multipart` is missing, this endpoint returns `503` with `QRC_MULTIPART_UNAVAILABLE`; other endpoints remain available.
- `analyze_all=false` returns one selected URL result.
- `analyze_all=true` returns wrapped multi-item results.

## Success Response Contract

All successful analysis responses include:

- `schema_version` (`"1.0"` for v1 flows, `"2.0"` for current v2 analyze flow)
- `flow` (`url_check`, `email_check`, `qr_scan`, `analyze`)
- `mode` (`single` or `multi`)
- `input_type`
- `item_count`

For `POST /api/v2/analyze`:

- `schema_version` is `"2.0"`
- `flow` is `"analyze"`
- `mode` is currently `"single"`
- URL responses add `item.analyst`; email responses do not require it

### Single-mode shape

```json
{
  "schema_version": "1.0",
  "flow": "url_check",
  "mode": "single",
  "input_type": "url",
  "item_count": 1,
  "item": {
    "subject": "https://example.com",
    "result": { "... AnalysisResult ..." },
    "family": { "... optional family summary object ..." }
  }
}
```

### Multi-mode shape

```json
{
  "schema_version": "1.0",
  "flow": "qr_scan",
  "mode": "multi",
  "input_type": "url",
  "item_count": 2,
  "items": [
    { "subject": "https://a.example", "result": { "... AnalysisResult ..." } },
    { "subject": "https://b.example", "result": { "... AnalysisResult ..." } }
  ]
}
```

### URL analyst shape (`/api/v2/analyze`, `input_type="url"`)

`item.analyst` is additive and currently URL-only.

```json
{
  "domain_anatomy": { "... normalized URL and host breakdown ..." },
  "evidence_rows": [
    {
      "module": "homoglyph",
      "category": "HMG004_CONFUSABLE_CHARACTERS",
      "finding_key": "homoglyph:HMG004_CONFUSABLE_CHARACTERS",
      "compare_key": "homoglyph:HMG004_CONFUSABLE_CHARACTERS",
      "sort_index": 0,
      "risk_delta": 25,
      "evidence": [
        { "key": "hostname", "label": "Hostname", "value": "?pple.com" }
      ],
      "evidence_map": {
        "hostname": "?pple.com"
      }
    }
  ],
  "redirect_trace": { "... optional redirect timeline ..." },
  "suppression_trace": {
    "configured_allowlist_domains": ["trusted.example"],
    "suppressed_rows": [
      {
        "finding_key": "homoglyph:HMG002_PUNYCODE_VISIBILITY",
        "compare_key": "homoglyph:HMG002_PUNYCODE_VISIBILITY:finding:hmg002_punycode_visibility",
        "sort_index": 0,
        "suppression_scope": "finding"
      }
    ]
  }
}
```

Compare-ready additions:

- `finding_key`: stable semantic key for one finding family (`<module>:<category>`)
- `compare_key`: deterministic row key for future history/delta matching; may diverge from `finding_key` if duplicate finding families ever appear
- `sort_index`: deterministic presentation order after analyst sorting
- `risk_delta`: parsed integer delta when evidence includes `Risk Delta`
- `evidence[].key`: normalized machine key for one evidence label (`character_mapping`, `redirect_hops`, etc.)
- `evidence_map`: flattened keyed evidence object for cheap compare/diff logic
- `suppression_trace.suppressed_rows[*].compare_key`: stable suppression-row key for future policy/history diff views

Current analyst sections:

- `domain_anatomy`: submitted/canonical URL, host labels, IDNA forms, IP-literal markers, normalization notes
- `evidence_rows`: UI-ready finding rows sorted by highest cumulative risk first
- `redirect_trace`: optional redirect chain projection built from redirect findings
- `suppression_trace`: allowlist inputs plus structured suppressed-finding rows

### QR compatibility keys

`/api/v1/qr/scan` additionally includes workflow metadata:

- `image_name` (uploaded filename when available)
- `decoded_payloads`
- `decoded_payload_count`
- `url_payload_count`
- `analyzed_all`

For compatibility with existing CLI JSON consumers, QR responses currently also include legacy keys:

- `image_path` (legacy alias of `image_name`)
- single mode: `selected_url`, `result`
- multi mode: `results`

New integrations should use wrapper keys (`item` / `items`) as the primary contract.

Legacy-key control:

- env var: `LSH_API_INCLUDE_QR_LEGACY_KEYS`
- default: enabled (`true`)
- disable legacy keys with: `LSH_API_INCLUDE_QR_LEGACY_KEYS=false`
- API response header:
  - enabled: `X-LSH-QR-Legacy-Keys: included; sunset=2026-06-01; use=item/items`
  - disabled: `X-LSH-QR-Legacy-Keys: disabled`

Deprecation target:

- legacy keys are planned for removal in the next major contract version (`2.0`).
- consumers should migrate to wrapper-first keys now: `item` / `items`.

## Error Contract

For explicit API errors generated by endpoint logic (for example QR decode issues), response body is:

```json
{
  "detail": {
    "schema_version": "1.0",
    "error": {
      "code": "QRC_NO_URL_PAYLOADS",
      "message": "Decoded QR payloads did not contain URL-like values.",
      "status": 400
    }
  }
}
```

Known error codes:

- `QRC_MULTIPART_UNAVAILABLE` (`503`)
- `QRC_DECODER_UNAVAILABLE` (`503`)
- `QRC_IMAGE_READ_ERROR` (`400`)
- `QRC_NO_PAYLOADS` (`400`)
- `QRC_NO_URL_PAYLOADS` (`400`)
- `POLICY_NOT_FOUND` (`404`)

Validation errors (`422`) use FastAPI's default validation format and should be handled separately.

## v1/v2 Snapshot Governance (E1-I4)

Deterministic overlap fixture and parity assertions live in:

- `tests/fixtures/contracts/v1_v2_single_payloads.json`
- `tests/contracts/test_v1_v2_snapshot_parity.py`

When to update fixtures:

- only when intentionally changing overlapping v1/v2 single-item contract fields
- never for unrelated adapter/UI changes

How to update fixtures:

1. Verify the intended contract change in code/tests first.
2. Regenerate the fixture with:

```bash
python -c "import json; from tests.contracts.test_v1_v2_snapshot_parity import _FIXTURE_PATH,_build_payloads; _FIXTURE_PATH.write_text(json.dumps(_build_payloads(), indent=2) + '\\n', encoding='utf-8')"
```

3. Re-run parity checks:

```bash
pytest -v --tb=short tests/contracts/test_v1_v2_snapshot_parity.py
```

Review expectations:

- PR description must explain why the snapshot changed.
- Runtime-variant fields (for example `analyzed_at`) must remain normalized as `<TIMESTAMP>` in fixtures.
- v1/v2 overlap parity assertions (`item.result`, `item.family`, `item.subject`) must remain green.

## Versioning Policy
- Clients must check `schema_version`.
- `1.x` can add non-breaking fields for `/api/v1/*`.
- current v2 draft flow uses `schema_version: "2.0"` on `/api/v2/analyze`.
- Breaking changes require a major version bump and migration notes.

Contract enforcement:

- FastAPI endpoints now declare explicit response models for success and QR error envelopes.
- This keeps OpenAPI schema and runtime response validation aligned with documented wrapper shapes.

## Next.js Integration Notes

### Recommended data access pattern

1. Create one typed API client module under `lib/api.ts`.
2. Parse by `mode` (`single` vs `multi`) rather than endpoint-specific branching where possible.
3. Handle non-2xx with:
   - `detail.error` envelope (contracted API errors)
   - fallback to `detail` string/object for framework errors
4. Pass `family=true` when rendering plain-language UI screens.
5. Use `FormData` for `/api/v1/qr/scan`; do not set `Content-Type` manually.

### TypeScript starter types

```ts
export type ApiMode = "single" | "multi";

export interface ApiErrorEnvelope {
  detail: {
    schema_version: "1.0";
    error: {
      code: string;
      message: string;
      status: number;
    };
  };
}

export interface WrappedItem {
  subject: string;
  result: Record<string, unknown>;
  family?: {
    risk_score: number;
    severity: string;
    summary: string;
    signal_confidence: string | null;
    reasons: string[];
    recommendations: string[];
  };
}
```

### Fetch helper sketch

```ts
export async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    cache: "no-store",
  });

  const payload = await res.json();
  if (!res.ok) {
    const apiMessage = payload?.detail?.error?.message;
    throw new Error(apiMessage ?? `API request failed (${res.status})`);
  }
  return payload as T;
}
```

## Operational Notes

- QR API now accepts uploaded image bytes and does not require server-local file paths.
- Policy storage path defaults to `.lsh/policies.json`; override with `LSH_POLICY_STORE_DIR`.
- Use timeout/retry policy in frontend for network-enabled URL checks.

