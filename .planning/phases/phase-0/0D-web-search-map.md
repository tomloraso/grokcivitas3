# Phase 0D Design - Web Search And Map Experience

## Document Control

- Status: Draft
- Last updated: 2026-02-27
- Depends on:
  - `.planning/phases/phase-0/0C-postcode-search-api.md`
  - `.planning/project-brief.md`
  - `docs/architecture/principles.md`

## Objective

Ship the first user-facing Civitas journey: postcode search showing nearby schools in both list and map views using the Phase 0 API contract.

## Scope

### In scope

- Postcode search form and radius control.
- Results list showing school headline fields and distance.
- Interactive map with markers for results.
- Loading, empty, and error states for search flow.
- Contract-aligned API client/types sourced from backend OpenAPI.

### Out of scope

- School profile pages (Phase 1).
- Compare/export/premium behaviors (Phase 3+).
- Advanced filtering/sorting beyond distance default.

## Decisions

1. **Map stack for Phase 0**: Leaflet (`react-leaflet`) for speed and maturity.
2. **State strategy**: local feature state via React hooks; no global state library in Phase 0.
3. **Contract strategy**: OpenAPI-exported schema remains source of truth for web types.
4. **Initial route strategy**: keep single-page flow in `App` for Phase 0; route split can follow in Phase 1.

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
  - `components/` (form, list, map)
  - `hooks/` (search state orchestration)
  - `types.ts` (feature-local view types if needed)

### API client integration

- Extend `apps/web/src/api/client.ts` with `searchSchools`.
- Generate/maintain request/response types from OpenAPI and use them in client + feature.
- Avoid ad-hoc contract definitions in feature code.

### App composition

- Replace task scaffold usage in `apps/web/src/App.tsx` with schools search feature root.
- Keep styling in `apps/web/src/styles.css` unless component-scoped CSS modules are introduced.

## File-Oriented Implementation Plan

1. `apps/web/package.json`
   - add map dependencies (`leaflet`, `react-leaflet`, and types as needed).
2. `apps/web/src/api/openapi.json`
   - refresh from backend after 0C contract is finalized.
3. `apps/web/src/api/generated-types.ts` (or equivalent generated target)
   - regenerate from updated OpenAPI.
4. `apps/web/src/api/client.ts`
   - add `searchSchools` function.
5. `apps/web/src/features/schools-search/components/SearchForm.tsx`
   - postcode + radius inputs and submit behavior.
6. `apps/web/src/features/schools-search/components/SchoolsList.tsx`
   - results list rendering and empty/error handling.
7. `apps/web/src/features/schools-search/components/SchoolsMap.tsx`
   - marker rendering and center behavior.
8. `apps/web/src/features/schools-search/SchoolsSearchFeature.tsx`
   - feature orchestration container.
9. `apps/web/src/App.tsx`
   - mount schools search feature.
10. `apps/web/src/styles.css`
    - update layout styles for list + map split and responsive behavior.
11. `apps/web/src/App.test.tsx`
    - replace task assertions with schools-search behavior tests.
12. `apps/web/e2e/tasks.spec.ts`
    - replace with schools search smoke test (rename file).

## Testing And Quality Gates

### Web tests to add/update

- Unit/component tests:
  - form validation and submit calls.
  - successful result rendering.
  - empty/error states.
- E2E smoke:
  - app loads and search UI is visible.
  - mocked or test backend path returns list and map markers.

### Required gates

- `make lint`
- `make test`

## Acceptance Criteria

1. User can search by postcode and see schools in list + map from live API data.
2. Distance values displayed in list align with API payload ordering.
3. Empty and error states are explicit and recoverable.
4. Web uses backend-derived contract types, not manually duplicated schemas.

## Risks And Mitigations

- **Risk**: map rendering complexity delays Phase 0 closeout.
  - **Mitigation**: keep Phase 0 map interactions minimal (markers + popups only).
- **Risk**: contract drift between API and web.
  - **Mitigation**: enforce OpenAPI export + type generation as part of implementation checklist.
