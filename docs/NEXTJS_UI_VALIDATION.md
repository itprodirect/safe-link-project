# Next.js UI Validation Checklist

## Goal

Validate that a minimal Next.js frontend can call and render all primary API flows against the `1.0` contract.
Current validation focus is still v1 wrapper flows, with incremental checks added for draft v2 paths as they stabilize.

Primary contract source: `docs/API_INTEGRATION.md`

Implementation status:

- minimal scaffold now lives under `ui/`
- API contract smoke script: `ui/scripts/api-contract-smoke.mjs`

## Environment

Set API base URL in frontend runtime:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
NEXT_PUBLIC_UI_ORIGIN=http://127.0.0.1:3000
```

## Minimum Screens / Actions

1. URL check form
2. Email header check form
3. QR scan request form (file upload using `multipart/form-data`)

## Required Assertions

### CORS / reachability

- GET `/health` succeeds on target API URL.
- OPTIONS preflight to `/api/v1/url/check` from the UI origin succeeds.
- `access-control-allow-origin` matches configured UI origin (or `*` when explicitly configured).

### URL flow

- POST `/api/v1/url/check` succeeds.
- `schema_version === "1.0"`.
- `mode === "single"`.
- `item.result.overall_risk` is rendered.
- family toggle (`family=true`) renders `item.family.summary` when present.
- allowlist controls are exposed in UI:
  - `allowlist_domains`
  - `allowlist_categories` (including `NONE`)
  - `allowlist_findings`
- per-finding suppression check works:
  - with `allowlist_categories=["NONE"]` and `allowlist_findings=["HMG002_PUNYCODE_VISIBILITY"]`,
    HMG002 is suppressed while non-targeted findings (for example HMG003) remain.

### Email flow

- POST `/api/v1/email/check` succeeds.
- Response uses wrapped single shape (`item_count === 1`, `item` present).
- findings list can render empty/non-empty states.

### QR flow

- POST `/api/v1/qr/scan` with uploaded file succeeds and single mode renders `item`.
- `analyze_all=true` renders `items[]` and handles `item_count > 1`.
- error envelope from `detail.error` is shown in UI for:
  - decoder unavailable
  - unreadable/invalid upload bytes
  - no payloads
  - no URL payloads

## Suggested Frontend Data Contracts

Prefer wrapper keys over legacy compatibility keys:

- single: `item`
- multi: `items`

Avoid binding new UI logic to:

- `selected_url`
- `result`
- `results`

These remain for backward compatibility and may be removed in a later major version.

## Minimal Validation Sequence

1. Start backend:
   - local Python (`uvicorn lsh.adapters.api:app --host 127.0.0.1 --port 8000`)
   - or Docker (`docker compose up --build`)
2. Start Next.js app with `NEXT_PUBLIC_API_BASE_URL`.
   - from `ui/`: `npm run dev`
3. Execute URL/email/QR happy paths.
4. Execute QR error path (invalid upload bytes or no payload case).
5. Run contract smoke script:
   - from `ui/`: `npm run smoke:api`
6. Capture screenshots of each flow and record contract notes in session log.

## Exit Criteria

- All three flows render from wrapped responses.
- Error states read `detail.error.message` when available.
- No frontend assumptions conflict with `docs/API_INTEGRATION.md`.
