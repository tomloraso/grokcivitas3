# Phase 0D1 Design - Web Foundations And Brand Baseline

## Document Control

- Status: Implemented
- Last updated: 2026-02-28
- Depends on:
  - `.planning/project-brief.md`
  - `.planning/phases/phase-0/0C-postcode-search-api.md`
  - `docs/architecture/principles.md`
  - `docs/architecture/testing-strategy.md`
  - `docs/architecture/frontend-conventions.md`

## Objective

Establish production-grade frontend foundations before 0D2 implementation so the first user-facing search/map slice is polished, accessible, performant, and easy to evolve over time.

## Implementation Progress (2026-02-28)

- Completed: Tailwind + PostCSS styling engine wired for Vite (`tailwind.config.ts`, `postcss.config.js`).
- Completed: Core/semantic/component token files added (`src/styles/tokens.css`, `src/styles/theme.css`) and consumed via global `src/styles.css`.
- Completed: Required shared layout and UI baseline components implemented under local ownership:
  - `src/components/layout/{AppShell,PageContainer,SplitPaneLayout}.tsx`
  - `src/components/ui/{Card,Button,TextInput,Select,Field,LoadingSkeleton,EmptyState,ErrorState,ResultCard}.tsx`
  - `src/components/maps/{MapPanel,MapPanelLeaflet}.tsx`
- Completed: Map tile provider configuration with primary/fallback resolution added (`src/shared/maps/map-tiles.ts`) with feature compatibility re-export (`src/features/schools-search/config/map-tiles.ts`).
- Completed: Frontend code-quality rail for Radix ownership boundary added in ESLint (raw `@radix-ui/*` imports restricted outside shared UI internals).
- Completed: Accessibility and responsiveness smoke tests added for shell/layout/primitives and map keyboard/touch interactions (`src/App.test.tsx`, `src/components/**/**/*.test.tsx`, `e2e/schools-search.spec.ts`), plus deterministic token contrast regression tests (`src/styles/contrast.test.ts`).
- Completed: Performance budget enforcement added (`scripts/check-budgets.mjs`) with thresholds:
  - app shell JS <= 170 KiB gzip
  - app shell CSS <= 35 KiB gzip
  - lazy map chunk JS <= 260 KiB gzip
- Completed: Lighthouse mobile budget enforcement and snapshot capture added (`scripts/check-lighthouse.mjs`) with thresholds:
  - LCP <= 2.0s
  - CLS <= 0.10
  - TBT <= 200ms
- Completed: Web gates executed and passing (`npm run lint`, `npm run typecheck`, `npm run test`, `npm run build`, `npm run budget:check`), with repository-level gates also passing (`make lint`, `make test`).

## Contrast Verification Snapshot (2026-02-28)

Validated with deterministic contrast calculation against seeded dark theme colors:

| Pairing | Ratio | Target | Status |
|---|---:|---:|---|
| `--color-text-primary` on `--color-bg-canvas` | 17.84:1 | >= 4.5:1 | pass |
| `--color-text-primary` on `--color-bg-surface` | 16.08:1 | >= 4.5:1 | pass |
| `--color-text-secondary` on `--color-bg-surface` | 6.56:1 | >= 4.5:1 | pass |
| `--color-text-secondary` on `--color-bg-canvas` | 7.28:1 | >= 4.5:1 | pass |
| `--color-action-primary` on `--color-bg-surface` | 3.97:1 | >= 3:1 | pass |
| white text on `--color-action-primary-solid` | 5.70:1 | >= 4.5:1 | pass |
| `--color-state-success` on `--color-bg-surface` | 7.38:1 | >= 3:1 | pass |
| `--color-state-warning` on `--color-bg-surface` | 7.83:1 | >= 3:1 | pass |
| `--color-state-danger` on `--color-bg-surface` | 4.47:1 | >= 3:1 | pass |
| `--color-state-info` on `--color-bg-surface` | 4.57:1 | >= 3:1 | pass |

