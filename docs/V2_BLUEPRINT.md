# Link Safety Hub V2 Blueprint

Updated: 2026-03-04
Owner: Product + Engineering
Status: Draft for execution planning

## 1) Product Thesis

V2 should be a decision product, not only a detector product.

1. Primary promise: "Tell me if this is safe, why, and what to do next in under 20 seconds."
2. UX priority: verdict first, technical detail second.
3. Audience split: `Quick Mode` (everyday users) and `Analyst Mode` (power users).
4. Keep offline-first default behavior, with explicit opt-in for network checks.
5. Keep strict versioned API contracts.

## 2) North-Star Outcomes

1. Time to first verdict (offline): <= 3 seconds median.
2. Time to actionable decision: <= 20 seconds median.
3. False-positive dispute rate on high-confidence alerts: <= 10%.
4. User understanding: >= 80% of users report they understand "why flagged."
5. Repeat usage (30-day return): >= 40%.

## 3) Personas and Jobs To Be Done

1. Everyday user: "Should I click this?"
2. Parent/family user: "Explain this clearly and safely."
3. Helpdesk user: "Triage quickly and escalate with evidence."
4. Security analyst: "Inspect deeply, tune policy, and export incident artifacts."

## 4) V2 Scope

### V2 Core

1. Unified Analyze workspace for URL, Email, and QR flows.
2. Quick and Analyst modes with shared backend semantics.
3. Verdict-first UI with structured explanation panels.
4. Policy packs (allowlist category/finding controls) in UI.
5. Analysis history and compare/rerun.
6. User feedback loop (`false_positive`, `true_positive`, `uncertain`).
7. `/api/v2` contract introduction while preserving `/api/v1`.

### Deferred (V2.1+)

1. Browser extension.
2. Mobile native apps.
3. Full case-management workflow.

## 5) Information Architecture

1. `/analyze`: single primary workspace.
2. `/history`: previous analyses, filters, compare.
3. `/policies`: policy packs and suppression management.
4. `/integrations`: API keys, webhooks, export config.
5. `/settings`: privacy, retention, performance defaults.
6. `/help`: confidence guidance and safety playbooks.

## 6) Core User Flows

1. Input and parse preview:
   - URL paste, email headers paste, QR upload.
   - Normalize and preview destination before execution.
2. Verdict:
   - Primary verdict card with risk, confidence, and next action.
3. Explain:
   - Top reasons first.
   - Expandable evidence for technical users.
4. Act:
   - "Open official site instead."
   - "Copy safe summary."
   - "Escalate with report."
5. Analyst workflow:
   - Enable advanced controls and policy overrides.
   - Inspect module-level evidence and suppression traces.

## 7) UX Component Blueprint

1. `AnalyzeInputPanel`
   - Input tabs (`url`, `email_headers`, `qr_image`).
   - Strict validation and copy/paste-friendly examples.
2. `VerdictCard`
   - Risk band, confidence, action-level, primary recommendation.
3. `WhyPanel`
   - Top 3 reasons in plain language.
4. `EvidencePanel`
   - Module/category/evidence rows with filter/search.
5. `DomainAnatomy`
   - Registrable domain highlight and suspicious token emphasis.
6. `RedirectPathView`
   - Chain timeline with domain changes and anomalies.
7. `PolicyDrawer`
   - Category suppression and finding-token controls.
   - Dry-run preview of suppression impact.
8. `HistoryTable`
   - Filter, search, rerun, and compare.
9. `CompareView`
   - Side-by-side scan deltas.
10. `ExportPanel`
   - JSON, family summary, incident bundle outputs.

## 8) Visual and Interaction Direction

1. Intentional visual language:
   - Forensic clarity, high signal contrast, no "debug scaffold" look.
2. Typography:
   - One expressive heading family plus one highly readable body family.
3. Motion:
   - Meaningful transitions (`input -> analyzing -> verdict`).
