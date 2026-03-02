# Phase 1F1 Design - Web Component Expansion And Data Visualization Baseline

## Document Control

- Status: Draft
- Last updated: 2026-03-02
- Depends on:
  - `.planning/phases/phase-0/0D1-web-foundations.md`
  - `.planning/phases/phase-1/1F-web-routing-navigation-foundation.md`
  - `.planning/phases/phase-1/1D-school-profile-api.md`
  - `.planning/phases/phase-1/1E-school-trends-api.md`
  - `docs/architecture/frontend-conventions.md`

## Objective

Expand the shared component library and establish the data visualization primitives needed by Phase 1 feature pages (school profiles, trends). This is the Phase 1 equivalent of 0D1: a foundations deliverable that ensures 1G can ship using shared, tested, token-integrated primitives rather than ad-hoc one-off implementations.

## Context

Phase 0D1 established the token system, layout primitives, and form controls. Phase 0D2 composed a feature (search/map) using those primitives. The same pattern applies here:

- **1F** provides routing, navigation shell, and site chrome.
- **1F1** (this deliverable) provides the expanded component library and data visualization baseline.
- **1G** composes the profile page feature using primitives from 0D1 + 1F + 1F1.

Without this step, 1G would either build these primitives inline (violating composition rules) or 1G's scope would be misleadingly large.

## Scope

### In scope

- Expand shared UI primitives (shadcn/ui-sourced, restyled to Civitas tokens, locally owned).
- Establish bespoke Civitas stat/metric component family for data-forward presentation.
- Install and configure chart/visualization baseline for trend rendering.
- All new components tested, accessible, token-integrated, and responsive.

### Out of scope

- Feature-specific page composition (owned by 1G).
- Full chart library deep integration beyond sparklines and basic trend lines.
- Complex animation or motion choreography.
- Components not needed until Phase 2+ (for example `Accordion`, `Pagination`, full data `Table`).

## Decisions

1. **Component sourcing strategy**: use shadcn/ui as a parts catalog. Each component is copied into `src/components/ui/` under local ownership, restyled to Civitas tokens. This follows the identical pattern established in 0D1 with `Button`, `Card`, `Select`, etc.
2. **Chart library**: adopt shadcn/ui Charts (Recharts-based) for standard chart types. For simple sparklines, hand-rolled SVG is acceptable to keep the bundle lean. The decision between Recharts sparkline and SVG sparkline is an implementation choice, not a design constraint.
3. **Bespoke metric components**: `StatCard`, `TrendIndicator`, and `RatingBadge` are Civitas-specific and do not exist in any UI kit. These are small compositions of existing tokens and primitives (each ~15-40 lines). They carry the product's visual identity for data presentation.
4. **Ownership boundary**: all new shared components live under `src/components/ui/` or `src/components/data/`. Feature code in `src/features/school-profile/` composes these but does not duplicate or redefine them.
5. **Phase scope limit**: only add components that 1G actually needs. Do not speculatively build Phase 2-3 components.

## Component Inventory

### Expanded Shared UI Primitives (shadcn/ui sourced)

| Component | Purpose | Phase 1 Consumer |
|---|---|---|
| `Badge` | Colored label/tag for categorical indicators | Ofsted rating, school phase, risk flags |
| `Tabs` | Section switcher for profile content areas | Profile page sections (demographics, Ofsted, trends) |
| `Tooltip` | Contextual help on hover/focus for metric explanations | Metric labels, data caveats, abbreviation definitions |
| `Toast` | Non-blocking notification feedback | Search feedback, error recovery, future actions |

Each follows the existing pattern:
- Radix primitive for accessibility behavior.
- CVA for variant control.
- Tailwind + semantic tokens for styling.
- Local ownership under `src/components/ui/`.
- Component test with accessibility smoke.

### Bespoke Civitas Data Components

| Component | Purpose | Complexity |
|---|---|---|
| `StatCard` | KPI display: big number + label + optional trend delta | ~25 lines, composes `Card` + tokens |
| `TrendIndicator` | Directional arrow + percentage/value delta + semantic color (up=green, down=red, stable=neutral) | ~15 lines, composes icon + tokens |
| `RatingBadge` | Maps Ofsted rating (or similar categorical rating) to a color-coded badge with accessible label | ~20 lines, composes `Badge` + rating-to-color mapping |
| `Sparkline` | Tiny inline SVG trend line for 3-5 year metric history | ~30-40 lines (hand-rolled SVG) or Recharts `<ResponsiveContainer>` |
| `MetricGrid` | CSS Grid layout wrapper for arranging stat cards in responsive columns | ~10 lines, pure layout |
| `MetricUnavailable` | Explicit "data not available" placeholder for unsupported metrics. Prevents silent omission | ~10 lines, composes `EmptyState` pattern |

These live under `src/components/data/` to distinguish data presentation components from generic UI primitives.

### Chart Baseline

