# Link Safety Hub UI (Contract Validation Surface)

This folder contains the current Next.js validation UI for checking API contract behavior.
It is still intentionally lean, but `/analyze` now works as a real shared workspace:

- URL and email submit through `POST /api/v2/analyze`
- QR remains available from the same page through `POST /api/v1/qr/scan` until v2 adds file input support
- Quick and Analyst display modes share the same request surface

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

Small reality check: the backend still does the heavy lifting today, and this UI is here to keep the contract honest while the v2 workspace grows.

## API Contract Smoke

Run quick API contract checks from Node:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 NEXT_PUBLIC_UI_ORIGIN=http://127.0.0.1:3000 npm run smoke:api
```

The API smoke script validates:

- `/health`
- CORS preflight for `/api/v1/url/check` from `NEXT_PUBLIC_UI_ORIGIN`
- `/api/v1/url/check` wrapped single response
- `/api/v2/analyze` URL request/response path
- `/api/v1/url/check` allowlist per-finding suppression behavior (`allowlist_findings` + `NONE`)
- `/api/v1/email/check` wrapped single response
- `/api/v2/analyze` email-header request/response path
- `/api/v1/qr/scan` structured error envelope for invalid upload/decoder-unavailable paths

## Browser Smoke

Install the browser once:

```bash
npx playwright install chromium
```

Build and start the UI with the same API base URL you want the browser to hit:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 NEXT_PUBLIC_UI_ORIGIN=http://127.0.0.1:3000 npm run build
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 NEXT_PUBLIC_UI_ORIGIN=http://127.0.0.1:3000 npm run start:smoke
```

In a second shell, run:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 NEXT_PUBLIC_UI_ORIGIN=http://127.0.0.1:3000 npm run smoke:e2e
```

The Playwright smoke covers the unified `/analyze` page for:

- URL submission through `POST /api/v2/analyze`
- email-header submission through `POST /api/v2/analyze`
- QR upload through `POST /api/v1/qr/scan`, asserting the structured error path when the decoded fixture is not a URL or QR decoding is unavailable
