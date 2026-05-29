# Local Analyze UI Runbook

Status: M1 closeout runbook
Milestone: M1 - Simplified Analyze UI
Last updated: 2026-05-29

## Milestone Summary

M1 simplified the primary `/analyze` page into a focused URL-or-QR analysis flow
without changing backend detection behavior, API contracts, scoring, policy
behavior, history behavior, auth, or billing surfaces.

The completed milestone includes:

- `#23` / `b0e8b4c`: added `docs/SIMPLE_ANALYZE_UI_SPEC.md` and the mockup asset.
- `#24` / `41a9d01`: simplified the Analyze shell and input card.
- `#25` / `476a8c9`: simplified the result hierarchy.
- `#26` / `1930bc5`: hardened loading, validation, QR/API error, accessibility,
  viewport, and verdict-state coverage.

The current `/analyze` local validation target is:

- Sidebar-only Analyze shell.
- Visible URL input and optional QR image upload.
- One primary `Analyze` button.
- Email hidden from the simplified `/analyze` browser surface while backend email
  behavior and legacy validation paths remain available elsewhere.
- Primary result hierarchy of `Verdict`, risk pill, plain-English explanation,
  `Key reasons`, `What to do next`, and collapsed `Evidence / technical details`.
- Display-only verdict mapping from existing action/severity logic:
  `Safe / Low`, `Caution / Medium`, `Suspicious / High`, and
  `Dangerous / Critical`.

## Mockup Reference

Reference mockup:

```text
docs/assets/simple-analyze-ui-mockup.png
```

Spec source:

```text
docs/SIMPLE_ANALYZE_UI_SPEC.md
```

## Prerequisites

- Python 3.11+
- Node.js 20+ for the UI workspace
- npm dependencies installed under `ui/`
- Playwright Chromium installed before browser smoke runs
- A local API server reachable at `http://127.0.0.1:8000`
- A local UI server reachable at `http://127.0.0.1:3000`

## Required Environment Variables

Local defaults:

```powershell
$env:NEXT_PUBLIC_API_BASE_URL = "http://127.0.0.1:8000"
$env:NEXT_PUBLIC_UI_ORIGIN = "http://127.0.0.1:3000"
```

Optional API environment variables:

```powershell
$env:LSH_API_CORS_ALLOW_ORIGINS = "http://127.0.0.1:3000,http://localhost:3000"
$env:LSH_API_INCLUDE_QR_LEGACY_KEYS = "true"
$env:LSH_POLICY_STORE_DIR = ".lsh"
```

Notes:

- `NEXT_PUBLIC_API_BASE_URL` must be set before `npm run build` when validating
  the production smoke server.
- `NEXT_PUBLIC_UI_ORIGIN` is used by API contract smoke and Playwright base URL
  configuration.
- `LSH_API_CORS_ALLOW_ORIGINS` defaults to local UI origins when unset.
- `LSH_API_INCLUDE_QR_LEGACY_KEYS=false` can be used by wrapper-first hosted
  integrations, but local M1 browser checks do not require disabling legacy keys.
- `LSH_POLICY_STORE_DIR` is only needed when policy CRUD persistence must use a
  specific local directory.

## Local Setup Commands

Backend setup from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Frontend setup:

```powershell
cd ui
npm install
npx playwright install chromium
```

## Backend Startup Commands

