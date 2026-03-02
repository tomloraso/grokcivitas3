# Phase UX-6 Design - Navigation And Site Chrome Refinement

## Document Control

- Status: Draft
- Last updated: 2026-03-02
- Depends on:
  - `.planning/phases/phase-1/1F-web-routing-navigation-foundation.md`
  - `.planning/phases/phase-ux/UX-1-maplibre-migration-uk-bounds-landing-state.md`
  - `.planning/phases/phase-ux/UX-3-overlay-panel-refinement.md`
  - `docs/architecture/frontend-conventions.md`

## Objective

Refine global navigation chrome so map-focused routes prioritize spatial context while preserving clear orientation and route recovery.

## Scope

### In scope

- Transparent/receding header behavior on search map route.
- Contextual search chips/breadcrumb linkage by postcode context.
- Footer suppression on map-primary route and retention on profile/static routes.
- Active search context indicator in header chrome.

### Out of scope

- Route model changes introduced in Phase 1.
- Typography-system changes (UX-4).
- Motion choreography details beyond what is needed for chrome state transitions (UX-5).

## Decisions

1. Search route (`/`) is treated as a map-primary experience with low-visual-noise chrome.
2. Profile and non-map routes keep stronger chrome presence for orientation.
3. Breadcrumb context should include originating postcode when available and safely encoded in navigation state/query.
4. Footer is hidden on map-primary route to preserve viewport height for map and overlay interactions.

## Frontend Design

### Header behavior

- Search route:
  - transparent by default.
  - gains backdrop once panel scroll/collapse threshold is crossed.
- Profile/static routes:
  - existing solid header behavior retained.

### Context navigation

- Search result context chip in header (postcode/area + radius).
- Profile breadcrumb: Home / [Postcode search context] / School Name.

### Footer behavior

- conditionally render footer by route classification.

## File-Oriented Implementation Plan

1. `apps/web/src/components/layout/AppShell.tsx`
   - route-aware chrome mode flags (map-primary versus standard).
2. `apps/web/src/components/layout/SiteHeader.tsx`
   - transparent/search-specific behavior and context chips.
3. `apps/web/src/components/layout/SiteFooter.tsx`
   - conditional hide behavior for search map route.
4. `apps/web/src/components/layout/Breadcrumbs.tsx`
   - include optional postcode context path segment.
5. `apps/web/src/shared/routing/paths.ts`
   - add helper for preserving search context parameters where needed.
6. `apps/web/src/features/schools-search/SchoolsSearchFeature.tsx`
   - expose active search context to header state source.
7. `apps/web/src/components/layout/site-chrome.test.tsx`
   - add route-mode behavior assertions.
8. `apps/web/e2e/schools-search.spec.ts`
   - assert header/footer behaviors on search route and profile route.

## Testing And Quality Gates

### Required tests

- Unit/component:
  - header mode changes by route/context.
  - footer visibility by route.
  - breadcrumb rendering with and without postcode context.
- E2E:
  - search page shows map-first chrome.
  - profile page restores full chrome and breadcrumb path.

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

1. Header visually recedes on search map route and remains readable.
2. Footer does not consume viewport on search map route.
3. Profile route breadcrumb includes one-click return to search context when present.
4. Site chrome behavior remains accessible and keyboard navigable.

## Risks And Mitigations

- Risk: route-aware chrome logic becomes brittle.
  - Mitigation: centralize route classification in shared shell logic.
- Risk: context propagation leaks stale postcode data.
  - Mitigation: explicit query/state ownership with deterministic reset conditions.
- Risk: transparency harms legibility over map background.
  - Mitigation: threshold-driven backdrop opacity and contrast checks.