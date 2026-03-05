# Phased Delivery Plan

## Guiding principles

- Each phase delivers a usable increment; no phase is purely infrastructure with no visible output.
- Data pipeline and API are built together, source by source.
- Frontend features start only when the API endpoint they consume is tested and stable.
- Frontend flagship slices must pass a foundations gate (tokens, primitives, and quality rails) before feature-specific polish.
- Each phase ends with working tests, passing lint, and a demoable artifact.
- Deployment assumptions are tracked in `.planning/deployment-strategy.md` and updated when phase design changes runtime needs.

## Program hold (effective 2026-03-04)

- Progression to new expansion phases is paused until source-strategy and trend-history reliability concerns are closed.
- `Phase S` (Source strategy stabilization + trend history recovery) is now a mandatory gate before advancing to `Phase 3`, `Phase 4`, or `Phase 5`.
- If any `Phase S` acceptance criteria fail, subsequent phase work is limited to bug fixes and stabilization only.

---

## Phase 0 - Data foundation + GIAS baseline

**Goal:** Prove the full Bronze -> Staging -> Gold pipeline with one source, expose schools via API, and deliver a production-grade frontend baseline plus search/map experience.

### Detailed design

- `.planning/phases/phase-0/README.md`
- `.planning/phases/phase-0/0A-data-platform-baseline.md`
- `.planning/phases/phase-0/0E-configuration-foundation.md`
- `.planning/phases/phase-0/0B-gias-pipeline.md`
- `.planning/phases/phase-0/0C-postcode-search-api.md`
- `.planning/phases/phase-0/0D1-web-foundations.md`
- `.planning/phases/phase-0/0D-web-search-map.md`

### Deliverables

1. **0A: Data platform baseline** - PostGIS runtime, migration framework, pipeline base contracts, CLI orchestration.
2. **0E: Configuration foundation** - typed backend settings, centralized environment access, and local `.env` workflow.
3. **0B: GIAS pipeline** - Bronze -> Staging -> Gold load into `schools` with PostGIS geometry and idempotent upsert semantics.
4. **0C: Postcode search API** - Postcodes.io resolution + cache, `GET /api/v1/schools?postcode=...&radius=...`, spatial radius query sorted by distance.
5. **0D1: Web foundations** - brand/theming baseline, design tokens, reusable component primitives, and frontend quality rails.
6. **0D2: Web search + map** - postcode form, list results, and Leaflet markers composed from 0D1 foundations and backed by Phase 0 API contract.

### Exit criteria

- User can enter a postcode and see nearby schools on a list and map.
- Pipeline is re-runnable and idempotent.
- Runtime configuration is centralized and typed (no ad-hoc `os.environ` access across features).
- OpenAPI contract is updated and consumed by web client/types.
- Web foundations are in place (tokenized theme + reusable primitives) and used by the Phase 0 search/map UI.
- Frontend quality rails for accessibility, responsiveness, performance, and code quality are defined and passing for the Phase 0 slice.
- Import boundary tests pass, with lint and tests green.

### Dependencies

- None.

---

## Phase 1 - School profiles + DfE metrics + Ofsted headline

**Goal:** Add depth to school records with DfE pupil characteristics plus the latest Ofsted headline rating on profile.

### Detailed design

- `.planning/phases/phase-1/README.md`
- `.planning/phases/phase-1/1A-source-contract-gate.md`
- `.planning/phases/phase-1/1B-dfe-characteristics-pipeline.md`
- `.planning/phases/phase-1/1C-ofsted-latest-pipeline.md`
- `.planning/phases/phase-1/1D-school-profile-api.md`
- `.planning/phases/phase-1/1E-school-trends-api.md`
- `.planning/phases/phase-1/1F-web-routing-navigation-foundation.md`
- `.planning/phases/phase-1/1F1-web-component-expansion-data-viz-baseline.md`
- `.planning/phases/phase-1/1G-web-school-profile-page.md`
- `.planning/phases/phase-1/1H-phase-1-quality-gates.md`

### Deliverables

