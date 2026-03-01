# Phase 0D2 Design - Web Search And Map Experience

## Document Control

- Status: Implemented
- Last updated: 2026-03-01
- Depends on:
  - `.planning/phases/phase-0/0D1-web-foundations.md`
  - `.planning/phases/phase-0/0C-postcode-search-api.md`
  - `.planning/project-brief.md`
  - `docs/architecture/principles.md`
  - `docs/architecture/frontend-conventions.md`

## Objective

Ship the first user-facing Civitas journey: postcode search showing nearby schools in both list and map views using the Phase 0 API contract and the shared foundations established in 0D1.

## Implementation Progress (2026-03-01)

- Completed: replaced demo preview-state scaffold with live schools-search feature composition under `apps/web/src/features/schools-search`.
- Completed: added typed API client support for `GET /api/v1/schools` with OpenAPI-derived contracts (`src/api/types.ts` aliases + `src/api/client.ts` `searchSchools`).
- Completed: implemented local feature orchestration hook for postcode/radius form state, submit lifecycle, and deterministic idle/loading/success/empty/error rendering.
- Completed: implemented map/list composition using shared 0D1 primitives:
  - `SearchForm` -> `TextInput`, `Select`, `Button`, `Field`
  - `SchoolsList` -> `ResultCard`, `LoadingSkeleton`, `EmptyState`, `ErrorState`
  - `SchoolsMap` -> `MapPanel` with lazy-loaded Leaflet chunk retained
  - `SchoolsSearchFeature` -> `AppShell`, `PageContainer`, `SplitPaneLayout`
