# L2 - SEO And Discoverability Infrastructure

## Document Control

- Status: Implemented
- Last updated: 2026-03-11
- Depends on:
  - `L1-content-page-foundation.md` (PageMeta component and react-helmet-async provider)
  - `docs/architecture/frontend-conventions.md`

## Objective

Deliver the baseline SEO infrastructure that the current Vite SPA can support without a rendering architecture change. This slice focuses on browser-visible titles and descriptions, canonical URLs, crawler entry points for launch-managed static routes, JSON-LD on school profile pages, and site-wide sharing fallbacks in `index.html`.

## Scope

### In scope

- `robots.txt` allowing crawl of public routes.
- Static `sitemap.xml` listing launch-managed public routes only.
- Favicon set (SVG plus PNG fallbacks) and web manifest for mobile add-to-home-screen.
- Site-wide fallback meta description, Open Graph, Twitter Card tags, and default share image in `index.html`.
- Client-rendered `<title>`, `<meta name="description">`, and canonical tags via `PageMeta`.
- Dynamic browser-visible title, description, and canonical tags on school profile pages.
- JSON-LD `School` structured data on school profile pages.

### Out of scope

- Reliable route-specific social share cards for dynamic SPA routes. This requires SSR, prerendering, or equivalent HTML injection.
- School-profile URL enumeration in the sitemap or crawler-scale school-profile discoverability. This requires a generated school index and sitemap process.
- Location-based SEO pages (Phase 12 / `11A-seo-location-pages.md`).
- Server-side rendering or prerendering. The current Vite SPA architecture is retained in this phase.
- Dynamic sitemap generation from the database or pipeline outputs.
- Page speed or Core Web Vitals optimization beyond what is already in `.planning/phases/phase-5-ux-uplift/`.

## Decisions

1. **Static sitemap covers launch-managed static routes only.** It intentionally omits school profile URLs because XML sitemaps require concrete URLs and this phase does not add a build-time or server-side school index.
2. **`index.html` carries site-wide share fallbacks.** Route-level `PageMeta` remains useful for browser UX and JS-capable crawlers, but launch sign-off does not depend on social debuggers for dynamic routes.
3. **SVG-first favicon.** Ship a single `favicon.svg` with `<link rel="icon">` fallbacks to `favicon-32x32.png` and `favicon-16x16.png` for older browsers. Include `apple-touch-icon.png` (180x180).
4. **Structured data uses Schema.org `School` type.** Properties: `name`, `identifier` (URN), `address` (from GIAS), and `url` (canonical). Extended properties such as `aggregateRating` are not included because Civitas does not assign ratings.
5. **Canonical base URL comes from configuration.** `PageMeta` reads the site origin from `VITE_PUBLIC_URL`, which is documented in `apps/web/.env.example`.
6. **No fake production domain.** If `VITE_PUBLIC_URL` is unset because the production domain is not yet fixed, canonical tags are omitted, `robots.txt` disallows crawling, and `sitemap.xml` emits no public URLs.

## Frontend Design

### `robots.txt`

```text
User-agent: *
Allow: /

Sitemap: https://civitas.uk/sitemap.xml
```

Served from generated build output. The production domain is used in the Sitemap directive only when `VITE_PUBLIC_URL` is configured. When it is unset, the generated file disallows crawling.

### `sitemap.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://civitas.uk/</loc></url>
  <url><loc>https://civitas.uk/about</loc></url>
  <url><loc>https://civitas.uk/data-sources</loc></url>
  <url><loc>https://civitas.uk/contact</loc></url>
  <url><loc>https://civitas.uk/privacy</loc></url>
  <url><loc>https://civitas.uk/terms</loc></url>
  <url><loc>https://civitas.uk/accessibility</loc></url>
</urlset>
```

Served from generated build output. School profile URLs are intentionally omitted from the launch sitemap. When `VITE_PUBLIC_URL` is unset, the file remains valid XML but contains no public URLs.

### Favicon and web manifest

Brand-neutral image assets are placed in `apps/web/public/`, while `site.webmanifest` is generated from shared site configuration:

| File | Purpose |
|---|---|
| `favicon.svg` | Modern browsers, scalable icon |
| `favicon-32x32.png` | Legacy fallback 32px |
| `favicon-16x16.png` | Legacy fallback 16px |
| `apple-touch-icon.png` | iOS home-screen icon (180x180) |
| `site.webmanifest` | PWA manifest - name, short_name, icons, theme_color, background_color |
| `og-default.png` | Default Open Graph share image (1200x630) |

`index.html` additions:

```html
<link rel="icon" type="image/svg+xml" href="/favicon.svg" />
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png" />
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
<link rel="manifest" href="/site.webmanifest" />
<meta
  name="description"
  content="Civitas - independent school research for England. Demographics, trends, Ofsted, and area context."
/>
<meta property="og:title" content="Civitas" />
<meta
  property="og:description"
  content="Independent school research for England. Demographics, trends, Ofsted, and area context."
