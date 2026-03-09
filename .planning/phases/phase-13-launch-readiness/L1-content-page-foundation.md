# L1 - Content Page Foundation

## Document Control

- Status: Planned
- Last updated: 2026-03-09
- Depends on:
  - `docs/architecture/frontend-conventions.md`
  - `.planning/phases/phase-5-ux-uplift/UX-4-typography-spacing-visual-hierarchy.md`
  - `.planning/phases/phase-5-ux-uplift/UX-6-navigation-site-chrome-refinement.md`

## Objective

Establish the shared layout, typography, and per-page meta infrastructure that all content pages (About, Privacy, Terms, Data Sources, etc.) use. This deliverable creates re-usable foundations — it does not create any user-facing pages itself.

## Scope

### In scope

- Shared `ContentPageLayout` component for long-form prose pages.
- Per-page `<title>` and `<meta name="description">` management using `react-helmet-async`.
- Route registration pattern for static content pages.
- Footer link wiring from placeholder `#` to real route paths.
- Prose typography styles that work in both dark and light themes.

### Out of scope

- Individual page content (delivered in L3 and L4).
- SEO infrastructure beyond page-level title and description (delivered in L2).
- Backend API changes — none required.

## Decisions

1. Use `react-helmet-async` for per-page document head management. It is the maintained fork of `react-helmet`, supports concurrent rendering, and does not require a build-time framework change.
2. Content pages use the existing `PageContainer` max-width constraint and site chrome (header + footer) but add prose-specific typography styling.
3. Content pages are standard React Router routes — no CMS, no MDX, no external content source. Page copy lives in component files or co-located constants.
4. All content page routes are defined in `paths.ts` so footer and header links use the same centralized path helpers.

## Frontend Design

### ContentPageLayout component

```text
ContentPageLayout
  props:
    title: string              — page heading (rendered as h1)
    metaTitle?: string         — document <title> override (defaults to "{title} | Civitas")
    metaDescription?: string   — <meta name="description"> content
    children: ReactNode        — page body content
```

Rendering:
- `<PageMeta>` component handles `<Helmet>` for title and description.
- `<PageContainer>` wraps content at the existing max-width.
- `<article>` element with prose typography class wraps children.
- `<h1>` rendered above the article body using the existing display typeface.

### Prose typography

Add a `prose` utility class (or Tailwind `@apply` group) that styles:
- paragraph spacing, line-height, and max line-width for readability
- heading hierarchy (h2, h3) with consistent scale and spacing
- list styling (ul, ol) with proper indentation
- link styling with brand colour and underline
- blockquote styling for callouts or disclaimers
- dark and light theme parity via semantic tokens

Do not adopt `@tailwindcss/typography` — the existing token system provides all the values needed, and the prose styles for Civitas content pages are narrow enough to define directly. This avoids a new dependency and keeps style ownership in the project.

### PageMeta component

```text
PageMeta
  props:
    title: string           — document <title>, appended with " | Civitas"
    description?: string    — <meta name="description">
```

Uses `react-helmet-async` under the hood. The `HelmetProvider` is registered at the app root alongside `ThemeProvider` and `AuthProvider`.

### Route registration

Add content page paths to `paths.ts`:

```text
about: "/about"
dataSources: "/data-sources"
contact: "/contact"
privacy: "/privacy"
terms: "/terms"
accessibility: "/accessibility"
```

Register route entries in `routes.tsx` using direct imports (content pages are small; no lazy loading needed).

### Footer link wiring

Replace the current `FOOTER_LINKS` array in `SiteFooter.tsx`:
- Change `href: "#"` entries to `to` links using `paths.about`, `paths.contact`, `paths.privacy`.
- Switch from `<a>` to `<Link>` for internal routes.
- Add Terms and Accessibility links to the footer.

## File-Oriented Implementation Plan

1. `apps/web/package.json`
   - Add `react-helmet-async` dependency.

2. `apps/web/src/App.tsx`
   - Wrap router with `HelmetProvider` from `react-helmet-async`.

3. `apps/web/src/components/layout/PageMeta.tsx` (new)
   - Thin wrapper around `<Helmet>` for title and description.

4. `apps/web/src/components/layout/ContentPageLayout.tsx` (new)
   - Shared prose page layout with `PageMeta`, `PageContainer`, heading, and article wrapper.

5. `apps/web/src/styles/prose.css` (new)
   - Prose typography styles using existing semantic tokens.
   - Imported in `styles.css`.

6. `apps/web/src/shared/routing/paths.ts`
   - Add content page path entries.

7. `apps/web/src/components/layout/SiteFooter.tsx`
   - Replace placeholder `#` links with `<Link>` to real paths.
   - Add Terms and Accessibility links.

8. `apps/web/src/app/routes.tsx`
   - Add route entries for content pages (actual page components created in L3 and L4; use placeholder components until then).

9. `apps/web/src/components/layout/content-page.test.tsx` (new)
   - Test `ContentPageLayout` renders heading, meta tags, and prose wrapper.
   - Test `PageMeta` sets document title.

10. `apps/web/src/components/layout/site-footer.test.tsx`
    - Assert footer links resolve to real paths, not `#`.

## Testing And Quality Gates

### Required tests

- `ContentPageLayout` renders `<h1>` with provided title.
- `PageMeta` sets document `<title>` to `"{title} | Civitas"`.
- Footer links use `<Link>` with paths from `paths.ts`.
- Prose styles render legibly in dark and light themes (visual check).

### Quality gate

- `make lint` passes.
- `make test` passes.
- `cd apps/web && npm run build` passes.
- No layout regression on existing routes (search, profile, compare).

## Acceptance Criteria

- A shared content page layout exists and can render any long-form page.
- Every route has a meaningful document `<title>`.
- Footer links navigate to real routes (placeholder page components are acceptable at this stage).
- Prose typography is readable in both themes at mobile and desktop widths.

## Rollback

Per-file: `git checkout -- <file>`