## Scope

### In scope

- Define a clear Civitas visual baseline using the provided reference points:
  - `https://shadow.wickedtemplates.com/` for layered modern UI composition.
  - `https://peaceandquiet.io/uk` for map-first control density and overlay patterns.
- Convert visual direction into tokenized design foundations:
  - color, typography, spacing, radius, elevation, motion, z-index, and breakpoints.
- Implement semantic theming on top of core tokens so future rebranding/style shifts do not require component rewrites.
- Adopt accessible UI primitives (Radix-based) wrapped in local Civitas components.
- Build a reusable baseline component set for Phase 0-1 web delivery.
- Establish frontend quality rails for accessibility, responsiveness, performance, and code quality.
- Commit to a single styling engine for predictable component implementation.

### Out of scope

- Full marketing template rollout.
- Complete multi-theme runtime switching (token model should support future addition).
- Advanced animation choreography beyond lightweight transitions.
- Phase 1+ feature-specific domain UI (profiles, comparisons, paywall flows).
- Runtime light/dark toggle in Phase 0 (token architecture keeps a clear path for a future light theme).

## Decisions

1. **Visual direction**: dark-first, data-forward, high-contrast, modern "civic intelligence" style inspired by Shadow (layered dark surfaces, vivid accent, typographic clarity). Not a template clone - a Civitas-owned visual language built on the same principles.
2. **Token-first architecture**: all visual styling flows through design tokens and semantic aliases.
3. **Styling engine**: use Tailwind CSS as the component styling engine, backed by semantic CSS custom properties from token files.
4. **Primitive strategy**: use shadcn-style local components under `apps/web/src/components/ui` with selective Radix primitives; feature code must not depend on raw Radix APIs directly.
5. **Reference usage strategy**: references are inspiration for interaction and composition, not direct cloning.
6. **Quality as release gate**: accessibility, responsiveness, and performance checks are mandatory acceptance criteria before 0D2 closeout.
7. **Theme scope**: dark theme is the default and only theme in Phase 0. Light mode is deferred. Token architecture must support adding a light semantic map in future without component rewrites.
8. **Map tiles**: use dark-compatible map tile provider (CartoDB Dark Matter or equivalent) so the map integrates visually with the dark shell. Default Leaflet/OSM tiles are not acceptable.
9. **Contrast verification**: every semantic token pairing (text on surface, accent on surface, muted on canvas) must be verified against WCAG 2.2 AA minimums on dark backgrounds before implementation sign-off.

## Brand And Theming Baseline

### Brand principles

- Trustworthy and decision-grade (clean information hierarchy, strong legibility).
- Modern and intentional (layered surfaces, subtle depth, controlled motion).
- Data-centric (metrics and comparability emphasized over decorative chrome).

### Token model

Use three layers:

1. **Core tokens** (`--ref-*`)
   - Raw palette, spacing scale, radii, shadows, typography sizes/weights.
2. **Semantic tokens** (`--color-*`, `--space-*`, `--radius-*`)
   - Meaning-based aliases used by components (`surface`, `text-muted`, `accent`).
3. **Component tokens** (`--button-*`, `--card-*`, `--input-*`)
   - Optional per-component variables for tuning without breaking global semantics.

### Initial visual system baseline

- **Typography**
  - Display/headlines: `Space Grotesk`.
  - Body/UI: `Public Sans`.
  - Data-mono accents (codes/distances): `IBM Plex Mono`.
- **Color strategy**
  - Dark-first: deep navy/charcoal canvas with layered elevated surfaces for depth.
  - Light text on dark for primary readability; muted grey for secondary content.
  - One vivid primary brand accent (violet) plus one secondary signal accent (cyan/teal).
  - Explicit semantic states for info/success/warning/error, verified for AA contrast on dark surfaces.
  - Borders use translucent white (`rgba(255,255,255,0.06-0.12)`) for subtle dark-on-dark separation.