Start the local FastAPI adapter from the repository root:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn lsh.adapters.api:app --host 127.0.0.1 --port 8000
```

Health check:

```powershell
curl.exe http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok"}
```

Container alternative:

```powershell
docker compose up --build
```

## Frontend Startup Commands

Development UI from `ui/`:

```powershell
$env:NEXT_PUBLIC_API_BASE_URL = "http://127.0.0.1:8000"
npm run dev
```

Open:

```text
http://127.0.0.1:3000/analyze
```

Production smoke UI from `ui/`:

```powershell
$env:NEXT_PUBLIC_API_BASE_URL = "http://127.0.0.1:8000"
$env:NEXT_PUBLIC_UI_ORIGIN = "http://127.0.0.1:3000"
npm run build
npm run start:smoke
```

Run `npm run start:smoke` in its own terminal. It is a long-running server
process.

## Frontend Validation Commands

Run from `ui/` unless noted.

Static and build validation:

```powershell
npm run lint
npm run typecheck
npm run build
```

API contract smoke with the backend running on `:8000`:

```powershell
$env:NEXT_PUBLIC_API_BASE_URL = "http://127.0.0.1:8000"
$env:NEXT_PUBLIC_UI_ORIGIN = "http://127.0.0.1:3000"
npm run smoke:api
```

Full browser smoke with backend and built UI smoke server running:

```powershell
$env:NEXT_PUBLIC_API_BASE_URL = "http://127.0.0.1:8000"
$env:NEXT_PUBLIC_UI_ORIGIN = "http://127.0.0.1:3000"
npm run smoke:e2e
```

Repository-level docs hygiene from the repository root:

```powershell
git diff --check
```

No markdown formatter or markdownlint script is currently declared in
`pyproject.toml`, `Makefile`, or `ui/package.json`. If a local markdown checker is
installed outside the repo, run it against:

```text
README.md
CLAUDE.md
SESSION_LOG.md
docs/SIMPLE_ANALYZE_UI_SPEC.md
docs/LOCAL_ANALYZE_UI_RUNBOOK.md
ui/README.md
docs/NEXTJS_UI_VALIDATION.md
```

## Relevant Playwright Analyze Test Commands

Run from `ui/` with the backend and UI smoke server running unless a test is
fully mocked.

Analyze smoke suite:

```powershell
npx playwright test e2e/analyze.smoke.spec.ts
```

Verdict and accessibility-focused suite:

```powershell
npx playwright test e2e/analyze.verdict.spec.ts
```

Combined npm script:

```powershell
npm run smoke:e2e
```

Current Analyze browser coverage includes:

- Simplified shell and blank input card.
- Empty and mixed-input validation.
- URL success preserving result cards.
- QR structured-error surfacing.
- Simplified verdict hierarchy.
- Keyboard-operable collapsed technical details.
- Loading, API error, QR decoder/multipart/no-url error states.
- Display mapping across Safe/Low, Caution/Medium, Suspicious/High, and
  Dangerous/Critical.
- Mobile viewport usability.

## Manual Verification Checklist

Use this checklist after backend and frontend servers are running locally.

- Visit `http://127.0.0.1:3000/analyze`.
- Confirm the page shows Safe Link Analyst sidebar branding.
- Confirm `Analyze` is the active sidebar item.
- Confirm `Policies` and `History` are visible but not wired to new M1 feature
  behavior.
- Confirm the heading is `Analyze a suspicious link or QR code`.
- Confirm helper text says `Paste a link or upload a QR image to get a clear verdict.`
- Confirm the URL input is blank on first load.
- Confirm the QR upload control is present and optional.
- Click `Analyze` with no input and confirm an inline accessible validation
  message.
- Enter a URL and click `Analyze`; confirm a verdict card appears.
- Confirm the result shows a risk pill, plain-English summary, key reasons, and
  next actions.
- Confirm `Evidence / technical details` is collapsed by default.
- Expand `Evidence / technical details` with keyboard input and confirm technical
  sections remain reachable.
- Upload a QR image without a URL and confirm the QR flow calls the existing
  `/api/v1/qr/scan` path or shows a structured QR error.
- Enter both a URL and QR image and confirm validation asks for one input type.
- Confirm a validation/API/QR error does not clear the previous successful
  result.
- Check the browser console for actionable errors; ignore the unrelated favicon
  404 noted below if it is the only console issue.

## Known Limitations

- The missing `/favicon.ico` browser-console 404 observed during PR `#26` is
  unrelated to M1 Analyze behavior. This repo currently has no favicon or
  Next.js app icon asset, so local browser sessions may still show that 404 until
  a separate visual-polish task adds one.
- QR scanning depends on `Pillow`, `pyzbar`, and a system `zbar` backend. Local
  or CI environments without decoder support should return structured QR errors
  such as `QRC_DECODER_UNAVAILABLE` or `QRC_MULTIPART_UNAVAILABLE`; these are
  accepted M1 validation states.
- Email remains intentionally hidden from the simplified `/analyze` browser
  surface. Backend email analysis and legacy email validation remain separate.
- `Policies` and `History` in the simplified sidebar are placeholders for M1 and
  must not be treated as completed policy or history product surfaces.
- Network redirect checks remain opt-in and should not be enabled by default.
- The runbook covers local validation. It does not claim hosted deployment or
  production-domain validation.

## Recommended Next Milestone

Resume E5 frontend policy selection as the next milestone:

- Add a focused policy selection surface for URL analysis, such as a
  page-appropriate `PolicyDrawer` or equivalent.
- Keep policy dry-run preview and policy audit logging as separate follow-up
  slices unless the next issue explicitly expands scope.
- Keep E6 history, compare, rerun, and feedback persistence separate until the
  remaining E5 policy UX and audit work is complete.

This keeps M1's simplified Analyze clarity intact while connecting the already
landed backend policy-pack foundation to the UI in a controlled next step.
