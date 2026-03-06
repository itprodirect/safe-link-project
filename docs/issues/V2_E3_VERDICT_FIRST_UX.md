# E3: V2 Verdict-First UX and Action Flow

Parent Epic: #2
Milestone: `V2-Phase-3`
Labels: `v2`, `epic`, `frontend`, `ux`

## Summary

Prioritize user decisions and safe next actions before deep technical detail.

## Scope

1. Implement a primary verdict card with clear action-level mapping.
2. Implement top reasons and recommended actions in plain language.
3. Keep technical evidence available but secondary.

## Checklist

- [x] Build `VerdictCard` component.
- [x] Build `WhyPanel` with ranked reasons.
- [x] Add action-level mapping (`safe`, `caution`, `avoid`, `block`).
- [ ] Add plain-language copy pass for all major outcomes.
- [ ] Add UX tests for first-decision clarity and speed.

## Definition of Done

1. Users can decide without inspecting raw detector output.
2. Recommendations are confidence-aware and action-oriented.

## References

- `docs/V2_BLUEPRINT.md`
- `docs/V2_ROADMAP_ISSUES.md`
