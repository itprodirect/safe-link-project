# E4: V2 Analyst Mode and Deep Evidence Surfaces

Parent Epic: #2
Milestone: `V2-Phase-4`
Labels: `v2`, `epic`, `frontend`, `backend`, `ux`
Status: Locally complete in PR #13 (`codex/analyst-mode-url-slice`)

## Summary

Provide deep inspection tools for analysts without overwhelming Quick mode users.

## Scope

1. Add evidence-focused analyst components and filters.
2. Expose structured domain anatomy and redirect path insights.
3. Make suppression traces visible in analyst output.
4. Add compare-ready evidence keys to the v2 analyst contract for future history/delta views.

## Checklist

- [x] Build `EvidencePanel` with filtering and search.
- [x] Build `DomainAnatomy` visual component.
- [x] Build `RedirectPathView` timeline.
- [x] Add suppression trace visibility in API/UI.
- [x] Add compare-ready evidence model in API output.
- [x] Add analyst-mode behavior tests.

## Definition of Done

1. Analysts can inspect full finding provenance in-app.
2. URL analyst output includes suppression traces and compare-stable evidence keys.
3. Quick mode remains uncluttered and focused on decision output.

## References

- `docs/V2_BLUEPRINT.md`
- `docs/V2_ROADMAP_ISSUES.md`
