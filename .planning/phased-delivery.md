# Phased Delivery Plan

## Guiding principles

- Each phase delivers a usable increment; no phase is purely infrastructure with no visible output.
- Data pipeline and API are built together, source by source.
- Frontend features start only when the API endpoint they consume is tested and stable.
- Frontend flagship slices must pass a foundations gate (tokens, primitives, and quality rails) before feature-specific polish.
- Each phase ends with working tests, passing lint, and a demoable artifact.
- Deployment assumptions are tracked in `.planning/deployment-strategy.md` and updated when phase design changes runtime needs.

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

### Deliverables

1. **Ofsted timeline pipeline extension** - Bronze -> Staging -> Gold for full inspection record history.
2. **Gold `ofsted_inspections` table** - full inspection timeline per school.
3. **ONS IMD pipeline** - Bronze -> Staging -> Gold for deprivation by LSOA.
4. **Gold `area_deprivation` table** - IMD decile and child poverty by LSOA.
5. **Police UK pipeline** - Bronze -> Staging -> Gold for aggregated crime context near schools.
6. **Gold `area_crime_context` table** - monthly crime aggregates per school location.
7. **School profile API extensions** - include Ofsted timeline, IMD decile, and crime summary.
8. **Frontend: profile enhancements** - Ofsted badge + timeline, area context section.

### Exit criteria

- School profiles show latest Ofsted rating and inspection history timeline.
- Area context is visible (deprivation decile and crime summary).
- New pipelines are idempotent and tested.

### Dependencies

- Phase 1.

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

### Exit criteria

- Free users see headline data only.
- Paid users unlock full postcode dataset for 30 days.
- All access control is backend-enforced.

### Dependencies

- Phase 3.

---

## Phase 5 (post-MVP) - Extend + optimize

**Goal:** Add datasets, operational hardening, SEO support, and growth features.

### Potential deliverables

- Land Registry house price pipeline and profile integration.
- School workforce data (teacher ratios, sickness days, supply percentage).
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
| 3 | Compare experience | Side-by-side comparison with aligned/missing data handling | Medium-large |
| 4 | Paywall + premium | Auth, entitlements, payment | Medium-large |
| 5 | Post-MVP extensions | Additional data and operational tooling | Ongoing |

---

## Open questions

1. **Auth provider** - managed provider vs custom email auth?
2. **Payment provider** - Stripe assumed but not yet confirmed.
3. **Typed metrics schema boundaries** - split by domain (`demographics`, `attendance`, `workforce`) or one wider yearly fact table?
4. **DfE school-level demographics coverage** - which validated callable source will provide direct FSM and ethnicity at school level if not present in current endpoint set?
