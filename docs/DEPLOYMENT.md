# Deployment Baseline

For deployment platform tradeoffs and recommendation paths, see:

- `docs/DEPLOYMENT_OPTIONS.md`

## Scope

This runbook covers the current baseline deployment path for the FastAPI adapter:

- local containerized run (`Dockerfile`, `docker-compose.yml`)
- one hosted profile example (Render)

## Local Docker Run

### Build

```bash
docker build -t link-safety-hub-api:local .
```

### Run

```bash
docker run --rm -p 8000:8000 --name lsh-api link-safety-hub-api:local
```

### Health check

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## Local Compose Run

```bash
docker compose up --build
```

Stop:

```bash
docker compose down
```

## Hosted Profile Example (Render)

### Service settings

- Runtime: Docker
- Build context: repo root
- Dockerfile path: `Dockerfile`
- Port: `8000`

### Health check path

```text
/health
```

### Suggested instance env

- `PYTHONUNBUFFERED=1`
- `LSH_API_CORS_ALLOW_ORIGINS=https://<your-ui-domain>`
- `LSH_API_INCLUDE_QR_LEGACY_KEYS=false` (optional once integrations are wrapper-first)

## Operational Notes

- QR endpoint support in container requires:
  - `pyzbar` + `Pillow` Python deps
  - `libzbar0` system package
- If QR libraries are unavailable in target environment, `/api/v1/qr/scan` returns structured `503`/`400` error envelopes.

## CI Recommendation

Use a runtime smoke gate on PRs so CI validates deploy behavior, not just image build:

```bash
docker build -t lsh-api:ci .
docker run -d -p 8000:8000 --name lsh-api-ci lsh-api:ci
curl http://127.0.0.1:8000/health
cd ui
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 NEXT_PUBLIC_UI_ORIGIN=http://127.0.0.1:3000 npm run smoke:api
```

## UI Contract Smoke Companion

After API container starts, run:

```bash
cd ui
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 NEXT_PUBLIC_UI_ORIGIN=http://127.0.0.1:3000 npm run smoke:api
```

This validates wrapper/error contract behavior from the frontend runtime perspective.
The QR portion uses `multipart/form-data` upload flow (no server-local `image_path` required).

## Hosted Validation Pass

Once the API is deployed, run this sequence against the hosted URL:

```bash
# 1) Reachability
curl https://<api-domain>/health

# 2) CORS preflight (replace UI origin)
curl -i -X OPTIONS "https://<api-domain>/api/v1/url/check" \
  -H "Origin: https://<ui-domain>" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type"

# 3) Contract smoke from UI runtime perspective
cd ui
NEXT_PUBLIC_API_BASE_URL=https://<api-domain> \
NEXT_PUBLIC_UI_ORIGIN=https://<ui-domain> \
npm run smoke:api
```

Expected CORS signal:

- `access-control-allow-origin` matches your UI origin (or `*` if explicitly configured)