| Deliverable | Approach |
|---|---|
| Install Recharts (or shadcn/ui Charts wrapper) | `package.json` dependency |
| Configure chart theme tokens | Map Recharts colors/grid/tooltip styles to Civitas semantic tokens |
| Verify lazy-loading strategy | Charts should not inflate the initial shell bundle; lazy-load if needed |
| Basic Sparkline implementation | Either SVG hand-rolled or Recharts `<LineChart>` in minimal config |

## File-Oriented Implementation Plan

### Dependencies

1. `apps/web/package.json`
   - add `recharts` (or equivalent chart library).
   - add Radix primitives if not already present for new components (`@radix-ui/react-tabs`, `@radix-ui/react-tooltip`, `@radix-ui/react-toast`).

### Expanded UI Primitives

2. `apps/web/src/components/ui/Badge.tsx` (new)
   - variants: `default`, `success`, `warning`, `danger`, `info`, `outline`.
3. `apps/web/src/components/ui/Tabs.tsx` (new)
   - `Tabs`, `TabsList`, `TabsTrigger`, `TabsContent` compound component.
4. `apps/web/src/components/ui/Tooltip.tsx` (new)
   - `TooltipProvider`, `Tooltip`, `TooltipTrigger`, `TooltipContent`.
5. `apps/web/src/components/ui/Toast.tsx` (new)
   - toast notification with auto-dismiss and manual close.

### Data Components

6. `apps/web/src/components/data/StatCard.tsx` (new)
   - label, value, optional delta, optional trend direction.
7. `apps/web/src/components/data/TrendIndicator.tsx` (new)
   - arrow icon (Lucide `TrendingUp`/`TrendingDown`/`Minus`), delta value, semantic color.
8. `apps/web/src/components/data/RatingBadge.tsx` (new)
   - rating string -> color-coded Badge with accessible label.
9. `apps/web/src/components/data/Sparkline.tsx` (new)
   - accepts `data: number[]`, renders minimal trend line.
10. `apps/web/src/components/data/MetricGrid.tsx` (new)
    - responsive CSS Grid wrapper for stat card layout.
11. `apps/web/src/components/data/MetricUnavailable.tsx` (new)
    - placeholder for unsupported/missing metric.

### Chart Configuration

12. `apps/web/src/shared/charts/chart-theme.ts` (new)
    - map Recharts colors, grid, and tooltip styles to Civitas tokens.

### Tests

13. `apps/web/src/components/ui/ui-expansion.test.tsx` (new)
    - component tests for Badge, Tabs, Tooltip, Toast.
    - accessibility smoke for each.
14. `apps/web/src/components/data/data-components.test.tsx` (new)
    - component tests for StatCard, TrendIndicator, RatingBadge, Sparkline, MetricGrid, MetricUnavailable.
    - variant and edge-case coverage (negative deltas, zero deltas, single-point sparkline, unknown ratings).
    - accessibility smoke.

## Testing And Quality Gates

### Required tests

- Badge renders all variants with correct semantic colors.
- Tabs switch content panels and maintain keyboard accessibility.
- Tooltip appears on hover/focus with correct content.
- Toast renders and auto-dismisses.
- StatCard renders label, value, and optional trend delta.
- TrendIndicator renders correct arrow direction and color for positive, negative, and zero deltas.
- RatingBadge maps known ratings to correct colors and renders accessible labels.
- Sparkline renders with multi-point data, single-point data, and empty data.
- MetricGrid renders children in responsive grid.
- MetricUnavailable renders explicit "not available" state.
- Accessibility smoke (axe) for all new components.

### Required gates

- `cd apps/web && npm run lint`
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run test`
- `cd apps/web && npm run build`
- `cd apps/web && npm run budget:check`
- `make lint`
- `make test`

## Acceptance Criteria

1. Expanded UI primitives (Badge, Tabs, Tooltip, Toast) are implemented, token-integrated, and tested under shared ownership.
2. Data component family (StatCard, TrendIndicator, RatingBadge, Sparkline, MetricGrid, MetricUnavailable) is implemented and tested.
3. Chart library is installed and theme-configured to use Civitas tokens.
4. All new components follow the same ownership pattern as Phase 0D1 primitives (local source, CVA variants, Tailwind + tokens, Radix for accessibility).
5. 1G can be implemented by composing from 0D1 + 1F + 1F1 shared components without introducing ad-hoc one-off primitives.
6. Performance budgets still pass with new dependencies added.
7. All quality gates pass.

## Risks And Mitigations

- Risk: chart library inflates bundle size beyond performance budgets.
  - Mitigation: lazy-load chart components if needed; verify budget gates after installation. For sparklines, hand-rolled SVG keeps bundle minimal.
- Risk: over-building components not needed by 1G.
  - Mitigation: scope is explicitly limited to components 1G consumes. Phase 2+ components are deferred.
- Risk: data component design decisions are premature without seeing real profile data.
  - Mitigation: components accept generic props (label, value, delta, data array). Design mapping from API contract to component props happens in 1G feature mappers.
- Risk: Recharts theming doesn't integrate cleanly with CSS custom property tokens.
  - Mitigation: define a `chart-theme.ts` that resolves token values for Recharts config; document any limitations.