4. Cognitive load:
   - One primary CTA per state.
5. Accessibility:
   - WCAG 2.2 AA, keyboard parity for critical actions.

## 9) Frontend Technical Architecture

1. Keep Next.js App Router.
2. Add typed API client generated from OpenAPI (or a shared contracts package).
3. Add runtime payload validation before rendering.
4. Add query/cache orchestration (for retries and stale-data policy).
5. Add global request timeout, error boundary, and offline boundary.
6. Persist mode preference (`Quick` vs `Analyst`) and key UI state.
7. Add telemetry hooks for UX latency and friction points.

## 10) Backend V2 Architecture

Keep current strengths, reduce duplication, prepare for scale.

1. Add composition root (`analysis_factory`) for orchestrator assembly.
2. Move duplicated adapter wiring into shared services.
3. Add `AnalysisService` as primary application entrypoint.
4. Add `PolicyService` for suppression and profile management.
5. Add `ResultService` for history, compare, export.
6. Keep detector modules stateless and deterministic.
7. Add optional async path for deep network and batch checks.

## 11) Suggested Package Reorganization

1. `src/lsh/domain/`
   - entities/value objects (`Finding`, `Verdict`, `PolicyPack`).
2. `src/lsh/application/`
   - use-case services (`AnalyzeInput`, `CompareResult`, `SaveResult`).
3. `src/lsh/detectors/`
   - migrated module analyzers.
4. `src/lsh/policies/`
   - category/finding suppression rules and pack registry.
5. `src/lsh/contracts/`
   - versioned request/response schemas.
6. `src/lsh/infrastructure/`
   - API adapter, CLI adapter, persistence adapters, external clients.

## 12) API V2 Contract Proposal

Introduce v2 without breaking v1.

### New endpoints

1. `POST /api/v2/analyze`
2. `GET /api/v2/analysis/{id}`
3. `POST /api/v2/analyze/batch` (optional async)
4. `GET /api/v2/policies`
5. `PUT /api/v2/policies/{id}`
6. `POST /api/v2/feedback`
7. `GET /api/v2/health`

### Contract principles

1. Preserve `schema_version` and explicit `mode`.
2. Keep wrappers stable (`item`/`items`) as first-class.
3. Emit clear deprecation headers for v1 transitions.
4. Keep structured error envelopes for all explicit API errors.

## 13) Data Model V2

1. `AnalysisRun`
   - id, input hash, input type, mode, policy id, created_at, latency_ms.
2. `Artifact`
   - normalized subject, canonical host/domain, parse metadata.
3. `Verdict`
   - risk score, severity, confidence, summary, action level.
4. `FindingRecord`
   - module, category, risk delta, confidence, evidence, suppressibility.
5. `PolicyPack`
   - category scopes, finding tokens, network settings, display mode defaults.
6. `FeedbackRecord`
   - user label and optional notes.
7. `AuditEvent`
   - policy updates, reruns, and export activity.

## 14) Scoring and Explainability V2

1. Keep risk score as 0-100.
2. Add explicit `action_level` (`safe`, `caution`, `avoid`, `block`).
3. Add confidence provenance ("highest impact finding + reason").
4. Rank reasons by impact and user clarity.
5. Make suppression transparent in output.
6. Include deterministic score-breakdown section in Analyst mode.

## 15) Policy System V2

1. Built-in packs:
   - `Default Family`
   - `Default Analyst`
   - `Enterprise Strict`
2. Custom packs:
   - domain allowlist, category suppression, finding-token suppression.
3. Policy dry-run:
   - replay result under another policy without mutating stored baseline result.

## 16) Technical Option Matrix

