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

## Visual Reference Points

Three production sites serve as design touchstones for the Civitas visual language. Each demonstrates a specific quality we aim to carry through the navigation shell and layout system:

| Reference | What we take from it |
|---|---|
| **[Vercel](https://vercel.com/)** | Restrained site chrome — ultra-thin header, no visual weight competing with content. Monochrome surfaces with a single accent colour. Typography does the heavy-lifting. |
| **[Linear](https://linear.app/)** | Dark-first palette where hierarchy comes from luminance steps, not colour variety. Subtle glassmorphism panels. Motion is purposeful and minimal. |
| **[The Refugee Project](https://www.therefugeeproject.org/)** | Map-as-canvas paradigm — the dark map *is* the background. Colour is reserved exclusively for data encoding (marker size/fill). UI overlays are semi-transparent so the spatial context reads through. |

These references inform a binding design principle:

> **Dark canvas, colour = data.** Background surfaces stay near-black. Every splash of chromatic colour must encode information (rating band, Ofsted category, selection state, trend direction). Decorative colour (ambient glows, tinted panels) is suppressed in map-first views so data owns the visual budget.

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
- **MapOverlayLayout**: a second layout variant (alongside `SplitPaneLayout`) where the map stretches to full viewport and UI panels float as glassmorphism overlays.
- Ambient-glow suppression mechanism so map-first views use the dark map tiles as background instead of the violet radial gradients.
- Chromeless `MapPanel` variant that renders without the panel header bar, allowing it to serve as a full-bleed background.

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
9. **Dark canvas, colour = data**: map-first views suppress ambient decoration (violet glow divs, tinted surfaces). The dark CartoDB tiles serve as the page background. Chromatic colour is reserved for data encoding — marker fill, selection rings, rating bands, trend indicators. Decorative uses of brand violet are limited to content pages (profile, about) and interactive UI chrome (buttons, links, focus rings).
10. **MapOverlayLayout**: introduced as a layout variant alongside `SplitPaneLayout`. The search route uses `MapOverlayLayout` by default; content routes (profile, 404) use standard `PageContainer` layout. The layout provides a `data-layout="map-overlay"` attribute on the root element so CSS can conditionally suppress ambient glows.
11. **Overlay panels use neutral glassmorphism**: panels floating over the map use `rgba(15, 15, 20, 0.85)` with `backdrop-filter: blur(16px)` — no violet tint — so they recede behind the data layer. This extends the existing `panel-surface` token with a `panel-surface-neutral` variant.
12. **Visual reference touchstones**: Vercel (restrained chrome), Linear (dark-first luminance hierarchy), The Refugee Project (map-as-canvas, colour = data). These inform all visual decisions in 1F and downstream deliverables.

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
16. `apps/web/src/components/layout/MapOverlayLayout.tsx` (new)
    - full-viewport map container with absolutely-positioned overlay panel slots (search panel, detail panel).
    - sets `data-layout="map-overlay"` on root for CSS-driven ambient-glow suppression.
    - accepts `children` for the overlay panel content and a `map` slot for the map component.
17. `apps/web/src/components/maps/MapPanelChromeless.tsx` (new)
    - variant of `MapPanel` that renders without the panel header bar and fixed-height constraint.
    - fills its parent container; intended for use inside `MapOverlayLayout`.
18. `apps/web/src/styles/tokens.css` (update)
    - add `--panel-surface-neutral` token (`rgba(15, 15, 20, 0.85)`) for map overlay panels.
19. `apps/web/src/styles/theme.css` (update)
    - add `[data-layout="map-overlay"] .ambient-glow { display: none; }` rule.
    - add `.panel-surface-neutral` utility class with neutral glassmorphism values.
20. `apps/web/src/components/layout/AppShell.tsx` (update)
    - ensure ambient-glow divs have the `.ambient-glow` class so they can be suppressed by layout context.

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
- MapOverlayLayout renders map at full viewport with overlay panel visible.
- MapOverlayLayout suppresses ambient-glow elements (not visible in DOM or hidden via CSS).
- MapPanelChromeless renders without header bar and fills parent container.
- `panel-surface-neutral` class applies correct glassmorphism values (no violet tint).

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
12. MapOverlayLayout renders the map as a full-viewport background with search panel as a glassmorphism overlay.
13. Ambient violet glow is suppressed in map-first layout; map tiles serve as the visual background.
14. Overlay panels use neutral glassmorphism (no violet tint) so colour budget is reserved for data.
15. Visual language is consistent with reference touchstones (Vercel, Linear, The Refugee Project).

## Risks And Mitigations

- Risk: route migration regresses existing search flow.
  - Mitigation: keep search feature unchanged and route-wrap it first.
- Risk: feature boundaries blur during route introduction.
  - Mitigation: enforce route/feature/api ownership per frontend conventions.
- Risk: header/footer add visual weight that competes with data content.
  - Mitigation: keep chrome minimal and low-contrast, consistent with dark-first token system; defer marketing/content-heavy navigation to post-MVP.
- Risk: mobile drawer adds bundle weight.
  - Mitigation: Radix Dialog is already a dependency for Select; Sheet reuses the same primitive with minimal incremental cost.
- Risk: MapOverlayLayout diverges visually from content pages, feeling like two different apps.
  - Mitigation: shared header/footer chrome, shared token system, and shared typography create continuity. Only the background treatment differs (map tiles vs ambient glow).
- Risk: neutral glassmorphism panels feel flat or clinical without the violet tint.
  - Mitigation: the data visualisation layer (coloured markers, rating bands) provides the chromatic richness. Panel borders use subtle `--color-border-primary` luminance steps for depth.
