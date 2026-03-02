# Phase UX-7 Design - Loading And Empty State Polish

## Document Control

- Status: Draft
- Last updated: 2026-03-02
- Depends on:
  - `.planning/phases/phase-ux/UX-2-map-interaction-depth.md`
  - `.planning/phases/phase-ux/UX-3-overlay-panel-refinement.md`
  - `.planning/phases/phase-ux/UX-4-typography-spacing-visual-hierarchy.md`
  - `docs/architecture/frontend-conventions.md`

## Objective

Replace generic loading/empty/error placeholders with contextual, map-aware states that preserve user orientation and reduce perceived friction.

## Scope

### In scope

- Shaped skeletons aligned with actual result-card layout.
- Map loading indicator centered on query target area.
- Empty-result messaging coupled with visible search-radius context.
- Error handling that preserves last-known map state and supports retry.

### Out of scope

- New backend API endpoints.
- Major interaction additions already covered in UX-2.
- Global motion strategy (UX-5), except where needed for loading affordance.

## Decisions

1. Last successful map context remains visible during loading/error transitions whenever possible.
2. Loading and empty states are spatially anchored (map plus panel), not panel-only placeholders.
3. Error state uses non-blocking notification with explicit retry, rather than full-panel hard reset.
4. Skeletons should mirror actual UI geometry to improve perceived responsiveness.

## Frontend Design

### State behavior

- Loading:
  - keep map visible.
  - pulse/search-radius indicator at current or incoming center.
  - shaped list skeletons in panel.
- Empty:
  - retain center and radius overlay.
  - show actionable copy to widen radius or try nearby postcode.
- Error:
  - retain last-known map and list context when possible.
  - show toast and retry control.

### Component strategy

- keep reusable state components in shared UI layer (`LoadingSkeleton`, `EmptyState`, `ErrorState`) but add map-aware variants in schools-search feature.

## File-Oriented Implementation Plan

1. `apps/web/src/components/ui/LoadingSkeleton.tsx`
   - add shaped variant API for result-card geometry.
2. `apps/web/src/components/ui/EmptyState.tsx`
   - support richer action/context slots for map-linked messaging.
3. `apps/web/src/components/ui/ErrorState.tsx`
   - support non-destructive retry presentation.
4. `apps/web/src/features/schools-search/hooks/useSchoolsSearch.ts`
   - preserve last successful result context for error fallback rendering.
5. `apps/web/src/features/schools-search/components/SchoolsList.tsx`
   - shaped skeletons and contextual empty/error copy updates.
6. `apps/web/src/features/schools-search/components/SchoolsMap.tsx`
   - loading pulse, empty-state radius overlay, and error-state map retention.
7. `apps/web/src/components/maps/MapPanelMapLibre.tsx`
   - optional transient loading-layer support.
8. `apps/web/src/features/schools-search/SchoolsSearchFeature.tsx`
   - orchestration for state-specific map/list composition.
9. `apps/web/e2e/schools-search.spec.ts`
   - add loading/empty/error journey assertions.

## Testing And Quality Gates

### Required tests

- Unit/component:
  - shaped skeleton variant rendering.
  - empty-state contextual copy and action visibility.
  - error retry path preserves context state.
- E2E:
  - loading state shows map-area feedback.
  - empty state keeps search radius visible.
  - error state keeps last-known map context and allows retry recovery.

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

1. Loading skeletons match result-card geometry and reduce visual jank.
2. Map shows spatial loading cue during in-flight searches.
3. Empty-result flow keeps map/radius context with actionable guidance.
4. Error flow preserves context and supports immediate retry.
5. Accessibility and performance gates remain green.

## Risks And Mitigations

- Risk: state orchestration becomes complex with context preservation.
  - Mitigation: explicit state model for `current` versus `lastSuccessful` search snapshots.
- Risk: additional loading overlays reduce map clarity.
  - Mitigation: keep overlays subtle and time-bound.
- Risk: richer state UI increases maintenance burden.
  - Mitigation: centralize reusable state components and keep feature-specific wrappers thin.