1. **Source contract gate (blocking)** - verify all source endpoints are real/callable and required fields are present before source-dependent implementation.
2. **DfE characteristics pipeline** - Bronze -> Staging -> Gold for verified school-level demographic fields from callable DfE endpoints.
3. **Ofsted latest pipeline** - Bronze -> Staging -> Gold latest inspection outcome per school (headline rating + date).
4. **Gold `school_demographics_yearly` table** - typed yearly columns for core demographic metrics (not metric-key EAV) with explicit coverage flags for unsupported source fields.
5. **Gold `school_ofsted_latest` table** - one latest Ofsted snapshot per school.
6. **School profile API** - `GET /api/v1/schools/{urn}` returning core info + latest demographics + latest Ofsted headline.
7. **Trends API** - `GET /api/v1/schools/{urn}/trends` returning available yearly history with deterministic delta behavior and explicit partial-history metadata.
8. **Frontend: navigation shell and site chrome** - routing, site header/footer, mobile navigation, breadcrumbs, skip-to-content, 404 page, and icon library.
9. **Frontend: component expansion and data visualization baseline** - expanded shared UI primitives (Badge, Tabs, Tooltip, Toast), bespoke data components (StatCard, TrendIndicator, RatingBadge, Sparkline, MetricGrid), and chart library baseline.
10. **Frontend: school profile page** - headline stats (including Ofsted badge) plus trend visuals that handle sparse history, composed from shared primitives.
11. **Frontend: quality gates** - mandatory phase sign-off checklist.

### Exit criteria

- User can open a school profile and view demographic indicators, trend direction, and latest Ofsted rating.
- Historical data covers 3+ years where available.
- Source contract gate is passed and documented for each source-dependent deliverable.

### Dependencies

- Phase 0.

---

## Phase 2 - Ofsted timeline + area context

**Goal:** Add full inspection history timeline and area-level context (crime, deprivation) to profile depth.

### Detailed design

- `.planning/phases/phase-2/README.md`
- `.planning/phases/phase-2/2A-source-contract-gate.md`
- `.planning/phases/phase-2/2B-ofsted-timeline-pipeline.md`
- `.planning/phases/phase-2/2C-ons-imd-pipeline.md`
- `.planning/phases/phase-2/2D-police-crime-context-pipeline.md`
- `.planning/phases/phase-2/2E-school-profile-api-extensions.md`
- `.planning/phases/phase-2/2F-web-profile-area-context-enhancements.md`
- `.planning/phases/phase-2/2G-phase-2-quality-gates.md`

### Deliverables

1. **Source contract gate (blocking)** - verify all Phase 2 source endpoints/fields and lock fallback paths before implementation.
2. **Ofsted timeline pipeline extension** - Bronze -> Staging -> Gold for full inspection record history.
3. **Gold `ofsted_inspections` table** - full inspection timeline per school.
4. **ONS IMD pipeline** - Bronze -> Staging -> Gold for deprivation by LSOA.
5. **Gold `area_deprivation` table** - IMD decile and IDACI child-poverty proxy by LSOA.
6. **Police UK pipeline** - Bronze -> Staging -> Gold for aggregated crime context near schools.
7. **Gold `area_crime_context` table** - monthly crime aggregates per school location.
8. **School profile API extensions** - include Ofsted timeline, IMD decile, and crime summary.
9. **Frontend: profile enhancements** - Ofsted badge + timeline, area context section.
10. **Phase 2 quality gates** - mandatory closeout checklist and sign-off sequence.

### Exit criteria

- School profiles show latest Ofsted rating and inspection history timeline.
- Area context is visible (deprivation decile and crime summary).
- New pipelines are idempotent and tested.

### Dependencies

- Phase 1.

---

## Phase H - Hardening (data reliability + completeness + resilience)

**Goal:** Convert data-quality RCA findings into production-grade hardening across ingestion correctness, historical depth, completeness transparency, and operational safety.

### Detailed design

- `.planning/phases/phase-hardening/README.md`
- `.planning/phases/phase-hardening/H1-pipeline-run-policy-quality-gates.md`
- `.planning/phases/phase-hardening/H2-source-normalization-contracts.md`
- `.planning/phases/phase-hardening/H3-historical-demographics-backfill-lookback.md`
- `.planning/phases/phase-hardening/H4-data-completeness-contract-api-ui.md`
- `.planning/phases/phase-hardening/H5-operational-observability-freshness-coverage-drift.md`
- `.planning/phases/phase-hardening/H6-pipeline-resilience-performance-hardening.md`
- `.planning/phases/phase-hardening/H7-hardening-quality-gates-signoff.md`

### Deliverables

