# Deployment Options Research (Session Closeout)

Updated: 2026-03-01

Purpose: capture deployment options, tradeoffs, and a concrete next-step plan so the next session can execute quickly.

## Current Project Shape

- Frontend: Next.js app in `ui/`
- Backend: FastAPI app in `src/lsh/adapters/api.py`
- Backend runtime dependency: system `libzbar0` in [Dockerfile](../Dockerfile) for QR decoding
- Existing validation assets:
  - container runtime smoke in CI
  - UI contract smoke script: `ui/scripts/api-contract-smoke.mjs`
  - CORS env support: `LSH_API_CORS_ALLOW_ORIGINS`

Implication: this architecture naturally maps to a split frontend/backend deployment model.

## Option Matrix

### Option A (Recommended): Vercel for Next.js UI + AWS App Runner for FastAPI API

Why it fits:

- Vercel is first-class for Next.js with low setup overhead.
- App Runner is container-native and aligns with current Dockerized FastAPI + `libzbar0`.
- Keeps backend on AWS (good fit for existing AWS preference and ops tooling).

Pros:

- fastest path to production-like MVP
- preserves current API runtime assumptions
- clean separation of concerns (frontend deploy velocity + backend container control)

Cons:

- two platforms to operate (Vercel + AWS)
- cross-platform observability needs explicit setup

### Option B: All AWS (Amplify Hosting for Next.js + App Runner for API)

Why it fits:

- single-cloud operations model
- managed Next.js hosting in AWS + managed container API in AWS

Pros:

- unified billing/IAM/governance stack
- easy alignment with Route 53 + AWS-native security controls

Cons:

- frontend DX and preview workflow may be slower vs Vercel depending on team preferences
- Amplify Next.js feature/limit considerations must be reviewed for your exact app usage

### Option C: All AWS with maximum control (CloudFront + ECS/Fargate + ALB, and UI on Amplify or ECS)

Why it fits:

- strongest control over networking, scaling, and enterprise security patterns

Pros:

- maximum flexibility and enterprise-grade topology control
- easy deep integration with existing VPC, WAF, security tooling

Cons:

- highest operational complexity
- longest time to first stable hosted MVP

### Option D: Full Vercel (Next.js + FastAPI function)

Why it might fit:

- single platform and very quick developer workflow

Why it is weaker for this project now:

- FastAPI runs as a Vercel Function bundle; this project currently expects container/system package behavior (`libzbar0` path)
- request/response payload limits and function model can become a constraint for upload-heavy QR use cases

## Recommendation

Use Option A now:

1. Deploy backend container to AWS App Runner.
2. Deploy Next.js UI to Vercel.
3. Point UI `NEXT_PUBLIC_API_BASE_URL` to App Runner custom domain.
4. Set backend `LSH_API_CORS_ALLOW_ORIGINS=https://<vercel-ui-domain>`.
5. Run hosted validation pass and close roadmap item.

This gives the fastest credible hosted MVP while preserving a clean path to all-AWS later.

## AWS-First Variant Recommendation

If you want all workloads under AWS from day one, choose Option B:

1. Host Next.js on Amplify Hosting.
2. Host API on App Runner.
3. Keep same API contract + smoke checks.
4. Set CORS to Amplify domain.

## Next Session Execution Plan

1. Provision `api.<domain>` for App Runner service.
2. Configure App Runner env:
   - `LSH_API_CORS_ALLOW_ORIGINS=https://<ui-domain>`
   - `LSH_API_INCLUDE_QR_LEGACY_KEYS=false` (optional when consumers are wrapper-first)
3. Deploy UI (`Vercel` or `Amplify`) and set:
   - `NEXT_PUBLIC_API_BASE_URL=https://api.<domain>`
4. Run hosted validation:
   - `GET /health`
   - CORS preflight to `/api/v1/url/check`
   - `npm run smoke:api` from `ui/` against hosted URLs
5. Record results in `SESSION_LOG.md` and mark `docs/ROADMAP.md` Session 9 item 3 complete.

## Decision Signals to Track

- latency on `/api/v1/url/check` and `/api/v1/qr/scan`
- cold-start behavior and cost
- QR decode reliability in hosted runtime
- operational simplicity for your team

## Sources (Research Snapshot)

- Vercel Next.js deployment model: https://vercel.com/docs/frameworks/full-stack/nextjs
- Vercel FastAPI support: https://vercel.com/docs/frameworks/backend/fastapi
- Vercel Functions limits (bundle, duration, payload): https://vercel.com/docs/functions/limitations
- AWS App Runner image-based services: https://docs.aws.amazon.com/apprunner/latest/dg/service-source-image.html
- AWS App Runner autoscaling knobs: https://docs.aws.amazon.com/apprunner/latest/dg/manage-autoscaling.html
- AWS App Runner custom domains: https://docs.aws.amazon.com/apprunner/latest/dg/manage-custom-domains.html
- AWS App Runner VPC outbound access: https://docs.aws.amazon.com/apprunner/latest/dg/network-vpc.html
- AWS App Runner pricing: https://aws.amazon.com/apprunner/pricing/
- AWS Amplify Next.js SSR deployment: https://docs.aws.amazon.com/amplify/latest/userguide/deploy-nextjs-app.html
- AWS Amplify Next.js support matrix: https://docs.aws.amazon.com/amplify/latest/userguide/ssr-amplify-support.html
- AWS ECS ALB integration reference: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/alb.html
- AWS API Gateway HTTP API CORS behavior: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-cors.html
