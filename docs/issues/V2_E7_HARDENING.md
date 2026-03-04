# E7: V2 Hardening (Security, Reliability, Observability)

Parent Epic: #2
Milestone: `V2-Phase-7`
Labels: `v2`, `epic`, `security`, `infra`, `backend`, `api`

## Summary

Harden hosted readiness with security controls, reliability instrumentation, and load validation.

## Scope

1. Add abuse controls (rate limit, quotas, guardrails).
2. Add privacy controls (redaction, retention lifecycle).
3. Add service-level metrics, tracing, and reliability dashboards.
4. Validate performance with load tests.

## Checklist

- [ ] Add request rate limiting and per-key quotas.
- [ ] Add logging redaction and retention controls.
- [ ] Add tracing/metrics for critical analysis paths.
- [ ] Add load and stress tests for URL and QR endpoints.
- [ ] Update runbooks and incident-response docs.

## Definition of Done

1. Hardening controls are active, verified, and documented.
2. Reliability objectives are measured and visible.

## References

- `docs/V2_BLUEPRINT.md`
- `docs/V2_ROADMAP_ISSUES.md`
- `docs/SECURITY.md`