- **Spacing and rhythm**
  - 4px base spacing scale with concrete values: `4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80`.
  - Consistent content widths and gutter rules across breakpoints.
- **Depth and motion**
  - Subtle layered elevation and restrained transitions (`120-260ms`).
  - Motion must support comprehension, not decoration.

### Initial token seed values (v1)

- **Core color references - dark surface scale**
  - `--ref-color-navy-950: #060a13` (deepest background)
  - `--ref-color-navy-900: #0c1222` (canvas default)
  - `--ref-color-navy-800: #141d30` (surface / cards)
  - `--ref-color-navy-700: #1c2840` (elevated panels / hover states)
  - `--ref-color-navy-600: #263350` (active/pressed states)
- **Core color references - light text scale**
  - `--ref-color-grey-50: #f8fafc` (primary text)
  - `--ref-color-grey-200: #e2e8f0` (bright secondary)
  - `--ref-color-grey-400: #94a3b8` (muted/secondary text)
  - `--ref-color-grey-500: #64748b` (disabled/placeholder)
- **Core color references - brand and accent**
  - `--ref-color-brand-500: #8b5cf6` (violet - primary accent)
  - `--ref-color-brand-400: #a78bfa` (violet light - hover/focus)
  - `--ref-color-brand-600: #7c3aed` (violet deep - filled primary actions)
  - `--ref-color-accent-400: #22d3ee` (cyan - secondary signal)
  - `--ref-color-accent-500: #06b6d4` (cyan - secondary default)
- **Core color references - semantic states**
  - `--ref-color-success-500: #22c55e`
  - `--ref-color-warning-500: #f59e0b`
  - `--ref-color-danger-500: #ef4444`
  - `--ref-color-info-500: #3b82f6`
- **Core color references - border**
  - `--ref-color-border-subtle: rgba(255, 255, 255, 0.06)`
  - `--ref-color-border-default: rgba(255, 255, 255, 0.10)`
  - `--ref-color-border-strong: rgba(255, 255, 255, 0.16)`
- **Semantic defaults (dark theme - Phase 0 default)**
  - `--color-bg-canvas: var(--ref-color-navy-900)`
  - `--color-bg-surface: var(--ref-color-navy-800)`
  - `--color-bg-elevated: var(--ref-color-navy-700)`
  - `--color-text-primary: var(--ref-color-grey-50)`
  - `--color-text-secondary: var(--ref-color-grey-400)`
  - `--color-text-disabled: var(--ref-color-grey-500)`
  - `--color-border-default: var(--ref-color-border-default)`
  - `--color-border-subtle: var(--ref-color-border-subtle)`
  - `--color-action-primary: var(--ref-color-brand-500)`
  - `--color-action-primary-hover: var(--ref-color-brand-400)`
  - `--color-action-primary-solid: var(--ref-color-brand-600)`
  - `--color-action-primary-solid-hover: var(--ref-color-brand-500)`
  - `--color-action-secondary: var(--ref-color-accent-500)`
  - `--color-state-success: var(--ref-color-success-500)`
  - `--color-state-warning: var(--ref-color-warning-500)`
  - `--color-state-danger: var(--ref-color-danger-500)`
  - `--color-state-info: var(--ref-color-info-500)`

### Contrast verification requirements

Every token pairing below must meet WCAG 2.2 AA minimums before implementation:

| Foreground | Background | Required ratio | Use |
|---|---|---|---|
| `--color-text-primary` | `--color-bg-canvas` | >= 4.5:1 (normal text) | Body copy |
| `--color-text-primary` | `--color-bg-surface` | >= 4.5:1 | Card content |
| `--color-text-secondary` | `--color-bg-surface` | >= 4.5:1 | Secondary labels |
| `--color-text-secondary` | `--color-bg-canvas` | >= 4.5:1 | Muted canvas text |
| `--color-action-primary` | `--color-bg-surface` | >= 3:1 (UI components) | Buttons, links |
| `--color-action-primary-solid` on filled bg | white text | >= 4.5:1 | Primary button label |
| Semantic states | `--color-bg-surface` | >= 3:1 | Badges, icons |

