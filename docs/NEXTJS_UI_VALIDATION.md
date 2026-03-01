# Next.js UI Validation Checklist

## Goal

Validate that a minimal Next.js frontend can call and render all primary API flows against the `1.0` contract.

Primary contract source: `docs/API_INTEGRATION.md`

## Environment

Set API base URL in frontend runtime:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## Minimum Screens / Actions

1. URL check form
2. Email header check form
3. QR scan request form (path-based input for current backend contract)

## Required Assertions

### URL flow

- POST `/api/v1/url/check` succeeds.
- `schema_version === "1.0"`.
- `mode === "single"`.
- `item.result.overall_risk` is rendered.
- family toggle (`family=true`) renders `item.family.summary` when present.

### Email flow

- POST `/api/v1/email/check` succeeds.
- Response uses wrapped single shape (`item_count === 1`, `item` present).
- findings list can render empty/non-empty states.

### QR flow

- POST `/api/v1/qr/scan` single mode renders `item`.
- `analyze_all=true` renders `items[]` and handles `item_count > 1`.
- error envelope from `detail.error` is shown in UI for:
  - decoder unavailable
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
3. Execute URL/email/QR happy paths.
4. Execute QR error path (invalid path or no payload case).
5. Capture screenshots of each flow and record contract notes in session log.

## Exit Criteria

- All three flows render from wrapped responses.
- Error states read `detail.error.message` when available.
- No frontend assumptions conflict with `docs/API_INTEGRATION.md`.
