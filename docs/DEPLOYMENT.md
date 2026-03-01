# Deployment Baseline

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

## Operational Notes

- QR endpoint support in container requires:
  - `pyzbar` + `Pillow` Python deps
  - `libzbar0` system package
- If QR libraries are unavailable in target environment, `/api/v1/qr/scan` returns structured `503`/`400` error envelopes.

## CI Recommendation

Add a container build check on PRs to ensure deployment artifacts stay valid:

```bash
docker build -t lsh-api:ci .
```

## UI Contract Smoke Companion

After API container starts, run:

```bash
cd ui
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run smoke:api
```

This validates wrapper/error contract behavior from the frontend runtime perspective.
