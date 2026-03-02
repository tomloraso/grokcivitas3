# Phase 1F Design - Web Routing, Navigation Shell, And Site Chrome

## Document Control

- Status: Draft
- Last updated: 2026-03-02
- Depends on:
  - `.planning/phases/phase-0/0D-web-search-map.md`
  - `.planning/phases/phase-0/0D1-web-foundations.md`
  - `.planning/phases/phase-1/1D-school-profile-api.md`
  - `docs/architecture/frontend-conventions.md`

## Objective

Move the web app from single-feature mount to route-based composition and add the persistent site chrome (header, footer, navigation, accessibility affordances) that every multi-page product requires. This ensures search and profile experiences can evolve independently and that the app presents as a cohesive website rather than an isolated feature demo.

## Context

Phase 0D1 established the tokenized visual system and reusable component primitives. Phase 0D2 composed the first feature using those primitives. This deliverable follows the same pattern: it provides the structural website shell that all subsequent pages and features render within.

## Scope

### In scope

- Introduce route shell for:
  - `/` (search)
  - `/schools/:urn` (profile)
  - `*` (404 not-found)
- Add persistent site header with:
  - Civitas logo/brand mark.
  - Primary navigation links.
  - Mobile-responsive navigation (hamburger -> drawer/slide-over).
- Add persistent site footer with:
  - Legal/about/contact links.
  - Copyright notice.
  - Appropriate spacing and visual separation from page content.
- Add skip-to-content link for keyboard/screen-reader accessibility.
- Add breadcrumb navigation pattern for drill-down flows (search -> school profile).
- Install icon library (Lucide React) used by navigation, breadcrumbs, and future UI.
- Add search-result navigation to profile route.
- Preserve existing Phase 0 search behavior on the `/` route.
- Add shared loading and not-found route behavior.

### Out of scope

- Full visual implementation of profile page (`1G`).
- Auth/paywall route guards (Phase 4).
- Marketing/landing page (post-MVP).
- Cookie/consent banner (deferred to pre-launch hardening).

## Decisions

1. Adopt route-level composition now to prevent Phase 1 UI growth inside `App.tsx`.
2. Keep search feature ownership under `features/schools-search`.
3. Introduce new profile feature ownership under `features/school-profile`.
4. All network IO remains in `src/api/*`; routes/features call typed API clients only.
5. **Icon library**: adopt Lucide React (tree-shakeable, consistent with shadcn ecosystem, covers navigation/action/indicator needs). Define a thin sizing/color convention but no mandatory wrapper component.
6. **Site header and footer are shared layout components**, owned under `src/components/layout/` consistent with `AppShell`, `PageContainer`, and `SplitPaneLayout`.
7. **Mobile navigation**: use shadcn/ui Sheet (Radix Dialog-based) for the mobile drawer. Follows existing Radix ownership boundary (wrapped as local component, raw Radix not exposed to features).
8. **Breadcrumbs**: implemented as a shared layout component; each page/route supplies breadcrumb segments declaratively.

## UX And Navigation Contract

1. User can navigate from a result card to `/schools/{urn}`.
2. Browser back returns to prior search route state.
3. Missing URN route state renders deterministic not-found UI (branded 404 page using shared primitives).
4. Route transitions preserve accessibility focus behavior.
5. Site header is visible on all routes and provides a consistent way to return to search.
6. Footer is visible on all routes below page content.
7. Skip-to-content link is the first focusable element when tabbing into the page.
8. Breadcrumbs on profile route show: Home -> School Name.

## File-Oriented Implementation Plan

1. `apps/web/package.json`
   - add router dependency (`react-router-dom`).
   - add icon library (`lucide-react`).
   - add Sheet/Drawer dependency (Radix Dialog if not already present, or shadcn/ui Sheet pattern).
2. `apps/web/src/app/routes.tsx` (new)
   - define route tree and element composition.