## Evolution Strategy

- Keep component code bound to semantic/component tokens only; avoid raw hex usage outside token files.
- Support future visual refreshes by changing semantic mappings and typography tokens without refactoring feature components.
- Document token additions/deprecations in the same change as component updates to prevent theme drift.

## Styling Engine And Consumption Model

- Use Tailwind CSS with `tailwind.config.ts` mapped to semantic tokens (not hardcoded utility colors/spaces).
- Define tokens in `tokens.css` and semantic theme mappings in `theme.css`; import both at app entry.
- Components consume tokens through Tailwind theme keys and limited `var(--token)` escapes when needed.
- Avoid broad, page-level ad-hoc CSS. Any unavoidable custom CSS (for example map container edge cases) must still use semantic tokens.

## Map Integration On Dark Shell

- **Tile provider**: use CartoDB Dark Matter (`https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png`) as the default Leaflet tile layer. Free, no API key required, visually aligned with dark canvas.
- **Provider fallback**: define at least one approved fallback dark tile provider (for example Stadia/MapTiler dark styles, or self-hosted tiles) configurable via environment so the app can switch providers without code rewrites.
- **Provider governance**: verify attribution, usage limits, and terms of service before production; document the operational fallback decision in runbooks.
- **Markers**: replace default Leaflet blue pins with branded circle markers using `--ref-color-brand-500` (violet accent) fill and a subtle white or light stroke. Size: 10-14px radius for desktop, 14-18px for touch.
- **Map container**: flush integration - no visible border or inset. Use `--color-bg-surface` as fallback background while tiles load. Optional subtle inner shadow or translucent overlay at map edges to blend with panel chrome.
- **Controls**: restyle or hide default Leaflet zoom controls; if visible, style to match dark surface tokens.
- **Attribution**: keep required tile attribution but style text to `--color-text-disabled` so it doesn't dominate.

## Radix And shadcn Boundary

- Adopt shadcn-style local ownership: checked-in component source under `apps/web/src/components/ui/*`.
- Use only required Radix primitives for Phase 0-1 (for example `Select`, `Dialog`, `Popover`, `Tooltip`, `VisuallyHidden`) as needed by UI behavior.
- `Button`, `TextInput`, `Card`, `Field`, and layout primitives are local Civitas components, not raw Radix exports.
- Feature modules import only Civitas local components; direct imports from `@radix-ui/*` are disallowed outside shared UI internals.

## Required Reusable Component Baseline

Implement and use a minimum of these shared components before 0D2:

1. `AppShell`
2. `PageContainer`
3. `SplitPaneLayout` (list/map responsive behavior)
4. `Card` / `Panel`
5. `Button` (variants: primary, secondary, ghost)
6. `TextInput`
7. `Select`
8. `Field` (label, helper, error text)
9. `LoadingSkeleton`
10. `EmptyState`
11. `ErrorState`
12. `ResultCard` (school list item shell)
13. `MapPanel` wrapper (map chrome + loading boundary)

## Quality Rails (Mandatory)

### Accessibility

- Keyboard-accessible primary flow (search input, radius, submit, results, map popups).
- Visible focus states for all interactive controls.
- WCAG 2.2 AA contrast compliance for text and controls, verified against dark surface backgrounds using the contrast table in the token seed section.
- Automated accessibility smoke checks in component/feature tests.

### Responsiveness

- Supported breakpoints validated at minimum mobile, tablet, and desktop widths.
- Map/list layout adapts without overlap or hidden controls.
- Minimum interactive target size of 44x44 px for touch controls.

### Performance

