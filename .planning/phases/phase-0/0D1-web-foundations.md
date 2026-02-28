# Phase 0D1 Design - Web Foundations And Brand Baseline

## Document Control

- Status: Draft
- Last updated: 2026-02-28
- Depends on:
  - `.planning/project-brief.md`
  - `.planning/phases/phase-0/0C-postcode-search-api.md`
  - `docs/architecture/principles.md`
  - `docs/architecture/testing-strategy.md`

## Objective

Establish production-grade frontend foundations before 0D2 implementation so the first user-facing search/map slice is polished, accessible, performant, and easy to evolve over time.

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

### Out of scope

- Full marketing template rollout.
- Complete multi-theme runtime switching (token model should support future addition).
- Advanced animation choreography beyond lightweight transitions.
- Phase 1+ feature-specific domain UI (profiles, comparisons, paywall flows).

## Decisions

1. **Visual direction**: use a data-forward, high-contrast, modern "civic intelligence" style rather than generic template aesthetics.
2. **Token-first architecture**: all visual styling flows through design tokens and semantic aliases.
3. **Primitive strategy**: use Radix primitives, wrapped by local components; feature code must not depend on raw primitive APIs directly.
4. **Reference usage strategy**: references are inspiration for interaction and composition, not direct cloning.
5. **Quality as release gate**: accessibility, responsiveness, and performance checks are mandatory acceptance criteria before 0D2 closeout.

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
  - Neutral surfaces with strong contrast for readability.
  - One primary brand accent plus one secondary signal accent.
  - Explicit semantic states for info/success/warning/error.
- **Spacing and rhythm**
  - 4px base spacing scale.
  - Consistent content widths and gutter rules across breakpoints.
- **Depth and motion**
  - Subtle layered elevation and restrained transitions (`120-260ms`).
  - Motion must support comprehension, not decoration.

### Initial token seed values (v1)

- **Core color references**
  - `--ref-color-slate-950: #0b1220`
  - `--ref-color-slate-900: #111827`
  - `--ref-color-slate-700: #334155`
  - `--ref-color-slate-100: #e2e8f0`
  - `--ref-color-slate-50: #f8fafc`
  - `--ref-color-brand-700: #0f766e`
  - `--ref-color-brand-500: #14b8a6`
  - `--ref-color-accent-600: #2563eb`
  - `--ref-color-success-600: #15803d`
  - `--ref-color-warning-600: #d97706`
  - `--ref-color-danger-600: #dc2626`
- **Semantic defaults (light theme)**
  - `--color-bg-canvas: var(--ref-color-slate-50)`
  - `--color-bg-surface: #ffffff`
  - `--color-text-primary: var(--ref-color-slate-950)`
  - `--color-text-secondary: var(--ref-color-slate-700)`
  - `--color-border-default: var(--ref-color-slate-100)`
  - `--color-action-primary: var(--ref-color-brand-700)`
  - `--color-action-secondary: var(--ref-color-accent-600)`
  - `--color-state-success|warning|danger`: mapped to semantic state references above.

## Evolution Strategy

- Keep component code bound to semantic/component tokens only; avoid raw hex usage outside token files.
- Support future visual refreshes by changing semantic mappings and typography tokens without refactoring feature components.
- Document token additions/deprecations in the same change as component updates to prevent theme drift.

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
- WCAG 2.2 AA contrast compliance for text and controls.
- Automated accessibility smoke checks in component/feature tests.

### Responsiveness

- Supported breakpoints validated at minimum mobile, tablet, and desktop widths.
- Map/list layout adapts without overlap or hidden controls.
- Minimum interactive target size of 44x44 px for touch controls.

### Performance

- Map implementation loaded lazily to keep initial shell payload lean.
- Search shell remains interactive quickly on mid-range mobile devices.
- Track bundle and render regressions during Phase 0 using build output and Lighthouse snapshots.

### Code quality and reuse

- Type-safe API integration from backend OpenAPI types only.
- Shared components own control styling; feature code composes, not duplicates.
- Lint, typecheck, tests, and build pass at repo gates.

## File-Oriented Implementation Plan

1. `apps/web/package.json`
   - add required UI primitive and utility dependencies.
2. `apps/web/src/styles/tokens.css`
   - core + semantic token definitions.
3. `apps/web/src/styles/theme.css`
   - typography, surface, and global theme application.
4. `apps/web/src/styles.css`
   - reduce to app entry imports and minimal global layout hooks.
5. `apps/web/src/components/layout/`
   - app shell and layout primitives.
6. `apps/web/src/components/ui/`
   - reusable base controls and state components.
7. `apps/web/src/components/maps/MapPanel.tsx`
   - shared map container wrapper for lazy loading and consistent chrome.
8. `apps/web/src/test/`
   - add shared accessibility/responsiveness test utilities.
9. `.planning/phases/phase-0/0D-web-search-map.md`
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

## Acceptance Criteria

1. Tokenized theme foundation is implemented and used by shared components.
2. Required reusable component baseline is available and documented in-code by usage.
3. 0D2 can ship without introducing ad-hoc one-off control styling.
4. Accessibility, responsiveness, performance, and code-quality rails are active and passing.
5. Visual baseline reflects Civitas brand direction while remaining easy to evolve through token changes.

## Risks And Mitigations

- **Risk**: over-design delays Phase 0 functional delivery.
  - **Mitigation**: keep 0D1 limited to shared foundations needed by 0D2 and Phase 1.
- **Risk**: template-inspired styling drifts into inconsistency.
  - **Mitigation**: enforce token-first styling and semantic component variants.
- **Risk**: map libraries inflate initial bundle size.
  - **Mitigation**: lazy-load map boundary and keep map interactions minimal in Phase 0.