1. **H1: Pipeline run policy and quality gates** - deterministic run outcomes with hard-fail protection when downloaded/staged/promoted counters violate quality rules.
2. **H2: Source normalization contracts** - versioned per-source normalization and schema drift controls at the Bronze -> Staging boundary.
3. **H3: Historical demographics backfill** - configurable lookback and idempotent historical ingestion for trend depth where source data exists.
4. **H4: Data completeness contract** - explicit section-level availability/reason metadata in profile/trends API and user-facing UI states.
5. **H5: Operational observability** - freshness, coverage, and drift metrics with actionable alerting and runbook support.
6. **H6: Pipeline resilience and performance** - retries, checkpoints, resume support, chunked processing, and throughput/recovery hardening.
7. **H7: Hardening quality gates** - mandatory sign-off gates proving hardening outcomes in one repository state.

### Exit criteria

- Pipeline runs cannot silently succeed when staged/promoted data quality fails.
- Source normalization is contract-driven, versioned, and test-covered for every active feed.
- Historical demographics support configurable lookback and produce multi-year trends where available.
- API and UI expose clear completeness metadata with user-friendly messaging.
- Freshness and coverage drift are continuously monitored with alerting.
- Recovery and performance drills pass for large-source and interruption scenarios.
- Hardening quality gates pass (`H7`) with evidence captured.

### Dependencies

- Phase 2 for complete profile and source surface area.
- Can run alongside late UX polish only when API contract changes are coordinated.

---

## Phase S - Source strategy stabilization + trend history recovery (blocking)

**Goal:** Replace single-year demographics source behavior with a verified multi-year source strategy so trend coverage is reliable, explainable, and phase-inclusive.
**Status:** S1-S6 complete (2026-03-04), with sign-off evidence in `.planning/phases/phase-source-stabilization/signoff-2026-03-04.md` and S6 implementation tracking in `.planning/phases/phase-source-stabilization/S6-school-level-ethnicity-breakdown-support.md`.

### Detailed design

- `.planning/phases/phase-source-stabilization/README.md`
- `.planning/phases/phase-source-stabilization/S1-source-contract-and-catalog-freeze.md`
- `.planning/phases/phase-source-stabilization/S2-release-file-discovery-and-bronze-ingest.md`
- `.planning/phases/phase-source-stabilization/S3-multi-source-normalization-and-gold-upsert.md`
- `.planning/phases/phase-source-stabilization/S4-completeness-contract-and-parent-facing-copy.md`
- `.planning/phases/phase-source-stabilization/S5-quality-gates-and-signoff.md`
- `.planning/phases/phase-source-stabilization/S6-school-level-ethnicity-breakdown-support.md`

### Deliverables

1. **S1: Source contract and catalog freeze** - lock approved publications/releases/files and required columns with explicit fallback behavior.
2. **S2: Release file discovery + Bronze ingest** - implement deterministic discovery of school-level underlying data assets and immutable Bronze manifests.
3. **S3: Multi-source normalization + Gold upsert** - combine SPC + SEN school-level files into `school_demographics_yearly` with consistent `(urn, academic_year)` semantics.
4. **S4: Completeness contract + parent copy** - expose precise reason codes and messaging for sparse/partial history states in API and web profile/trends UX.
5. **S5: Quality gates + sign-off** - enforce coverage/depth gates and document evidence in one repository state.
6. **S6: School-level ethnicity breakdown support** - map existing SPC school-level ethnicity columns into serving contracts and remove the ethnicity unsupported gap where data exists.

### Exit criteria

- Open-school trend history has `>=2` years for primary and secondary at agreed target thresholds.
- `school_demographics_yearly` reflects multi-year coverage from approved source families (not single-year fallback behavior).
- Trend suppression and UI copy align with actual source availability and do not use pipeline-internal language.
- School profile APIs expose ethnicity breakdown from approved SPC school-level files where present.
- All implemented `Phase S` gates pass with evidence.

### Dependencies

- Phase 2 and Phase H outputs.
- Blocks progression to Phase 3+ until signed off.

---

## Phase UX - Visual quality + interaction uplift (web cross-cutting)

**Goal:** Elevate Civitas web experience from functional baseline to polished, map-first editorial quality across search and profile journeys, with explicit dark/light mode control.

### Detailed design

