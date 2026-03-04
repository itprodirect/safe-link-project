# E2: V2 Unified Analyze Workspace

Parent Epic: #2
Milestone: `V2-Phase-2`
Labels: `v2`, `epic`, `frontend`, `api`, `ux`

## Summary

Ship one primary `/analyze` workspace for URL, email, and QR flows.

## Scope

1. Unify current route-by-feature flows behind one primary workspace.
2. Add typed client integration with v2 contract shape.
3. Support URL, email headers, and QR upload from a single view.

## Checklist

- [ ] Build a shared input panel with URL/email/QR tabs.
- [ ] Add strict validation per input type.
- [ ] Integrate typed API client for v2 payloads.
- [ ] Add loading, error, timeout, and retry states.
- [ ] Add integration tests for all three input types.

## Definition of Done

1. A user can complete URL/email/QR analysis from one page.
2. Basic user flow does not rely on raw JSON rendering.

## References

- `docs/V2_BLUEPRINT.md`
- `docs/V2_ROADMAP_ISSUES.md`
- `docs/NEXTJS_UI_VALIDATION.md`
