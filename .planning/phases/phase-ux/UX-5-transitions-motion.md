# Phase UX-5 Design - Transitions And Motion

## Document Control

- Status: Draft
- Last updated: 2026-03-02
- Depends on:
  - `.planning/phases/phase-ux/UX-2-map-interaction-depth.md`
  - `.planning/phases/phase-ux/UX-3-overlay-panel-refinement.md`
  - `.planning/phases/phase-ux/UX-4-typography-spacing-visual-hierarchy.md`
  - `docs/architecture/frontend-conventions.md`

## Objective

Introduce purposeful motion and route continuity that improves orientation, perceived quality, and map/list spatial coherence without harming performance or accessibility.

## Scope

### In scope

- Search/profile transition continuity (cross-fade or progressive view transitions).
- Overlay panel mount and results-section reveal motion.
- Marker entrance animation behavior for new result sets.
- Scroll-linked panel backdrop opacity refinement.
- Full reduced-motion support for non-essential animations.

### Out of scope

- Structural layout changes from UX-3.
- Typography/content hierarchy changes from UX-4.
- Net-new map interaction behavior beyond UX-2 primitives.

## Decisions

1. Motion is additive and optional; functional behavior must not depend on animation completion.
2. View Transitions API is progressive enhancement only.
3. Baseline fallback is CSS/React-driven transitions that work across supported browsers.
4. `prefers-reduced-motion` disables non-essential transitions, stagger effects, and marker animations.
5. Motion budgets must not materially increase TBT or violate Lighthouse thresholds.

## Frontend Design

### Route continuity

- Search -> profile:
  - cross-fade plus subtle content translation.
- Profile -> search:
  - preserve map context and avoid hard-cut flash.

### Interaction motion

- Results load:
  - panel content reveal and marker entrance.
- Scroll response:
  - backdrop opacity tied to panel scroll depth.

### Reduced motion

- central utility hook to detect `prefers-reduced-motion` and gate motion paths consistently.

## File-Oriented Implementation Plan

1. `apps/web/src/shared/` (new utility)
   - add `useReducedMotion` hook and shared motion constants.
2. `apps/web/src/app/` or route composition modules
   - add route transition wrapper/progressive enhancement handling.
3. `apps/web/src/components/layout/MapOverlayLayout.tsx`
   - panel entry motion and scroll-linked backdrop behavior.
4. `apps/web/src/components/maps/MapPanelMapLibre.tsx`
   - marker appearance animation guard by reduced-motion preference.
5. `apps/web/src/styles/theme.css`
   - transition tokens, keyframes, reduced-motion media query fallbacks.
6. `apps/web/src/features/schools-search/SchoolsSearchFeature.tsx`
   - coordinate result-state motion classes.
7. `apps/web/e2e/schools-search.spec.ts`
   - add assertions for reduced-motion behavior and transition presence.

## Testing And Quality Gates

### Required tests

- Unit/component:
  - reduced-motion utility behavior.
  - animation class toggles across loading/success states.
- E2E:
  - route transition continuity visible in default motion mode.
  - reduced-motion mode disables non-essential animation.
- Performance:
  - Lighthouse and budget checks remain green after motion changes.

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

1. Search/profile navigation has visible continuity instead of hard transitions.
2. Marker/result entrance animations improve readability without delaying interaction.
3. Reduced-motion users get functional parity with minimized animation.
4. Motion changes keep web performance gates passing.

## Risks And Mitigations

- Risk: over-animated UI reduces clarity.
  - Mitigation: constrain motion to orientation and hierarchy cues only.
- Risk: browser differences create inconsistent route transitions.
  - Mitigation: progressive enhancement with deterministic fallback path.
- Risk: motion regressions are hard to test reliably.
  - Mitigation: central motion utilities and explicit reduced-motion automated checks.