# E1: V2 Foundation (Composition Root, Service Layer, `/api/v2` Skeleton)

Parent Epic: #2
Milestone: `V2-Phase-1`
Labels: `v2`, `epic`, `backend`, `api`, `docs`

## Summary

Build the v2 execution foundation without breaking existing v1 behavior.

## Scope

1. Introduce shared orchestrator/service composition root.
2. Deduplicate CLI/API orchestrator wiring and summary-builder duplication.
3. Add draft `POST /api/v2/analyze` endpoint shape and contract tests.
4. Keep all current v1 endpoints and outputs stable.

## Checklist

- [ ] Add `AnalysisService` and composition root module.
- [ ] Move duplicated URL/email orchestrator setup out of adapters.
- [ ] Add v2 analyze request/response models (draft).
- [ ] Add parity tests validating no regressions in v1 behavior.
- [ ] Update architecture docs to include the new service boundary.

## Definition of Done

1. No user-visible regressions in CLI/API v1 flows.
2. Shared service layer is consumed by both adapters.
3. v2 analyze skeleton exists and is test-covered.

## References

- `docs/V2_BLUEPRINT.md`
- `docs/V2_ROADMAP_ISSUES.md`
- `docs/ARCHITECTURE.md`