- `.planning/phases/phase-ux/README.md`
- `.planning/phases/phase-ux/UX-1-maplibre-migration-uk-bounds-landing-state.md`
- `.planning/phases/phase-ux/UX-2-map-interaction-depth.md`
- `.planning/phases/phase-ux/UX-3-overlay-panel-refinement.md`
- `.planning/phases/phase-ux/UX-4-typography-spacing-visual-hierarchy.md`
- `.planning/phases/phase-ux/UX-5-transitions-motion.md`
- `.planning/phases/phase-ux/UX-6-navigation-site-chrome-refinement.md`
- `.planning/phases/phase-ux/UX-7-loading-empty-state-polish.md`
- `.planning/phases/phase-ux/UX-8-theme-mode-toggle.md`

### Deliverables

1. **UX-1: MapLibre migration + UK bounds** - move from raster Leaflet stack to UK-scoped vector rendering with custom style control.
2. **UX-2: Map interaction depth** - fly-to, radius overlays, clustering, and list-marker interaction linking.
3. **UX-3: Overlay panel refinement** - desktop collapse, mobile bottom-sheet, hidden-scrollbar behavior, and scroll affordances.
4. **UX-4: Typography and hierarchy** - editorial spacing and data-first visual hierarchy on search/profile routes.
5. **UX-5: Transitions and motion** - route and interaction continuity with reduced-motion parity.
6. **UX-6: Navigation chrome refinement** - map-first header/footer behavior and contextual breadcrumb/search state.
7. **UX-7: Loading/empty/error polish** - map-aware contextual states preserving user orientation.
8. **UX-8: Theme mode toggle** - user-selectable dark/light mode with persisted preference and map style parity.

### Exit criteria

- Search route renders UK-bounded vector map and map/list interactions feel connected.
- Overlay, typography, motion, and chrome refinements produce a polished map-first UX.
- Loading, empty, and error states preserve map context and support recovery.
- Users can switch between dark and light mode, and both themes remain accessible and visually coherent with the map stack.
- Existing quality rails remain green (`make lint`, `make test`, web budgets, Lighthouse, accessibility).

### Dependencies

- Phase 0 and Phase 1 web baseline.
- Can run in parallel with Phase 2 backend work; coordinate with Phase 2 web section (`2F`) to keep profile styling aligned.
- Must align with `Phase S` API completeness semantics before final UX sign-off on profile trend states.

---

## Phase M - Metrics parity and coverage closure

**Goal:** Close remaining metric gaps from `.planning/metrics.md` by extending existing ingested sources and integrating new sources where required.

### Detailed design

- `.planning/phases/phase-metrics-parity/README.md`
- `.planning/phases/phase-metrics-parity/M1-ofsted-depth-and-derived-indicators.md`
- `.planning/phases/phase-metrics-parity/M2-demographics-support-depth.md`
- `.planning/phases/phase-metrics-parity/M3-attendance-behaviour-pipelines.md`
- `.planning/phases/phase-metrics-parity/M4-workforce-leadership-pipelines.md`
- `.planning/phases/phase-metrics-parity/M5-area-context-and-house-prices.md`
- `.planning/phases/phase-metrics-parity/M6-benchmarks-and-trend-dashboard.md`

### Deliverables

1. **M1: Ofsted depth + derived indicators** - add sub-judgements and time-since-last-inspection fields.
2. **M2: Demographics/support depth** - close FSM6, gender, mobility, SEN primary need, and languages coverage where publishable.
3. **M3: Attendance/behaviour pipelines** - ingest attendance, persistent absence, suspensions, and exclusions with trend history.
4. **M4: Workforce/leadership pipelines** - ingest staffing and leadership metrics for profile + trend views.
5. **M5: Area context expansion** - add IMD domains, crime rates, and house-price context/trends.
6. **M6: Benchmark and dashboard layer** - deliver national/local benchmark context and a cross-metric trend dashboard.

### Exit criteria

- Every metric in `.planning/metrics.md` is either implemented end-to-end or explicitly marked unavailable with source-backed reason.
- New source integrations include direct endpoint schema validation evidence before implementation.
- Profile/trends API and web UI expose consistent completeness metadata for all newly added domains.

### Dependencies

- Phase S completion (source strategy and completeness semantics stable).
- Phase H quality and observability controls in place for additional source onboarding.

---

## Phase 3 - Compare experience

