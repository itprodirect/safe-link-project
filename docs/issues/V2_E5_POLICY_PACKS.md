# E5: V2 Policy Packs and Suppression Management

Parent Epic: #2
Milestone: `V2-Phase-5`
Labels: `v2`, `epic`, `backend`, `api`, `frontend`, `security`

## Summary

Turn suppression controls into first-class policy packs with UI and API management.

## Scope

1. Add policy-pack model and persistence.
2. Add policy CRUD API endpoints.
3. Add policy management UX and dry-run behavior previews.

## Checklist

- [ ] Implement policy-pack data model.
- [ ] Add `/api/v2/policies` read/write endpoints.
- [ ] Build policy management UI (`PolicyDrawer` or equivalent).
- [ ] Add policy dry-run preview and diff output.
- [ ] Add policy audit events and tests.

## Definition of Done

1. Users can create, edit, apply, and test policies in-app.
2. Policy application effects are transparent and test-covered.

## References

- `docs/V2_BLUEPRINT.md`
- `docs/V2_ROADMAP_ISSUES.md`
