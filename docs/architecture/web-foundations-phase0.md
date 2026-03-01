# Web Foundations (Phase 0D1)

This document tracks the implemented frontend foundation baseline introduced in Phase 0D1.

## Scope delivered

1. Tailwind + PostCSS styling pipeline wired for Vite.
2. Tokenized dark-first theme with core, semantic, and component tokens.
3. Shared local UI primitives and layout components for 0D2 composition.
4. Lazy-loaded Leaflet map boundary with configurable dark tile providers.
5. Quality rails for accessibility, responsiveness, and performance budgets and Lighthouse checks.

## Styling and tokens

- `apps/web/src/styles/tokens.css`: core + semantic + component token values.
- `apps/web/src/styles/theme.css`: font imports, global theme baseline, map control styling.
- `apps/web/src/styles.css`: token/theme imports plus Tailwind layers.
- `apps/web/tailwind.config.ts`: semantic token mapping for colors, typography, spacing, radius, elevation, z-index.

## Shared component baseline

Phase 0D1 shared components live under `apps/web/src/components`:

- Layout: `layout/AppShell.tsx`, `layout/PageContainer.tsx`, `layout/SplitPaneLayout.tsx`
- UI: `ui/Button.tsx`, `ui/Card.tsx`, `ui/TextInput.tsx`, `ui/Select.tsx`, `ui/Field.tsx`, `ui/LoadingSkeleton.tsx`, `ui/EmptyState.tsx`, `ui/ErrorState.tsx`, `ui/ResultCard.tsx`
- Maps: `maps/MapPanel.tsx`, `maps/MapPanelLeaflet.tsx`

Radix boundary rule:

- Raw `@radix-ui/*` imports are restricted to `src/components/ui/*` by ESLint.

## Map provider strategy

- Primary default: CartoDB Dark Matter (`dark_all`).
- Provider config source: `src/shared/maps/map-tiles.ts` (feature compatibility re-export remains at `src/features/schools-search/config/map-tiles.ts`).
- Runtime behavior: `MapPanelLeaflet` switches to fallback provider on tile error.

## Quality rails

## Accessibility

- Accessibility smoke tests run with `vitest-axe` for shell, layout, and primitives.
- Contrast pairings required by 0D1 are enforced by `src/styles/contrast.test.ts` against token values.
- E2E coverage validates keyboard activation for map markers and popups in `apps/web/e2e/schools-search.spec.ts`.

## Responsiveness

- `SplitPaneLayout` provides the mobile-first single-column to desktop split-pane transition.
- Touch target minimum enforced through 44px control heights (`h-11`) for primary inputs/buttons and
  44px Leaflet zoom controls in the map panel.
- Playwright smoke coverage validates desktop/tablet/mobile layout behavior in `apps/web/e2e/schools-search.spec.ts`.

## Performance

- Map stack is lazy-loaded through `MapPanel -> MapPanelLeaflet` dynamic import.
- Build budget enforcement script: `apps/web/scripts/check-budgets.mjs`.
- Lighthouse budget enforcement script: `apps/web/scripts/check-lighthouse.mjs`.
- Current thresholds:
  - App shell JS: <= 170 KiB gzip
  - App shell CSS: <= 35 KiB gzip
  - Lazy map chunk JS: <= 260 KiB gzip
  - Mobile LCP: <= 2.0s
  - Mobile CLS: <= 0.10
  - Mobile TBT: <= 200ms
- Latest Lighthouse snapshot artifact: `apps/web/artifacts/lighthouse/latest.json`.

## Validation commands

Run from repo root:

```bash
make lint
make test
cd apps/web && npm run build
cd apps/web && npm run budget:check
cd apps/web && npm run lighthouse:check
```
