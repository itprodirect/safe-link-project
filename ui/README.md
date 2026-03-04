# Link Safety Hub UI (Contract Validation Surface)

This folder contains the current Next.js validation UI for checking API contract behavior.
It is intentionally lean: reliable for integration validation, not yet the final v2 product UX.

For the full product UX direction, see:

- `docs/V2_BLUEPRINT.md`
- `docs/V2_ROADMAP_ISSUES.md`

## Prerequisites

- Node.js 20+ (tested on Node 22)
- running Link Safety Hub API at `http://127.0.0.1:8000` (or set `NEXT_PUBLIC_API_BASE_URL`)

## Install

```bash
cd ui
npm install
```

## Run Dev UI

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

Open `http://127.0.0.1:3000`.

Small reality check: the backend does the heavy lifting today, this UI keeps us honest on contracts while the v2 workspace is in progress.

## Contract Smoke

Run quick API contract checks from Node:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 NEXT_PUBLIC_UI_ORIGIN=http://127.0.0.1:3000 npm run smoke:api
```

The smoke script validates:

- `/health`
- CORS preflight for `/api/v1/url/check` from `NEXT_PUBLIC_UI_ORIGIN`
- `/api/v1/url/check` wrapped single response
- `/api/v1/url/check` allowlist per-finding suppression behavior (`allowlist_findings` + `NONE`)
- `/api/v1/email/check` wrapped single response
- `/api/v1/qr/scan` structured error envelope for invalid upload/decoder-unavailable paths
