# Phase 5 / UX-3 Design - Overlay Panel Refinement

## Document Control

- Status: Complete
- Last updated: 2026-03-03
- Depends on:
  - `.planning/phases/phase-ux/UX-1-maplibre-migration-uk-bounds-landing-state.md`
  - `.planning/phases/phase-0/0D1-web-foundations.md`
  - `.planning/phases/phase-1/1F-web-routing-navigation-foundation.md`
  - `docs/architecture/frontend-conventions.md`

## Objective

Refine the floating overlay panel into a premium interaction surface with strong desktop ergonomics and a map-visible mobile bottom-sheet experience.

## Scope

### In scope

- Hide native panel scrollbars while preserving wheel/touch/keyboard scroll behavior.
- Add top/bottom scroll shadows as explicit scroll affordance.
- Add result-entry and card-hover micro-interactions.
- Add desktop panel collapse/expand behavior.
- Implement mobile bottom-sheet overlay pattern with persistent map visibility.
- Show persistent result context summary (count/radius/postcode).

### Out of scope

- Map interaction primitives (UX-2).
- Typography system-level refinements (UX-4).
- Route transition choreography (UX-5).

## Decisions

1. Overlay mechanics remain owned by `MapOverlayLayout`; feature-level children remain content-only.
2. Hidden-scrollbar behavior must not break keyboard scroll, focus order, or discoverability.
3. Desktop collapse state is persisted per session (localStorage key) for user control continuity.
4. Mobile bottom-sheet starts at a peek height and supports drag-to-expand with explicit accessible controls.
5. Any third-party bottom-sheet dependency must justify bundle cost; default path is hand-rolled first.

## Frontend Design

### Layout behavior

- Desktop:
  - panel width remains constrained.
  - collapsed rail mode keeps search summary visible.
- Mobile:
  - panel anchored to bottom.
  - map remains visible above folded/peek state.
  - drag handle and keyboard-accessible expand/collapse controls.

### Scroll affordance

- sentinel elements + IntersectionObserver to toggle top/bottom shadow visibility.
- `aria-live` or visually hidden status text for collapsed/expanded state changes.

## File-Oriented Implementation Plan

1. `apps/web/src/components/layout/MapOverlayLayout.tsx`
   - add panel collapse state, mobile bottom-sheet mode, drag/expand behavior, and scroll-shadow hooks.
2. `apps/web/src/components/layout/MapOverlayLayout.test.tsx`
   - add desktop collapse and mobile behavior coverage.
3. `apps/web/src/features/schools-search/SchoolsSearchFeature.tsx`
   - provide context summary text and hooks for panel state display.
4. `apps/web/src/features/schools-search/components/SchoolsList.tsx`
   - apply staged reveal classes and active hover styles.
5. `apps/web/src/components/ui/ResultCard.tsx`
   - card hover/lift/glow variants.
6. `apps/web/src/styles/theme.css`
   - hidden scrollbar utilities, scroll-shadow styles, and panel animation tokens.
7. `apps/web/e2e/schools-search.spec.ts`
   - add desktop collapse and mobile sheet interaction assertions.

## Testing And Quality Gates

### Required tests

- Unit/component:
  - collapse/expand state transitions and aria labels.
  - scroll-shadow visibility toggles with scroll position.
  - mobile panel initial peek versus expanded behavior.
- E2E:
  - desktop collapse toggle reduces panel width and remains interactive.
  - mobile panel expands/collapses while map remains visible.
  - keyboard navigation remains possible with hidden scrollbar styling.

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

1. Panel scrollbars are hidden without loss of usable scrolling.
2. Scroll shadows indicate additional content above/below viewport.
3. Desktop users can collapse and expand panel state reliably.
4. Mobile users get a bottom-sheet interaction model with visible map context.
5. Results context summary stays visible and updates per query.

## Risks And Mitigations

- Risk: hidden scrollbar treatment harms usability for some users.
  - Mitigation: preserve keyboard scroll and add clear visual scroll shadows.
- Risk: mobile drag interactions conflict with map gestures.
  - Mitigation: explicit gesture zones and touch-action tuning per element.
- Risk: panel complexity causes fragile layout regressions across breakpoints.
  - Mitigation: keep logic centralized in `MapOverlayLayout` with viewport-specific tests.
