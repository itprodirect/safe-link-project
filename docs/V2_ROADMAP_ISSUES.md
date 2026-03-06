# V2 Roadmap and Issue Tracker

Updated: 2026-03-05
Owner: Product + Engineering
Status: Execution tracker

This file is the planning source for GitHub issues and milestones for V2 delivery.

Umbrella GitHub epic issue: `#2`  
URL: https://github.com/itprodirect/safe-link-project/issues/2

## 1) How To Use This Tracker

1. Use existing milestones (`V2-Phase-1` ... `V2-Phase-8`) and phase epics (`#3`-`#10`).
2. Create child issues from each epic checklist as work is pulled.
3. Update this document with issue numbers and status.
4. Use labels:
   - `v2`
   - `epic`
   - `backend`
   - `frontend`
   - `api`
   - `ux`
   - `security`
   - `infra`
   - `docs`

## 2) Phase Roadmap (16 Weeks)

| Phase | Window | Objective | Exit Criteria |
|---|---|---|---|
| 1 | Weeks 1-2 | Foundation: shared services and v2 API skeleton | No regression, v2 endpoint scaffold, contract tests added |
| 2 | Weeks 3-4 | Unified Analyze workspace shell | URL/Email/QR all supported from one page |
| 3 | Weeks 5-6 | Verdict-first UX | Users can decide without reading raw JSON |
| 4 | Weeks 7-8 | Analyst mode deep inspection | Full evidence inspection in UI |
| 5 | Weeks 9-10 | Policy packs and suppression UX/API | Policy management in-app and persisted |
| 6 | Weeks 11-12 | History, compare, feedback loop | Rerun/compare + feedback persistence live |
| 7 | Weeks 13-14 | Hardening: security, reliability, performance | SLO/abuse controls and load checks pass |
| 8 | Weeks 15-16 | Stabilization and launch readiness | Docs complete, migration path defined, release candidate approved |

## 3) Epic Issue Map

Epic issues are now created and linked below.

