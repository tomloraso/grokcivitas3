# Phase 5 / UX-2 Design - Map Interaction Depth

## Document Control

- Status: Complete
- Last updated: 2026-03-03
- Depends on:
  - `.planning/phases/phase-ux/UX-1-maplibre-migration-uk-bounds-landing-state.md`
  - `.planning/phases/phase-0/0D-web-search-map.md`
  - `docs/architecture/frontend-conventions.md`

## Objective

Deepen map/list interaction quality so the map behaves as a first-class analytical surface rather than a passive marker background.

## Scope

### In scope

- Fly-to animation on search completion.
- Radius overlay rendering for current search radius.
- Bi-directional list-marker hover/focus linking.
- Marker clustering for dense result sets.
- Data-driven marker visual encoding (rating/phase with deterministic fallback).
- Compact map popup card with profile deep-link.

### Out of scope

- Map engine migration and UK bounds (UX-1).
- Overlay panel mechanics and bottom-sheet (UX-3).
- Page-level transitions and global motion choreography (UX-5).

## Decisions

1. Use MapLibre native GeoJSON clustering (`cluster`, `clusterRadius`, `clusterMaxZoom`) and avoid third-party clustering dependencies.
2. Maintain one canonical source of search results; list and map derive from the same mapped view-model to prevent drift.
3. Hover and keyboard focus both drive highlight state for accessibility parity.
4. Marker colour encoding uses deterministic precedence:
   - Ofsted rating when available.
   - fallback to school phase when rating unavailable.
   - fallback to neutral token when both unavailable.
5. Fly-to animation timing must respect `prefers-reduced-motion` (instant recenter when reduced motion is enabled).

## Frontend Design

### Shared interaction state

Add a focused interaction-state model in the schools-search feature:

- `activeSchoolId` (hover/focus/selected marker linkage).
- `mapViewTarget` (center/zoom to fly to after search).

### Map layers

- Base school points source.
- Cluster circles + cluster count symbols.
- Unclustered point markers with interactive hover/selected style variants.
- Radius overlay source/layer anchored to current search center and radius.

### List integration

- Result cards emit hover/focus events with school id.
- Map marker hover/focus updates list highlight and optional `scrollIntoView` behavior.

## File-Oriented Implementation Plan

1. `apps/web/src/features/schools-search/types.ts`
   - extend map marker view-model with interaction metadata and optional rating/phase fields.
2. `apps/web/src/features/schools-search/SchoolsSearchFeature.tsx`
   - own shared `activeSchoolId` and interaction callbacks.
3. `apps/web/src/features/schools-search/components/SchoolsList.tsx`
   - emit hover/focus events and render active-card styling.
4. `apps/web/src/features/schools-search/components/SchoolsMap.tsx`
   - pass interaction props into map panel boundary.
5. `apps/web/src/components/maps/MapPanelMapLibre.tsx`
   - implement fly-to behavior, radius layer, clustering, hover/focus linking, popup layout.
6. `apps/web/src/shared/maps/` (new helpers as needed)
   - radius-to-GeoJSON helper and marker-style expression helpers.
7. `apps/web/src/components/ui/ResultCard.tsx`
   - add optional active-state and hover/focus callback props.
8. `apps/web/e2e/schools-search.spec.ts`
   - add interaction assertions (hover linking, fly-to, cluster expand behavior).

## Testing And Quality Gates

### Required tests

- Unit/component:
  - fly-to invocation behavior including reduced-motion branch.
  - marker/list active-state linking from both directions.
  - clustering layer visibility across zoom thresholds.
  - radius GeoJSON helper correctness.
- E2E:
  - search triggers visible map recenter.
  - card hover highlights marker and marker hover highlights card.
  - dense fixture clusters at low zoom and expands on zoom in.

### Required commands

- `cd apps/web && npm run lint`
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run test`
- `cd apps/web && npm run build`
- `cd apps/web && npm run budget:check`
- `cd apps/web && npm run test:e2e`
- `make lint`
- `make test`

## Acceptance Criteria

1. Search submits trigger smooth map recenter (or instant recenter under reduced motion).
2. Radius overlay renders correctly from active query parameters.
3. List and map are bi-directionally linked by hover/focus state.
4. Dense result sets cluster and expand predictably as zoom changes.
5. Marker styling communicates primary school metadata at a glance.

## Risks And Mitigations

- Risk: interaction complexity causes fragile state coupling between map and list.
  - Mitigation: centralize active-id state and keep child components controlled.
- Risk: clustering and per-marker interaction increase render cost.
  - Mitigation: prefer layer-based rendering over large DOM marker trees where possible.
- Risk: keyboard users lose parity with pointer-only hover features.
  - Mitigation: mirror hover behavior through focus handlers and explicit aria semantics.
