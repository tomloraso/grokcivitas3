# Phase 1G Design - Web School Profile Page

## Document Control

- Status: Completed
- Last updated: 2026-03-02
- Depends on:
  - `.planning/phases/phase-1/1D-school-profile-api.md`
  - `.planning/phases/phase-1/1E-school-trends-api.md`
  - `.planning/phases/phase-1/1F-web-routing-navigation-foundation.md`
  - `.planning/phases/phase-1/1F1-web-component-expansion-data-viz-baseline.md`
  - `.planning/phases/phase-0/0D1-web-foundations.md`
  - `docs/architecture/frontend-conventions.md`

## Tracking Update (2026-03-02)

- Implementation complete for `/schools/:urn` profile composition.
- Route wiring updated in `apps/web/src/app/routes.tsx` to mount `SchoolProfileFeature`.
- Feature delivered under `apps/web/src/features/school-profile/` with:
  - typed data fetching (`getSchoolProfile`, `getSchoolTrends`),
  - contract-to-view-model mapper,
  - profile header, Ofsted card, demographics summary, trends panel, and coverage notice.
- Sparse/empty data handling implemented:
  - explicit partial-history messaging,
  - explicit no-trend-data state,
  - explicit unsupported-metric coverage notice.
- Degradation behavior implemented:
  - trends failures do not block profile rendering.
- Test coverage added/updated:
  - mapper tests,
  - feature state tests (loading/success/error/not-found),
  - single-year and empty-series trend tests,
  - coverage notice and accessibility smoke tests,
  - E2E verification from search -> profile including Ofsted and demographics assertions.
- Quality gates executed and green:
  - `cd apps/web && npm run lint`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run test`
  - `cd apps/web && npm run build`
  - `cd apps/web && npm run budget:check`
  - `cd apps/web && npm run test:e2e`
  - `make lint`
  - `make test`

## Objective

Deliver a profile route that presents school identity, latest demographics, latest Ofsted headline, and trend visuals using typed backend contracts and shared Phase 0 primitives.

## Scope

### In scope

- Profile page route composition for `/schools/:urn`.
- Headline school metadata section.
- Demographics summary cards.
- Ofsted headline badge and date metadata.
- Trend visual block for supported metrics.
- Explicit sparse-history and missing-metric states.

### Out of scope

- Ofsted full timeline UI (Phase 2).
- Compare flows (Phase 3).
- Premium gating UI (Phase 4).

## Decisions

1. Reuse Phase 0 shared layout/UI primitives and Phase 1F1 expanded components (StatCard, TrendIndicator, RatingBadge, Sparkline, Badge, Tabs); no profile-specific ad-hoc design system.
2. Treat unsupported metrics as explicit UI states using `MetricUnavailable`, not hidden omissions.
3. Trend cards must render correctly with one data point (no fake sparkline interpolation).
4. Profile feature owns mapping from API wire contract to UI view model at feature boundary.
5. Composition rule: 1G must not introduce new shared primitives. If a missing primitive is discovered, it is added to 1F1 first.

## UI Composition

Profile route composition:

1. Header panel:
   - school name, phase, type, postcode.
2. Ofsted panel:
   - headline rating badge,
   - inspection/publication dates,
   - graded vs ungraded indicator.
3. Demographics panel:
   - disadvantaged, SEN, EHCP, EAL, first-language breakdown.
4. Trends panel:
   - compact sparklines or fallback stat rows per metric.
5. Coverage note panel:
   - indicates unavailable metrics (for example FSM direct field, ethnicity, top languages).

## Feature Structure

Add profile feature folder:

- `apps/web/src/features/school-profile/`
  - `SchoolProfileFeature.tsx`
  - `hooks/`
  - `components/`
  - `mappers/`
  - `types.ts`

## API Client Integration

- Extend `apps/web/src/api/client.ts` with:
  - `getSchoolProfile(urn)`
  - `getSchoolTrends(urn)`
- Use OpenAPI-generated types from `src/api/types.ts`.
- No manual duplication of API payload types.

## File-Oriented Implementation Plan

1. `apps/web/src/api/client.ts`
   - add typed profile and trends fetchers.
2. `apps/web/src/features/school-profile/hooks/useSchoolProfile.ts` (new)
   - orchestrate profile + trends request lifecycle.
3. `apps/web/src/features/school-profile/mappers/profileMapper.ts` (new)
   - map API contract to view model.
4. `apps/web/src/features/school-profile/components/ProfileHeader.tsx` (new)
5. `apps/web/src/features/school-profile/components/OfstedHeadlineCard.tsx` (new)
6. `apps/web/src/features/school-profile/components/DemographicsSummary.tsx` (new)
7. `apps/web/src/features/school-profile/components/TrendPanel.tsx` (new)
8. `apps/web/src/features/school-profile/components/CoverageNotice.tsx` (new)
9. `apps/web/src/features/school-profile/SchoolProfileFeature.tsx` (new)
10. `apps/web/src/app/routes.tsx`
    - map `/schools/:urn` to `SchoolProfileFeature`.

## Testing And Quality Gates

### Required tests

- profile route renders loading, success, error, and not-found states.
- Ofsted headline card renders graded and ungraded scenarios.
- trend panel handles:
  - one-year series,
  - multi-year series,
  - empty series.
- coverage notice renders when unsupported metrics are null with `coverage=false`.

### E2E updates

- from search route, open profile and verify:
  - school heading,
  - Ofsted panel,
  - demographics panel.

### Required gates

- `cd apps/web && npm run lint`
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run test`
- `cd apps/web && npm run build`
- `cd apps/web && npm run budget:check`
- `make lint`
- `make test`

## Acceptance Criteria

1. User can open `/schools/:urn` and view school profile with demographics and Ofsted headline.
2. Trends render truthfully based on available years (including sparse history).
3. Unsupported metrics are explicitly communicated.
4. UI uses shared primitives and remains responsive and accessible.

## Risks And Mitigations

- Risk: sparse source history makes trends appear broken.
  - Mitigation: explicit sparse-history UI treatment and messaging.
- Risk: profile page grows ad-hoc visual patterns outside shared system.
  - Mitigation: enforce composition through 0D1 + 1F + 1F1 shared primitives. No new shared component definitions in feature code.
