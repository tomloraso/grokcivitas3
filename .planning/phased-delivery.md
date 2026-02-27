# Phased Delivery Plan

## Guiding principles

- Each phase delivers a usable increment; no phase is purely infrastructure with no visible output.
- Data pipeline and API are built together, source by source.
- Frontend features start only when the API endpoint they consume is tested and stable.
- Each phase ends with working tests, passing lint, and a demoable artifact.
- Deployment assumptions are tracked in `.planning/deployment-strategy.md` and updated when phase design changes runtime needs.

---

## Phase 0 - Data foundation + GIAS baseline

**Goal:** Prove the full Bronze -> Staging -> Gold pipeline with one source, expose schools via API, display on frontend.

### Detailed design

- `.planning/phases/phase-0/README.md`
- `.planning/phases/phase-0/0A-data-platform-baseline.md`
- `.planning/phases/phase-0/0B-gias-pipeline.md`
- `.planning/phases/phase-0/0C-postcode-search-api.md`
- `.planning/phases/phase-0/0D-web-search-map.md`

### Deliverables

1. **0A: Data platform baseline** - PostGIS runtime, migration framework, pipeline base contracts, CLI orchestration.
2. **0B: GIAS pipeline** - Bronze -> Staging -> Gold load into `schools` with PostGIS geometry and idempotent upsert semantics.
3. **0C: Postcode search API** - Postcodes.io resolution + cache, `GET /api/v1/schools?postcode=...&radius=...`, spatial radius query sorted by distance.
4. **0D: Web search + map** - postcode form, list results, and Leaflet markers backed by Phase 0 API contract.

### Exit criteria

- User can enter a postcode and see nearby schools on a list and map.
- Pipeline is re-runnable and idempotent.
- OpenAPI contract is updated and consumed by web client/types.
- Import boundary tests pass, with lint and tests green.

### Dependencies

- None.

---

## Phase 1 - School profiles + DfE metrics + Ofsted headline

**Goal:** Add depth to school records with DfE pupil characteristics plus the latest Ofsted headline rating on profile.

### Deliverables

1. **DfE characteristics pipeline** - Bronze -> Staging -> Gold for pupil demographics (FSM, SEN, ethnicity, languages).
2. **Ofsted latest pipeline** - Bronze -> Staging -> Gold latest inspection outcome per school (headline rating + date).
3. **Gold `school_demographics_yearly` table** - typed yearly columns for core demographic metrics (not metric-key EAV).
4. **Gold `school_ofsted_latest` table** - one latest Ofsted snapshot per school.
5. **School profile API** - `GET /api/v1/schools/{urn}` returning core info + latest demographics + latest Ofsted headline.
6. **Trends API** - `GET /api/v1/schools/{urn}/trends` returning 3-5 year history with deltas from typed yearly metrics.
7. **Frontend: school profile page** - headline stats (including Ofsted badge) plus trend sparklines.
8. **Frontend: navigation** - results list -> profile page linking.

### Exit criteria

- User can open a school profile and view demographic indicators, trend direction, and latest Ofsted rating.
- Historical data covers 3+ years where available.

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
| 0 | Data foundation + GIAS | Search by postcode, schools on map | Foundation / largest setup effort |
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
