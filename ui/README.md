# Link Safety Hub UI (Minimal Scaffold)

This folder contains a minimal Next.js UI for validating API contract behavior.

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

## Contract Smoke

Run quick API contract checks from Node:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run smoke:api
```

The smoke script validates:

- `/health`
- `/api/v1/url/check` wrapped single response
- `/api/v1/email/check` wrapped single response
- `/api/v1/qr/scan` structured error envelope for missing image