/>
<meta property="og:image" content="/og-default.png" />
<meta property="og:type" content="website" />
<meta property="og:url" content="https://civitas.uk/" />
<meta name="twitter:card" content="summary_large_image" />
```

These tags remain generic for launch. Reliable route-specific social cards are deferred until a rendering strategy change lands.

### `PageMeta` extension for canonical URLs

Extend the `PageMeta` component from L1 to accept:

```text
PageMeta
  props:
    title: string
    description?: string
    canonicalPath?: string   - path segment, e.g. "/about"
```

The component renders:

- `<title>{title} | Civitas</title>`
- `<meta name="description" content="{description}" />`
- `<link rel="canonical" href="{VITE_PUBLIC_URL}{canonicalPath}" />`

The canonical base URL is read from an environment variable (`VITE_PUBLIC_URL`) so development and production diverge cleanly.

### School profile dynamic metadata

On the school profile route (`/schools/:urn`), `PageMeta` receives:

- `title`: School name (for example, `Oakwood Academy`)
- `description`: `{School name} - {type of establishment}, {phase}, Ofsted: {rating}. View demographics, trends, and area context on Civitas.`
- `canonicalPath`: `/schools/{urn}`

These values are derived from the profile API response that is already fetched on this route.

### JSON-LD structured data

A `SchoolJsonLd` component renders a `<script type="application/ld+json">` block on school profile pages:

```json
{
  "@context": "https://schema.org",
  "@type": "School",
  "name": "Oakwood Academy",
  "identifier": "123456",
  "url": "https://civitas.uk/schools/123456",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "...",
    "addressLocality": "...",
    "postalCode": "...",
    "addressCountry": "GB"
  }
}
```

Properties are derived from the GIAS data already in the profile API response.

## File-Oriented Implementation Plan

1. `apps/web/public/` (new directory)
   - Create with `robots.txt`, `sitemap.xml`, and `site.webmanifest`.
   - Add favicon files and `og-default.png` (placeholder asset until branding is finalised).

2. `apps/web/index.html`
   - Add favicon, apple-touch-icon, and manifest `<link>` elements.
   - Add fallback meta description plus generic Open Graph and Twitter Card tags.

3. `apps/web/.env.example`
   - Add `VITE_PUBLIC_URL` with a production example and a short comment describing its use for canonical URLs.

4. `apps/web/src/components/layout/PageMeta.tsx`
   - Extend with `canonicalPath` support while retaining title and description handling from L1.

5. `apps/web/src/components/seo/SchoolJsonLd.tsx` (new)
   - Render JSON-LD `School` structured data from profile data props.

6. `apps/web/src/features/school-profile/SchoolProfileFeature.tsx`
   - Wire `PageMeta` with dynamic title, description, and canonical path from API data.
   - Render `SchoolJsonLd` alongside the profile content.

7. Existing route-owner components for launch-managed routes (`LandingMeshFeature`, `SchoolsSearchFeature`, `SignInFeature`, `SchoolCompareFeature`, and any new content pages)
   - Render `PageMeta` with route-appropriate title and description.
   - If the team prefers route wrappers instead, add those wrappers in `apps/web/src/pages/` and update `apps/web/src/app/routes.tsx` in the same change.

8. `apps/web/src/components/seo/school-json-ld.test.tsx` (new)
   - Test JSON-LD output matches Schema.org `School` structure.
   - Test missing address fields still produce valid minimal output.

9. `apps/web/src/components/layout/page-meta.test.tsx` (extend)
   - Test document title, description, and canonical link output.

10. Route-level tests for the home/search/sign-in/compare/profile surfaces
    - Assert each route renders the expected title/description in the browser DOM after hydration.

## Testing And Quality Gates

### Required tests

- `PageMeta` renders document title, description, and `<link rel="canonical">` with the correct URL.
- `SchoolJsonLd` outputs valid JSON-LD with `@type: "School"`.
- School profile page passes title, description, and canonical values through from API data.
- `robots.txt` and `sitemap.xml` are served by the Vite dev server from `public/`.
- `index.html` contains the expected site-wide fallback Open Graph and Twitter Card tags.

### Quality gate

- `make lint` passes.
- `make test` passes.
- `cd apps/web && npm run build` passes.
- Manual validation: inspect browser-visible title, description, and canonical tags on home, search, sign-in, compare, and school profile routes.

## Acceptance Criteria

- Launch-managed routes render meaningful browser-visible titles and descriptions.
- Static content routes and school profile routes render canonical URLs where appropriate.
- School profile pages include JSON-LD `School` structured data.
- `robots.txt` and the static-route `sitemap.xml` are accessible at root.
- Favicon, default OG image, and web manifest render correctly.
- Reliable school-profile social share cards and school-profile sitemap enumeration are explicitly deferred rather than implied.
- No existing route regresses in layout or functionality.

## Rollback

Per-file: `git checkout -- <file>`

Static assets in `public/` can be removed without side effects on application logic.