**Goal:** Deliver side-by-side school comparison with robust metric alignment and missing-data handling.

### Deliverables

1. **Compare API** - `GET /api/v1/schools/compare?urns=...` returning aligned metrics for up to 4 schools.
2. **Frontend: compare view** - side-by-side table/card layout with consistent metric rows.
3. **Frontend: compare selection UX** - add/remove schools from comparison set across search and profile.
4. **Compare data contract hardening** - deterministic handling for missing/suppressed values and differing year coverage.

### Exit criteria

- User can select 2-4 schools and compare them side-by-side.
- Comparison output remains readable and stable when schools have different data coverage.

### Dependencies

- Phase 2.
- Phase S.
- Phase M.

---

## Phase 4 - Paywall + premium access

**Goal:** Deliver freemium model with authentication and backend-enforced entitlements.

### Deliverables

1. **Authentication** - email-based auth (sign-up, login, session management).
2. **Entitlements model** - domain model for premium access (postcode unlock, duration, purchase record).
3. **Backend access enforcement** - dependency/middleware checks before returning premium data.
4. **Payment integration** - Stripe (or equivalent) for postcode unlock purchase.
5. **Free vs paid data boundary** - define which fields/endpoints are gated; API returns allowed subset.
6. **Frontend: auth flow** - sign-up, login, session UI.
7. **Frontend: paywall UX** - preview gated data with upgrade prompt; unlock after purchase.
8. **Authenticated premium AI exposure** - expose `groks_take` summaries generated by `.planning/phases/phase-ai/AI-3-groks-take-premium-analysis.md` only after backend identity and entitlement checks are live.

### Exit criteria

- Free users see headline data only.
- Paid users unlock full postcode dataset for 30 days.
- All access control is backend-enforced.
- Premium AI analysis is never returned from public endpoints without authenticated backend entitlement checks.

### Dependencies

- Phase 3.

---

## Phase 5 (post-MVP) - Extend + optimize

**Goal:** Add post-MVP expansion, operational hardening, SEO support, and growth features beyond the Phase M metrics-catalog scope.

### Potential deliverables

- Additional public datasets beyond `.planning/metrics.md` (for example deprivation/crime/health extensions outside the school-profile baseline).
- Advanced house-price context beyond Phase M baseline (for example affordability ratios or finer-grain geographies).
- PDF report export (postcode and/or school reports) if business value justifies.
- SEO-ready static/indexable location pages.
- Operational admin dashboard (pipeline health, row counts, last refresh).
- Lifetime unlock option.
- Performance optimization (query caching, CDN, materialized views).
- Additional search dimensions (school type filter, Ofsted rating filter).

### Dependencies

- MVP complete (Phases 0-4).

---

## Phase summary

| Phase | Name | Key outcome | Estimated complexity |
|-------|------|-------------|---------------------|
| 0 | Data foundation + GIAS | Search by postcode with production-grade web foundations and schools on map | Foundation / largest setup effort |
| 1 | Profiles + DfE + Ofsted headline | School profile with trends and latest Ofsted | Medium-large |
| 2 | Ofsted timeline + area context | Rich profiles with full inspections and area data | Medium-large (multiple pipelines) |
| H | Hardening | Deterministic pipeline quality, completeness transparency, and operational resilience | Large (cross-cutting) |
| S | Source strategy stabilization | Reliable multi-year trend coverage and source-contract clarity | Large (cross-cutting + source integration) |
| M | Metrics parity and coverage closure | Full metrics catalog delivery with source-backed completeness handling | Large (cross-cutting + multi-source) |
| UX | Visual quality + interaction uplift | Map-first polished UX across search and profile interactions | Medium-large (frontend heavy) |
| 3 | Compare experience | Side-by-side comparison with aligned/missing data handling | Medium-large |
| 4 | Paywall + premium | Auth, entitlements, payment | Medium-large |
| 5 | Post-MVP extensions | Expansion and optimization beyond Phase M coverage | Ongoing |

---

## Open questions

1. **Auth provider** - managed provider vs custom email auth?
2. **Payment provider** - Stripe assumed but not yet confirmed.
3. **Typed metrics schema boundaries** - split by domain (`demographics`, `attendance`, `workforce`) or one wider yearly fact table?
4. **Phase S target thresholds** - should open-school `>=2` year and `>=3` year coverage thresholds be adjusted by phase category before final sign-off?
