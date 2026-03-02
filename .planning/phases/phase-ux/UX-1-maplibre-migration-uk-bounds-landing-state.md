# Phase UX-1 Design - MapLibre Migration, UK Bounds, And Landing State

## Document Control

- Status: Draft
- Last updated: 2026-03-02
- Depends on:
  - `.planning/phases/phase-0/0D1-web-foundations.md`
  - `.planning/phases/phase-0/0D-web-search-map.md`
  - `.planning/phases/phase-ux/README.md`
  - `docs/architecture/frontend-conventions.md`

## Objective

Replace the raster Leaflet map stack with a UK-bounded MapLibre vector map that enables full cartographic style control and a polished map-first landing state.

## Scope

### In scope

- Replace `leaflet` + `react-leaflet` with `maplibre-gl` + `react-map-gl/maplibre`.
- Preserve the existing map boundary abstraction (`MapPanel` and `MapPanelChromeless`) so feature call-sites stay stable.
- Introduce a custom dark vector style contract (`shared/maps/map-style.ts`).
- Apply UK panning/zoom constraints and a UK-first default view.
- Keep marker popup and keyboard-accessibility behavior at parity with the current baseline.
- Keep map rendering lazy-loaded and inside existing map-chunk performance budget.

### Out of scope

- Bi-directional hover linking and clustering (UX-2).
- Overlay panel redesign and mobile bottom-sheet behavior (UX-3).
- Typography, motion, and site chrome refinements (UX-4/UX-5/UX-6).
- Loading/empty/error polish enhancements (UX-7).

## Decisions

1. Map engine is MapLibre GL JS for vector style control and open-source licensing.
2. React integration uses `react-map-gl` MapLibre entrypoint (`react-map-gl/maplibre`) to minimize bespoke map lifecycle wiring.
3. Migration remains behind existing component boundary:
   - `MapPanelLeaflet` -> `MapPanelMapLibre`
   - `MapPanel` and `MapPanelChromeless` public interfaces unchanged.
4. UK map constraints are enforced via map options and runtime move guards:
   - approximate bounds SW `[49.5, -8.2]`, NE `[61.0, 2.0]`
   - `minZoom` around `5`, `maxZoom` around `17`.
5. Landing state always renders a map canvas (no empty placeholder panel) even before first successful search.
6. Failure behavior must be explicit: if vector style/source fails to load, retain container layout and render actionable fallback messaging instead of blank canvas.

## Frontend Design

### Map component migration

- Replace lazy import target in:
  - `apps/web/src/components/maps/MapPanel.tsx`
  - `apps/web/src/components/maps/MapPanelChromeless.tsx`
- New map implementation file:
  - `apps/web/src/components/maps/MapPanelMapLibre.tsx`

### Map style configuration

Introduce style/config modules under shared ownership:

- `apps/web/src/shared/maps/map-style.ts`
  - resolves style URL/object from env and defaults.
  - provides style attribution metadata.
- `apps/web/src/shared/maps/map-bounds.ts`
  - central UK bounds, minZoom, maxZoom, default center/zoom.

### CSS and token integration

- Remove Leaflet-specific CSS selectors from `apps/web/src/styles/theme.css`.
- Add MapLibre control/focus styling hooks aligned to semantic tokens.

### Accessibility parity

- Ensure markers remain keyboard focusable and popup controls remain screen-reader discoverable.
- Ensure zoom controls meet touch target minimums on mobile.

## File-Oriented Implementation Plan

1. `apps/web/package.json`
   - add `maplibre-gl` and `react-map-gl`.
   - remove `leaflet`, `react-leaflet`, and `@types/leaflet`.
2. `apps/web/src/components/maps/MapPanelMapLibre.tsx` (new)
   - MapLibre map container, vector source/style loading, markers, popups, controls.
3. `apps/web/src/components/maps/MapPanel.tsx`
   - lazy-load `MapPanelMapLibre`.
4. `apps/web/src/components/maps/MapPanelChromeless.tsx`
   - lazy-load `MapPanelMapLibre` and preserve chromeless behavior.
5. `apps/web/src/shared/maps/map-style.ts` (new)
   - map style resolver and provider fallback contract.
6. `apps/web/src/shared/maps/map-bounds.ts` (new)
   - central UK bounds and default viewport constants.
7. `apps/web/src/features/schools-search/components/SchoolsMap.tsx`
   - ensure map center behavior supports UK landing view for idle/loading/error states.
8. `apps/web/src/styles/theme.css`
   - remove Leaflet-specific control/attribution selectors and add MapLibre equivalents.
9. `apps/web/scripts/check-budgets.mjs`
   - update map-chunk detection pattern to include `maplibre` and `react-map-gl` chunk names.
10. `apps/web/e2e/schools-search.spec.ts`
    - migrate selectors away from `.leaflet-*` classes.

## Testing And Quality Gates

### Required tests

- Unit/component:
  - `MapPanel` and `MapPanelChromeless` lazy-load path still works.
  - map style resolver behavior for default and env-driven config.
  - fallback rendering when style load fails.
- E2E:
  - UK bounds enforcement (cannot pan beyond configured extent).
  - keyboard marker focus and popup activation.
  - mobile zoom controls remain >= 44x44 px.

### Required commands

- `cd apps/web && npm run lint`
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run test`
- `cd apps/web && npm run build`
- `cd apps/web && npm run budget:check`
- `cd apps/web && npm run lighthouse:check`
- `cd apps/web && npm run test:e2e`
- `make lint`
- `make test`

## Acceptance Criteria

1. Leaflet stack is fully removed from dependencies and runtime.
2. Search page renders UK-bounded vector map at first load.
3. User cannot pan map outside configured UK bounds.
4. Marker/popup keyboard and screen-reader behavior is preserved.
5. Map-chunk and web performance budgets remain within thresholds.
6. Style/source failures are recoverable and do not leave an unusable map area.

## Risks And Mitigations

- Risk: Map chunk growth reduces room for downstream UX work.
  - Mitigation: re-baseline bundle budgets immediately after UX-1 and track headroom before UX-2/UX-5.
- Risk: vector provider outages or token/config mistakes break map rendering.
  - Mitigation: centralized style resolver with fallback and explicit error UI.
- Risk: migration breaks existing E2E and accessibility assumptions tied to Leaflet CSS classes.
  - Mitigation: replace class-based selectors with role/data-testid selectors and add parity checks.
- Risk: browser/WebGL compatibility regressions.
  - Mitigation: include a tested non-blank fallback panel for unsupported or failed rendering paths.