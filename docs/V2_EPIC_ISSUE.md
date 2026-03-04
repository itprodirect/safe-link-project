# Epic: Execute Link Safety Hub V2 Blueprint

## Summary

Track end-to-end execution of the V2 product and architecture plan:

- Blueprint: `docs/V2_BLUEPRINT.md`
- Roadmap and issue map: `docs/V2_ROADMAP_ISSUES.md`

This epic covers all V2 phases from architecture foundation through release stabilization.

## Objectives

1. Deliver a verdict-first user experience for URL, Email, and QR analysis.
2. Preserve backend strengths (offline-first, modular detection, contract stability).
3. Introduce `/api/v2` without breaking `/api/v1` consumers.
4. Add policy management, history, compare, and feedback loops.
5. Meet reliability, security, and observability requirements for hosted usage.

## Epic Checklist

- [ ] E1 Foundation: composition root, service layer, `/api/v2` skeleton (#3)
- [ ] E2 Unified Analyze workspace (URL/Email/QR) (#4)
- [ ] E3 Verdict-first UX and action model (#5)
- [ ] E4 Analyst mode evidence surfaces (#6)
- [ ] E5 Policy packs and suppression management (#7)
- [ ] E6 History, compare, and feedback loop (#8)
- [ ] E7 Hardening: security, reliability, observability (#9)
- [ ] E8 Stabilization, migration, and launch prep (#10)

## Exit Criteria

1. V2 core flows are production-ready and documented.
2. Migration path and deprecation guidance are published.
3. Reliability/security baselines are verified in hosted validation.

## References

- `docs/V2_BLUEPRINT.md`
- `docs/V2_ROADMAP_ISSUES.md`
- `docs/API_INTEGRATION.md`
- `docs/ARCHITECTURE.md`