| Epic ID | GitHub Issue | Title | Milestone | Status |
|---|---|---|---|---|
| E1 | [#3](https://github.com/itprodirect/safe-link-project/issues/3) | V2 Foundation: composition root, service layer, `/api/v2` skeleton | V2-Phase-1 | Open |
| E2 | [#4](https://github.com/itprodirect/safe-link-project/issues/4) | V2 Unified Analyze Workspace (URL/Email/QR) | V2-Phase-2 | Open |
| E3 | [#5](https://github.com/itprodirect/safe-link-project/issues/5) | V2 Verdict-First UX and action flow | V2-Phase-3 | Open |
| E4 | [#6](https://github.com/itprodirect/safe-link-project/issues/6) | V2 Analyst Mode and deep evidence surfaces | V2-Phase-4 | Open |
| E5 | [#7](https://github.com/itprodirect/safe-link-project/issues/7) | V2 Policy Packs and suppression management | V2-Phase-5 | Open |
| E6 | [#8](https://github.com/itprodirect/safe-link-project/issues/8) | V2 History, compare, and feedback loop | V2-Phase-6 | Open |
| E7 | [#9](https://github.com/itprodirect/safe-link-project/issues/9) | V2 Hardening: security, reliability, observability | V2-Phase-7 | Open |
| E8 | [#10](https://github.com/itprodirect/safe-link-project/issues/10) | V2 Stabilization, migration, and launch prep | V2-Phase-8 | Open |

## 4) Epic Breakdown and Child Issues

## E1: Foundation

### Scope

1. Shared orchestrator/service composition root.
2. Deduplicate CLI/API wiring.
3. Add `/api/v2/analyze` skeleton and contract tests.

### Child issues

- [x] `E1-I1` Build `AnalysisService` and `analysis_factory`.
- [x] `E1-I2` Move duplicated summary/wiring logic from adapters to service layer.
- [x] `E1-I3` Add `POST /api/v2/analyze` draft contract and response model.
- [x] `E1-I4` Add contract tests and parity tests versus v1 baseline ([#11](https://github.com/itprodirect/safe-link-project/issues/11)).
- [x] `E1-I5` Update architecture/docs status for shared service layer and v2 analyze ([#12](https://github.com/itprodirect/safe-link-project/issues/12)).

### Definition of done

1. Existing CLI/API behavior unchanged.
2. v2 endpoint exists with tests.
3. No adapter-level duplicated orchestration setup.

## E2: Unified Analyze Workspace

### Scope

1. Replace route-by-feature primary flow with `/analyze`.
2. Input tabs for URL, Email, QR in one workspace.

### Child issues

- [x] `E2-I1` Build unified input panel with type-specific validation.
- [x] `E2-I2` Add typed API client for v2 payloads.
- [x] `E2-I3` Add load/error/retry states.
- [x] `E2-I4` Add mode toggle scaffold (`Quick` vs `Analyst`).
- [x] `E2-I5` Add e2e smoke path for all three input types.

### Definition of done

1. One page handles all primary input types.
2. No raw JSON dependency for basic use.

## E3: Verdict-First UX

### Scope

1. Prioritize decision and action over debug details.

### Child issues

- [x] `E3-I1` Implement `VerdictCard`.
- [x] `E3-I2` Implement `WhyPanel` and recommendation ordering.
- [x] `E3-I3` Add action-level mapping (`safe/caution/avoid/block`).
- [ ] `E3-I4` Add UX copy pass for plain-language flow.
- [ ] `E3-I5` Add usability checks for decision speed.

### Definition of done

1. User can decide from first screen state.
2. Explanations are plain-language and confidence-aware.

## E4: Analyst Mode

### Scope

1. Deep inspection features without cluttering Quick mode.

### Child issues

- [ ] `E4-I1` Implement `EvidencePanel` with filtering.
- [ ] `E4-I2` Implement `DomainAnatomy` component.
- [ ] `E4-I3` Implement `RedirectPathView`.
- [ ] `E4-I4` Add suppression trace visibility.
- [ ] `E4-I5` Add compare-ready evidence model in API output.

### Definition of done

1. Analysts can inspect full evidence and derivation path.
2. Quick mode remains uncluttered.

## E5: Policy Packs

### Scope

1. Turn allowlist/suppression into first-class policy management.

### Child issues

- [ ] `E5-I1` Create policy pack data model and storage.
- [ ] `E5-I2` Add `/api/v2/policies` CRUD endpoints.
- [ ] `E5-I3` Build `PolicyDrawer` with scoped controls.
- [ ] `E5-I4` Add policy dry-run preview.
- [ ] `E5-I5` Add policy audit logging.

### Definition of done

1. Policy packs can be created, edited, and applied in UI.
2. Suppression behavior is transparent and test-covered.

## E6: History, Compare, Feedback

### Scope

1. Persist and reuse scan outcomes as product memory.

### Child issues

- [ ] `E6-I1` Add analysis run persistence and retrieval.
- [ ] `E6-I2` Build history list with filtering/search.
- [ ] `E6-I3` Build compare view.
- [ ] `E6-I4` Add rerun with same policy/options.
- [ ] `E6-I5` Add feedback API and UI controls.

### Definition of done

1. Users can find prior runs and compare deltas.
2. Feedback data captured and queryable.

## E7: Hardening

### Scope

1. Production-grade reliability and security controls.

### Child issues

- [ ] `E7-I1` Add request rate limiting and per-key quotas.
- [ ] `E7-I2` Add input redaction and retention controls.
- [ ] `E7-I3` Add tracing and latency/error dashboards.
- [ ] `E7-I4` Add load and stress tests for URL/QR flows.
- [ ] `E7-I5` Add incident runbook updates.

### Definition of done

1. Security controls active and documented.
2. Reliability targets measured and visible.

## E8: Stabilization and Launch

### Scope

1. Release candidate quality and migration confidence.

### Child issues

- [ ] `E8-I1` Fix launch-blocking defects and edge-case regressions.
- [ ] `E8-I2` Finalize v1 to v2 migration guide.
- [ ] `E8-I3` Add deprecation headers/timeline for v1 where applicable.
- [ ] `E8-I4` Final docs pass and launch checklists.
- [ ] `E8-I5` Release retrospective and follow-up backlog.

### Definition of done

1. Release candidate approved.
2. Docs and migration guidance are complete.

## 5) Cross-Cutting Workstreams

Track these in parallel labels and sprint planning:

1. Accessibility.
2. Localization readiness.
3. Performance budgets.
4. Telemetry quality and schema governance.
5. Contract versioning discipline.

## 6) Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Scope expansion overload | Slips and churn | Enforce phase gates and strict DoD |
| Frontend redesign drift from API semantics | Rework | Contract-first UI integration tests |
| False-positive regression during policy expansion | Trust loss | Golden tests + feedback loop triage |
| Hosted reliability issues | Adoption risk | Observability + load testing before launch |
| Migration friction for existing consumers | Breakage risk | v1 stability window + migration docs |

## 7) Governance Cadence

1. Weekly roadmap review: status, blockers, scope control.
2. Bi-weekly milestone review: phase exit criteria.
3. Monthly strategy review: reprioritize backlog with telemetry data.

## 8) Metrics Dashboard Starter

1. Decision speed metrics:
   - time to first verdict.
   - time to action.
2. Reliability:
   - API p95 latency.
   - error rates per flow.
3. Quality:
   - false-positive feedback ratio.
   - unresolved high-risk findings ratio.
4. UX:
   - mode usage split.
   - drop-off points in analyze flow.
