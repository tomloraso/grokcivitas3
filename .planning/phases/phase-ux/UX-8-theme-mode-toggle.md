# Phase UX-8 Design - Theme Mode Toggle (Dark And Light)

## Document Control

- Status: Proposed
- Last updated: 2026-03-03
- Depends on:
  - `.planning/phases/phase-ux/UX-1-maplibre-migration-uk-bounds-landing-state.md`
  - `.planning/phases/phase-ux/UX-4-typography-spacing-visual-hierarchy.md`
  - `.planning/phases/phase-ux/UX-6-navigation-site-chrome-refinement.md`
  - `docs/architecture/frontend-conventions.md`

## Objective

Add a user-selectable dark/light mode toggle across the Civitas web app, including map rendering, while preserving accessibility, visual consistency, and map-first clarity.

## Scope

### In scope

- Theme mode system with `dark`, `light`, and `system` preference handling.
- Header-level theme toggle available on search and profile routes.
- Persisted theme preference in browser storage with deterministic hydration behavior.
- Semantic design tokens for both dark and light themes (no hard-coded feature colors).
- Map style parity for both themes through explicit style assets (`civitas-dark.json` and `civitas-light.json`).
- Automated tests for toggle behavior, persistence, and theme-correct rendering of key surfaces.

### Out of scope

- Additional branded themes beyond dark and light.
- Backend-stored theme preference and account-level cross-device sync.
- Major typography, spacing, or layout redesign outside UX-4 standards.
- New backend API endpoints.

## Decisions

1. Theme precedence order is explicit user preference, then system preference, then dark fallback.
2. Theme state is app-level infrastructure (`ThemeProvider`) and applied through a root `data-theme` attribute.
3. Feature/UI modules consume semantic tokens only; no route-specific hard-coded color escapes.
4. Toggle control must be keyboard/screen-reader friendly and visible in primary site chrome.
5. Map style selection is theme-aware and driven through shared map-style configuration.

## Frontend Design

### Theme model

- Persist mode under a stable storage key (for example `civitas.theme.mode`).
- Support three persisted values:
  - `dark`
  - `light`
  - `system`
- Resolve active runtime theme from persisted mode plus `prefers-color-scheme`.

### UI behavior

- Add a theme toggle control in `SiteHeader`.
- Ensure control has:
  - descriptive accessible label,
  - deterministic state indication (`aria-pressed` and/or selected option semantics),
  - touch-target compliance on mobile.
- Keep the toggle behavior route-consistent (search and profile).

### Styling contract

- Extend token surfaces in `tokens.css` for light values with contrast-safe text/surface/border combinations.
- Keep existing dark palette contract as first-class and unchanged unless required for parity fixes.
- Use semantic aliases in feature styles so both themes render correctly without feature-level overrides.

### Map parity

- Add `civitas-light.json` with the same cartographic hierarchy rules as the dark style:
  - subdued base layers,
  - clear geometry,
  - data markers remain primary attention anchors.
- Switch map style by active theme mode without breaking bounds/interaction behaviors from UX-1/UX-2.

## File-Oriented Implementation Plan

1. `apps/web/src/app/providers/ThemeProvider.tsx` (new)
   - app-level theme mode state, hydration, persistence, and `data-theme` wiring.
2. `apps/web/src/app/main.tsx` (or provider composition entrypoint)
   - register `ThemeProvider` at app root.
3. `apps/web/src/styles/tokens.css`
   - add light-theme semantic token set.
4. `apps/web/src/styles/theme.css`
   - remove dark-only assumptions and rely on semantic variables.
5. `apps/web/src/components/layout/SiteHeader.tsx`
   - add theme mode toggle UI and route-stable placement.
6. `apps/web/src/shared/theme/theme-mode.ts` (new)
   - theme mode constants, parsing, and precedence helpers.
7. `apps/web/src/shared/maps/map-style.ts`
   - resolve style asset by active theme.
8. `apps/web/src/shared/maps/civitas-light.json` (new)
   - light-mode map style artifact aligned with UX-1 hierarchy rules.
9. `apps/web/src/components/maps/MapPanelMapLibre.tsx`
   - react to theme style changes without regressing map interaction behavior.
10. `apps/web/src/components/layout/site-chrome.test.tsx`
    - cover theme toggle rendering and interaction behavior.
11. `apps/web/src/components/maps/map-panel-maplibre.test.tsx` (or equivalent)
    - cover theme-based style selection behavior.
12. `apps/web/e2e/schools-search.spec.ts`
    - add cross-route theme persistence and map-style parity assertions.

## Testing And Quality Gates

### Required tests

- Unit/component:
  - theme-mode parser and precedence rules.
  - header toggle state and accessibility behavior.
  - map-style resolver returns dark/light style deterministically.
- E2E:
  - toggling theme updates app surfaces and persists after refresh.
  - selected mode is preserved across route changes.
  - map remains interactive and correctly styled after theme switch.

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

1. User can switch between dark and light mode from site chrome on desktop and mobile.
2. Theme choice persists across page refresh and route transitions.
3. Both themes meet accessibility contrast expectations for primary surfaces and text.
4. Map uses theme-matched style assets and remains fully interactive.
5. Existing UX-1 to UX-7 behavior remains functionally intact.
6. Repository quality gates remain green.

## Risks And Mitigations

- Risk: flash of incorrect theme during hydration.
  - Mitigation: apply initial theme mode before first paint via provider bootstrap logic.
- Risk: token drift causes partial dark-only styling in feature components.
  - Mitigation: enforce semantic-token-only lint/review checks for changed files.
- Risk: theme switching triggers map style reload jank.
  - Mitigation: preserve map viewport/interaction state while swapping style artifacts.