- Completed: replaced app tests with 0D2 behavior coverage (validation, submit call shape, loading, success list+map markers, empty, error/retry, accessibility smoke).
- Completed: replaced Playwright demo spec with schools-search smoke coverage using route-level API mocking (`apps/web/e2e/schools-search.spec.ts`) and removed the old `tasks.spec.ts`.
- Completed: quality gates passing for 0D2 integration:
  - `cd apps/web && npm run lint`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run test`
  - `cd apps/web && npm run build`
  - `cd apps/web && npm run budget:check`
  - `make lint`
  - `make test`

## Scope

### In scope

- Postcode search form and radius control.
- Results list showing school headline fields and distance.
- Interactive map with markers for results.
- Loading, empty, and error states for search flow.
- Contract-aligned API client/types sourced from backend OpenAPI.
- Composition from shared tokenized primitives and layout patterns defined in 0D1.

### Out of scope

- School profile pages (Phase 1).
- Compare/export/premium behaviors (Phase 3+).
- Advanced filtering/sorting beyond distance default.
- New design-token or primitive-system decisions (owned by 0D1).

## Decisions

1. **Map stack for Phase 0**: Leaflet (`react-leaflet`) for speed and maturity.
2. **State strategy**: local feature state via React hooks; no global state library in Phase 0.
3. **Contract strategy**: OpenAPI-exported schema remains source of truth for web types.
4. **Initial route strategy**: keep single-page flow in `App` for Phase 0; route split can follow in Phase 1.
5. **Composition rule**: search/map UI must use shared components/tokens from 0D1; no one-off control styling in feature code.
6. **Map performance rule**: map bundle loads lazily so initial shell render remains fast on mobile.

## UX Contract

### Inputs

- Postcode text input (required).
- Radius selector (default 5 miles; values aligned with API limits).
- Submit action.

### Results list item fields

- School name
- School type
- Phase
- Postcode
- Distance in miles (rounded display)

### Map behavior

- Center map on resolved postcode coordinates from API response.
- Render one marker per returned school.
- Opening marker popup shows school name + distance.
- List and map consume same result data source to avoid divergence.

### States

- Initial: guidance text before first search.
- Loading: active fetch state.
- Empty: valid request with zero schools.
- Error: API/network failure with clear retry path.

## Frontend Design

### Feature structure

Add a dedicated feature folder:

- `apps/web/src/features/schools-search/`
  - `components/` (feature composition from shared primitives)
  - `hooks/` (search state orchestration)
  - `types.ts` (feature-local view types if needed)

### API client integration

- Extend `apps/web/src/api/client.ts` with `searchSchools`.
- Generate/maintain request/response types from OpenAPI and use them in client + feature.
- Avoid ad-hoc contract definitions in feature code.

### App composition

- Replace task scaffold usage in `apps/web/src/App.tsx` with schools search feature root.
- Keep layout and control styling aligned with 0D1 token and primitive layers.
- Add map/list responsive behavior through shared layout primitives, not ad-hoc page-level overrides.

### 0D2 to 0D1 composition map

| 0D2 component | Required 0D1 composition |
|---|---|
| `SearchForm` | `TextInput`, `Select`, `Button`, `Field` |
| `SchoolsList` | `ResultCard`, `LoadingSkeleton`, `EmptyState`, `ErrorState` |
| `SchoolsMap` | `MapPanel` |
| `SchoolsSearchFeature` | `AppShell`, `PageContainer`, `SplitPaneLayout` |

## File-Oriented Implementation Plan

1. `apps/web/package.json`
   - add map dependencies (`leaflet`, `react-leaflet`, and types as needed) if not already added by 0D1.
2. `apps/web/src/api/openapi.json`
   - refresh from backend after 0C contract is finalized.
3. `apps/web/src/api/generated-types.ts` (or equivalent generated target)
   - regenerate from updated OpenAPI.
4. `apps/web/src/api/client.ts`
   - add `searchSchools` function.
5. `apps/web/src/features/schools-search/components/SearchForm.tsx`
   - postcode + radius inputs and submit behavior composed with shared form primitives.
6. `apps/web/src/features/schools-search/components/SchoolsList.tsx`
   - results list rendering and empty/error handling composed with shared state/card primitives.
7. `apps/web/src/features/schools-search/components/SchoolsMap.tsx`
   - marker rendering and center behavior with lazy-loaded map boundary via shared `MapPanel`.
8. `apps/web/src/features/schools-search/SchoolsSearchFeature.tsx`
   - feature orchestration container.
9. `apps/web/src/App.tsx`
   - mount schools search feature.
10. `apps/web/src/App.test.tsx`
    - replace task assertions with schools-search behavior tests.
11. `apps/web/e2e/schools-search.spec.ts`
    - schools search smoke test with mocked API response path.
12. `apps/web/scripts/check-budgets.mjs` (or equivalent)
    - ensure 0D1 performance budgets remain green during 0D2 integration.

## Testing And Quality Gates

### Web tests to add/update

- Unit/component tests:
  - form validation and submit calls.
  - successful result rendering.
  - empty/error states.
  - keyboard/focus navigation for form + result list controls.
  - accessibility smoke on feature root using shared 0D1 testing utilities.
- E2E smoke:
  - app loads and search UI is visible.
  - mocked or test backend path returns list and map markers.
  - responsive behavior validated at minimum mobile and desktop viewports.

### Required gates

- `make lint`
- `make test`
- `cd apps/web && npm run build`
- `cd apps/web && npm run budget:check`

## Acceptance Criteria

1. User can search by postcode and see schools in list + map from live API data.
2. Distance values displayed in list align with API payload ordering.
3. Empty and error states are explicit and recoverable.
4. Web uses backend-derived contract types, not manually duplicated schemas.
5. Web search/map feature uses shared 0D1 primitives/tokens and passes agreed accessibility/responsiveness/performance rails.
6. 0D2 feature code does not import raw `@radix-ui/*` primitives or bypass the shared component/token system.

## Risks And Mitigations

- **Risk**: map rendering complexity delays Phase 0 closeout.
  - **Mitigation**: keep Phase 0 map interactions minimal (markers + popups only).
- **Risk**: contract drift between API and web.
  - **Mitigation**: enforce OpenAPI export + type generation as part of implementation checklist.
