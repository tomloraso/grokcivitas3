# Frontend Conventions

This page defines concrete conventions for `apps/web` so frontend features stay consistent and architecture boundaries remain enforceable.

## Scope

Applies to `apps/web/src/*` for all new frontend features.

## Frontend Layer Map

Use this ownership model as the app grows:

```text
src/
  app/                  # app shell, providers, route wiring
  pages/                # route-level composition only
  features/<feature>/   # feature UI, hooks, local state, feature mapping
  components/           # shared local UI/layout/map primitives (Phase 0 baseline)
  api/                  # HTTP clients, generated contracts, contract aliases
  shared/               # reusable UI primitives and pure utilities
```

If a feature starts in a flatter structure, new files should still follow these ownership rules and migrate toward this layout.

Phase 0D1 currently keeps shared primitives under `src/components/*` with local ownership (shadcn-style for UI primitives). Treat `components` as part of the shared layer for dependency direction purposes.

## Dependency Direction

1. `app` may import `pages`, `features`, `api`, and `shared`.
2. `pages` may import `features`, `api`, and `shared`.
3. `features` may import `components`, `api`, and `shared`.
4. `components` may import `shared` only.
5. `api` may import generated contract files and internal API helpers only.
6. `shared` must not import `app`, `pages`, `features`, `components`, or `api`.
6. Use explicit leaf imports; avoid barrel re-export chains.

## Contracts and Type Ownership

1. Backend OpenAPI remains the single source of truth for wire contracts.
2. Regenerate contract types after backend schema changes using:
   - `cd apps/web && npm run generate:types`
3. `src/api/types.ts` is the canonical frontend contract surface derived from `src/api/generated-types.ts`.
4. Do not hand-maintain duplicate API payload types when generated contracts already define them.
5. Feature/view-model types are allowed, but they must be mapped from API contract types at feature boundaries.

## Network Access Rules

1. Only modules under `src/api/*` should make HTTP/network calls.
2. UI components/pages/features must call typed API functions, not `fetch` directly.
3. Keep transport mapping close to the API boundary so the rest of the UI sees stable, app-friendly shapes.

## State and Business Rule Boundaries

1. Keep server state as close as possible to the feature that owns it.
2. Promote state to app-wide scope only when multiple distant branches need it.
3. Prefer derived state over duplicated stored state.
4. Business rules, entitlement checks, and decision logic remain backend-owned; frontend should render data and send intent.

## UI and Styling

1. Build mobile-first layouts by default.
2. Keep shared tokens and global primitives centralized (for example in global styles and shared UI components).
3. Keep feature-specific presentation and styles inside the owning feature.
4. Avoid repeating magic spacing/color values across unrelated components.

## Site Identity and Metadata

1. Product name, operator name, contact emails, and canonical public origin must come from shared site configuration, not scattered string literals.
2. Frontend routes should use `PageMeta` for browser-visible title/description management instead of mutating `document.title` directly.
3. Canonical URLs and structured-data absolute URLs should only render when a valid public origin is configured.
4. Static SEO assets such as `robots.txt`, `sitemap.xml`, and `site.webmanifest` should be generated from the same site configuration so launch details stay consistent.

## Metric Display Pattern (StatCard / BenchmarkSlot)

`StatCard` (`src/components/data/StatCard.tsx`) is the canonical component for displaying a single school metric. All new metric cards must use it.

**Key props:**
- `value` / `label` / `unit` — the metric's current value and display metadata
- `trend` — sparkline data points; drives the `TrendIndicator` below the value
- `benchmark?: BenchmarkSlot` — when provided, renders an inline `BenchmarkBlock` with proportional bar chart (sm+) or compact text rows (mobile)
- `description?: string` — plain-English explanation surfaced via an ⓘ toggle; pull from `metricCatalog.ts`

**`BenchmarkSlot` interface** (exported from StatCard):
- `schoolRaw / localRaw / nationalRaw` — raw numeric values for proportional bar widths
- `displayDecimals` — round raw values to this precision before computing bar widths (prevents mismatched bars from sub-display-precision differences)
- `isPercent` — when true, fixes the bar scale to 0–100 rather than dynamic max
- `localLabel` — local area name shown in the benchmark block (e.g. "Camden")
- `*ValueFormatted` / `*DeltaFormatted` — pre-formatted strings for display

**Building a benchmark lookup in a section component:**
```ts
const benchmarkLookup = new Map<string, BenchmarkMetricVM>(
  benchmarkDashboard?.sections.flatMap((s) => s.metrics.map((m) => [m.metricKey, m] as const)) ?? []
);
// at card-build time:
const bm = benchmarkLookup.get(metricKey);
<StatCard ... benchmark={bm ? toBenchmarkSlot(bm) : undefined} />
```

Established in Phase 7 (P2–P3). If the StatCard benchmark pattern is approved for Phase 9 (compare), apply the same `BenchmarkSlot` interface — do not invent a parallel pattern.

**Metric catalog:** `src/features/school-profile/metricCatalog.ts` is the single source for metric labels and `description` strings. Update it rather than hardcoding strings in section components.

## Testing Expectations

1. Unit test pure feature helpers/mappers.
2. Component test user-visible behavior with Testing Library.
3. Add/extend Playwright coverage for critical journeys as they ship.
4. Keep lint + typecheck green to enforce import and contract boundaries in CI.
