# Phased Delivery Plan

## Guiding principles

- Each phase delivers a usable increment; no phase is purely infrastructure with no visible output.
- Data pipeline and API are built together, source by source.
- Frontend features start only when the API endpoint they consume is tested and stable.
- Each phase ends with working tests, passing lint, and a demoable artifact.

---

## Phase 0 - Data foundation + GIAS baseline

**Goal:** Prove the full Bronze -> Staging -> Gold pipeline with one source, expose schools via API, display on frontend.

### Deliverables

1. **PostgreSQL + PostGIS setup** - Docker Compose service, schema migrations (Alembic or raw SQL).
2. **Pipeline framework** - base pipeline interface, CLI integration (`civitas pipeline run --source gias`).
3. **GIAS pipeline** - download, clean, load schools into Gold `schools` table with PostGIS geometry.
4. **Postcode resolution** - Postcodes.io integration for user search (postcode -> lat/lng).
5. **Schools search API** - `GET /api/schools?postcode=...&radius=5` returning schools within radius, sorted by distance.
6. **Frontend: search + results list** - postcode input, results list with school name/type/distance.
7. **Frontend: map view** - markers for results on an interactive map.

### Exit criteria

- User can enter a postcode and see nearby schools on a list and map.
- Pipeline is re-runnable and idempotent.
- Import boundary tests pass, with lint and tests green.

### Dependencies

- None.

---

## Phase 1 - School profiles + DfE metrics

**Goal:** Add depth to school records with DfE pupil characteristics. Deliver a profile page with headline stats and trends.

### Deliverables

1. **DfE characteristics pipeline** - Bronze -> Staging -> Gold for pupil demographics (FSM, SEN, ethnicity, languages).
2. **Gold `school_metrics` table** - yearly snapshots per school, metric-key model.
3. **School profile API** - `GET /api/schools/{urn}` returning core info + latest metrics.
4. **Trends API** - `GET /api/schools/{urn}/trends` returning 3-5 year metric history with deltas.
5. **Frontend: school profile page** - headline stats (big numbers, flags), trend sparklines.
6. **Frontend: navigation** - results list -> profile page linking.

### Exit criteria

- User can open a school profile and view demographic indicators plus trend direction.
- Historical data covers 3+ years where available.

### Dependencies

- Phase 0.

---

## Phase 2 - Ofsted + area context

**Goal:** Add inspection history and area-level context (crime, deprivation) to profile depth.

### Deliverables

1. **Ofsted pipeline** - Bronze -> Staging -> Gold for inspection records.
2. **Gold `ofsted_inspections` table** - full inspection timeline per school.
3. **ONS IMD pipeline** - Bronze -> Staging -> Gold for deprivation by LSOA.
4. **Gold `area_deprivation` table** - IMD decile and child poverty by LSOA.
5. **Police UK pipeline** - Bronze -> Staging -> Gold for aggregated crime context near schools.
6. **Gold `area_crime_context` table** - monthly crime aggregates per school location.
7. **School profile API extensions** - include Ofsted timeline, IMD decile, and crime summary.
8. **Frontend: profile enhancements** - Ofsted badge + timeline, area context section.

### Exit criteria

- School profiles show Ofsted rating with inspection history.
- Area context is visible (deprivation decile and crime summary).
- New pipelines are idempotent and tested.

### Dependencies

- Phase 1.

---

## Phase 3 - Compare + export

**Goal:** Deliver side-by-side school comparison and PDF report export.

### Deliverables

1. **Compare API** - `GET /api/schools/compare?urns=...` returning aligned metrics for up to 4 schools.
2. **Frontend: compare view** - side-by-side table/card layout with consistent metric rows.
3. **Frontend: compare selection UX** - add/remove schools from comparison set across search and profile.
4. **PDF export API** - `GET /api/reports/postcode/{postcode}` generating a branded PDF report.
5. **Frontend: export trigger** - download button on search results and/or school profile.

### Exit criteria

- User can select 2-4 schools and compare them side-by-side.
- User can download a postcode PDF report.

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
| 1 | Profiles + DfE metrics | School profile with trends | Medium |
| 2 | Ofsted + area context | Rich profiles with inspections and area data | Medium-large (multiple pipelines) |
| 3 | Compare + export | Side-by-side comparison and PDF reports | Medium |
| 4 | Paywall + premium | Auth, entitlements, payment | Medium-large |
| 5 | Post-MVP extensions | Additional data and operational tooling | Ongoing |

---

## Open questions

1. **Phase 0 map stack** - Leaflet vs MapLibre for initial map implementation?
2. **PDF generation** - server-side rendering (recommended) vs client-side?
3. **Auth provider** - managed provider vs custom email auth?
4. **Payment provider** - Stripe assumed but not yet confirmed.
5. **Phase ordering** - move Ofsted elements earlier if user value justifies it?