3. `apps/web/src/app/AppRouter.tsx` (new)
   - mount router provider.
4. `apps/web/src/app/RootLayout.tsx` (new)
   - compose `SiteHeader` + `<Outlet>` + `SiteFooter` + `SkipToContent` as the persistent shell.
5. `apps/web/src/App.tsx`
   - replace direct feature mount with router entry.
6. `apps/web/src/components/layout/SiteHeader.tsx` (new)
   - logo/brand mark, primary nav links, mobile hamburger trigger.
7. `apps/web/src/components/layout/MobileNav.tsx` (new)
   - slide-over drawer using Sheet/Dialog primitive, nav links, close behavior.
8. `apps/web/src/components/layout/SiteFooter.tsx` (new)
   - footer links, copyright, styled to token system.
9. `apps/web/src/components/layout/Breadcrumbs.tsx` (new)
   - shared breadcrumb component consuming route-provided segments.
10. `apps/web/src/components/layout/SkipToContent.tsx` (new)
    - visually hidden link that becomes visible on focus, jumps to `#main-content`.
11. `apps/web/src/components/ui/Sheet.tsx` (new)
    - shadcn/ui-style local Sheet component wrapping Radix Dialog for mobile nav.
12. `apps/web/src/pages/NotFoundPage.tsx` (new)
    - branded 404 page using shared `EmptyState` primitive with navigation back to search.
13. `apps/web/src/features/schools-search/components/SchoolsList.tsx`
    - add profile link action per school result.
14. `apps/web/src/components/ui/ResultCard.tsx`
    - support navigation affordance while keeping shared ownership boundaries.
15. `apps/web/src/shared/routing/` (new optional)
    - route helpers for profile path construction.

## Testing And Quality Gates

### Required tests

- Route renders search feature on `/`.
- Route renders profile shell on `/schools/:urn`.
- Catch-all route renders 404 page for unknown paths.
- Search result card link points to expected profile path.
- Back navigation behavior smoke coverage.
- Site header renders and is visible on all routes.
- Site footer renders and is visible on all routes.
- Mobile navigation drawer opens/closes and contains expected links.
- Skip-to-content link is first focusable element and targets `#main-content`.
- Breadcrumbs render correct segments on profile route.
- Accessibility smoke (axe) for header, footer, and navigation components.

### E2E updates

- Extend `apps/web/e2e/schools-search.spec.ts` (or add route spec) with:
  - click result -> profile route visible.
  - header navigation back to search route.
  - 404 route renders not-found page.

### Required gates

- `cd apps/web && npm run lint`
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run test`
- `cd apps/web && npm run build`
- `cd apps/web && npm run budget:check`
- `make lint`
- `make test`

## Acceptance Criteria

1. Search route and profile route are independently addressable.
2. Navigation from search to profile is wired and test-covered.
3. Site header with logo and navigation is visible on all routes.
4. Site footer is visible on all routes.
5. Mobile navigation adapts to small viewports with drawer/slide-over pattern.
6. Skip-to-content link is present and functional.
7. Breadcrumbs provide wayfinding on drill-down routes.
8. 404 page renders for unknown routes using shared primitives.
9. Icon library is installed and available for use by 1F1 and 1G.
10. Route architecture follows frontend ownership and dependency conventions.
11. Existing Phase 0 search behavior remains intact.

## Risks And Mitigations

- Risk: route migration regresses existing search flow.
  - Mitigation: keep search feature unchanged and route-wrap it first.
- Risk: feature boundaries blur during route introduction.
  - Mitigation: enforce route/feature/api ownership per frontend conventions.
- Risk: header/footer add visual weight that competes with data content.
  - Mitigation: keep chrome minimal and low-contrast, consistent with dark-first token system; defer marketing/content-heavy navigation to post-MVP.
- Risk: mobile drawer adds bundle weight.
  - Mitigation: Radix Dialog is already a dependency for Select; Sheet reuses the same primitive with minimal incremental cost.