- Map implementation loaded lazily to keep initial shell payload lean.
- Numeric budgets for Phase 0:
  - Initial app shell JavaScript (excluding lazy map chunk): <= 170 KB gzip.
  - Initial app shell CSS: <= 35 KB gzip.
  - Lazy map chunk (Leaflet + map wrapper): <= 260 KB gzip.
  - Lighthouse mobile profile (4G emulation) for search shell route: LCP <= 2.0s, CLS <= 0.10, TBT <= 200ms.
- Track bundle and render regressions using build artifacts plus Lighthouse snapshots captured before 0D2 sign-off.

### Code quality and reuse

- Type-safe API integration from backend OpenAPI types only.
- Shared components own control styling; feature code composes, not duplicates.
- Lint, typecheck, tests, and build pass at repo gates.

## File-Oriented Implementation Plan

1. `apps/web/package.json`
   - add required UI primitive and utility dependencies (`tailwindcss`, shadcn/Radix dependencies, class variance helpers as needed).
2. `apps/web/tailwind.config.ts`
   - map Tailwind theme keys to semantic token variables.
3. `apps/web/postcss.config.js`
   - wire Tailwind processing for Vite build.
4. `apps/web/src/styles/tokens.css`
   - core + semantic token definitions.
5. `apps/web/src/styles/theme.css`
   - typography, surface, and global theme application.
6. `apps/web/src/styles.css`
   - reduce to app entry imports and minimal global layout hooks.
7. `apps/web/src/components/layout/`
   - app shell and layout primitives.
8. `apps/web/src/components/ui/`
   - reusable base controls and state components (shadcn-style local ownership).
9. `apps/web/src/components/maps/MapPanel.tsx`
   - shared map container wrapper for lazy loading and consistent chrome.
10. `apps/web/src/shared/maps/map-tiles.ts` (with compatibility re-export in `apps/web/src/features/schools-search/config/map-tiles.ts`)
   - centralize tile URL/attribution config and primary/fallback provider selection.
11. `apps/web/src/test/`
   - add shared accessibility/responsiveness test utilities.
12. `apps/web/scripts/check-budgets.mjs` (or equivalent)
   - enforce JS/CSS/map chunk performance budgets in CI/local checks.
13. `.planning/phases/phase-0/0D-web-search-map.md`
   - align 0D2 implementation plan to consume foundations.

## Testing And Quality Gates

### Required web tests

- Component tests for each shared primitive/state component.
- Accessibility smoke tests for critical primitives and shell composition.
- Responsive layout assertions for map/list split behavior.
- Regression tests for token application on key controls/states.

### Required gates

- `make lint`
- `make test`
- `cd apps/web && npm run build`
- `cd apps/web && npm run budget:check`

## Acceptance Criteria

1. Tokenized theme foundation is implemented and used by shared components.
2. Required reusable component baseline is available and documented in-code by usage.
3. 0D2 can ship without introducing ad-hoc one-off control styling.
4. Accessibility, responsiveness, performance, and code-quality rails are active and passing.
5. Visual baseline reflects Civitas brand direction while remaining easy to evolve through token changes.
6. Styling engine, primitive ownership boundaries, and numeric performance budgets are implemented and verified.

## Risks And Mitigations

- **Risk**: over-design delays Phase 0 functional delivery.
  - **Mitigation**: keep 0D1 limited to shared foundations needed by 0D2 and Phase 1.
- **Risk**: template-inspired styling drifts into inconsistency.
  - **Mitigation**: enforce token-first styling and semantic component variants.
- **Risk**: map libraries inflate initial bundle size.
  - **Mitigation**: lazy-load map boundary and keep map interactions minimal in Phase 0.
- **Risk**: dark UI + map tile clash creates a jarring visual seam.
  - **Mitigation**: mandate dark tile provider (CartoDB Dark Matter); verify visual integration in both desktop and mobile layouts before 0D2 sign-off.
- **Risk**: external dark tile provider outages, policy changes, or usage-limit constraints impact map availability.
  - **Mitigation**: keep provider config centralized with a tested fallback provider and documented attribution/terms compliance checks before production release.