| Decision | Option A | Option B | Recommended path |
|---|---|---|---|
| Persistence | SQLite local-first | Managed Postgres | Repository abstraction now; SQLite dev + Postgres hosted |
| Async jobs | In-process background | Queue worker | In-process for V2 core; queue for batch/deep scans |
| API typing | Manual interfaces | OpenAPI-generated | OpenAPI-generated and shared across UI/API |
| Hosted auth | None | API key + roles | API key for V2 hosted; preserve no-auth local mode |
| Signal model | Offline only | Hybrid optional enrichment | Keep offline default; optional enrichers behind policy |

## 17) Security and Privacy Plan

1. Redact sensitive input by default in logs.
2. Store hashed identifiers where possible.
3. Add retention policy controls and purge jobs.
4. Show explicit user consent prompt when network checks are enabled.
5. Strict file-size/type limits on uploads.
6. Add rate limits and per-key quotas for hosted API.
7. Add redaction profiles for export bundles.

## 18) Observability and Reliability

1. Metrics:
   - latency by flow and mode.
   - module error rates.
   - decoder availability.
   - feedback distribution by category.
2. Tracing:
   - parse, detect, score, and format stage durations.
3. Logging:
   - structured events with analysis id and policy id.
4. SLO:
   - 99.5% API availability for hosted deployments.

## 19) Testing Strategy

1. Keep detector unit tests and adversarial fixtures.
2. Add golden snapshot tests for verdict and reason ordering.
3. Add mode parity tests (`Quick` vs `Analyst` output consistency).
4. Add API contract tests from generated schema.
5. Add UI path tests for top user journeys and failure journeys.
6. Add load tests for URL and QR paths.
7. Add parser fuzz tests for hostile URLs and malformed inputs.

## 20) Migration Plan

1. Phase 1:
   - add composition root and shared services under current adapters.
2. Phase 2:
   - introduce `/api/v2/analyze` with full contract tests.
3. Phase 3:
   - launch new Analyze workspace behind feature flag.
4. Phase 4:
   - add policies/history/feedback.
5. Phase 5:
   - publish v1 migration guide and deprecation timeline.
6. Phase 6:
   - remove v1 legacy keys only after telemetry shows low usage.

## 21) Sprint Blueprint (16 weeks, 8 sprints)

1. Sprint 1 (Weeks 1-2)
   - service composition root
   - adapter dedup
   - v2 endpoint skeleton
2. Sprint 2 (Weeks 3-4)
   - unified Analyze workspace shell
   - typed API client integration
3. Sprint 3 (Weeks 5-6)
   - verdict-first UX and action panel
4. Sprint 4 (Weeks 7-8)
   - analyst evidence panels and deep inspection UI
5. Sprint 5 (Weeks 9-10)
   - policy packs and suppression management UI/API
6. Sprint 6 (Weeks 11-12)
   - history, compare, rerun, feedback
7. Sprint 7 (Weeks 13-14)
   - performance, reliability, security hardening
8. Sprint 8 (Weeks 15-16)
   - stabilization, docs, migration, release readiness

## 22) V2 Differentiators

1. URL character diff lens (suspicious vs expected domain).
2. One-click "open official site" safe action.
3. Trust story timeline (how score was constructed).
4. Inline education cards for common phishing tricks.
5. One-click analyst export bundle.
6. Policy impact simulator against historical results.

## 23) Immediate Decision Checklist

1. Launch persona priority:
   - everyday-first
   - analyst-first
   - balanced dual-mode
2. Retention policy:
   - ephemeral
   - fixed window
   - configurable
3. Hosted auth level:
   - none
   - API key
   - API key + role model
4. Persistence starting point:
   - SQLite-first
   - Postgres-first
5. Release model:
   - big-bang
   - feature-flagged progressive rollout

## 24) Recommended Starting Choices

1. Balanced dual-mode with Quick as default.
2. Repository abstraction now, SQLite local and Postgres hosted.
3. API keys for hosted mode; preserve local no-auth mode.
4. Feature-flagged incremental rollout.
5. Priority order:
   - verdict UX
   - policy UI
   - history and feedback.
