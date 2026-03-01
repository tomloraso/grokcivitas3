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

## Testing Expectations

1. Unit test pure feature helpers/mappers.
2. Component test user-visible behavior with Testing Library.
3. Add/extend Playwright coverage for critical journeys as they ship.
4. Keep lint + typecheck green to enforce import and contract boundaries in CI.
