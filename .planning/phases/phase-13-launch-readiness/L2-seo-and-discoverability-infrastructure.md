# L2 - SEO And Discoverability Infrastructure

## Document Control

- Status: Planned
- Last updated: 2026-03-09
- Depends on:
  - `L1-content-page-foundation.md` (PageMeta component and react-helmet-async provider)
  - `docs/architecture/frontend-conventions.md`

## Objective

Make every Civitas route discoverable by search engines and shareable on social platforms. Deliver the technical SEO infrastructure — meta tags, structured data, canonical URLs, robots.txt, sitemap, favicon, and web manifest — so that search and profile pages can rank, share cards render correctly, and crawlers can index the site.

## Scope

### In scope

- robots.txt allowing crawl of public routes.
- Sitemap XML file listing known static routes and school profile URL patterns.
- Favicon set (SVG + PNG fallbacks) and web manifest for mobile add-to-home-screen.
- Open Graph and Twitter Card meta tags on every route.
- Dynamic OG tags on school profile pages (school name, type, Ofsted rating in description).
- Canonical `<link rel="canonical">` on every route.
- JSON-LD `School` structured data on school profile pages.
- Default share image (OG fallback) for routes without a page-specific image.

### Out of scope

- Location-based SEO pages (Phase 12 / `11A-seo-location-pages.md`).
- Server-side rendering or pre-rendering — the current Vite SPA architecture is retained. If SSR is adopted later, SEO tags will already be in place.
- Dynamic sitemap generation from the database — the initial sitemap is a static file covering known route patterns. Dynamic generation can be added as a Phase 12 enhancement.
- Page speed or Core Web Vitals optimization beyond what is already in `.planning/phases/phase-5-ux-uplift/`.

## Decisions

1. **Static sitemap, not dynamic.** A hand-maintained `sitemap.xml` listing the static content pages and a URL pattern hint for `/schools/{urn}` is sufficient for launch. A build-time or server-generated sitemap enumerating all ~25,000 school URNs is a Phase 12 enhancement.
2. **SVG-first favicon.** Ship a single `favicon.svg` with a `<link rel="icon">` fallback to `favicon-32x32.png` and `favicon-16x16.png` for older browsers. Apple Touch Icon included as `apple-touch-icon.png` (180×180).
3. **No third-party OG image generation.** The default share image is a static asset. School profile OG descriptions are text-only (school name + type + Ofsted rating). Image generation per school is deferred.
4. **Structured data uses Schema.org `School` type.** Properties: `name`, `identifier` (URN), `address` (from GIAS), `url` (canonical). Extended properties like `aggregateRating` are not included — Civitas does not assign ratings.

## Frontend Design

### robots.txt

```text
User-agent: *
Allow: /

Sitemap: https://civitas.uk/sitemap.xml
```

Served from `apps/web/public/robots.txt`. The production domain is used in the Sitemap directive; local development ignores this file.

### sitemap.xml

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

Served from `apps/web/public/sitemap.xml`. School profile URLs are omitted from the static sitemap and added when dynamic generation is implemented.

### Favicon and web manifest

Files placed in `apps/web/public/`:

| File | Purpose |
|---|---|
| `favicon.svg` | Modern browsers, scalable icon |
| `favicon-32x32.png` | Legacy fallback 32px |
| `favicon-16x16.png` | Legacy fallback 16px |
| `apple-touch-icon.png` | iOS home-screen icon (180×180) |
| `site.webmanifest` | PWA manifest — name, short_name, icons, theme_color, background_color |
| `og-default.png` | Default Open Graph share image (1200×630) |

`index.html` additions:

```html
<link rel="icon" type="image/svg+xml" href="/favicon.svg" />
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png" />
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
<link rel="manifest" href="/site.webmanifest" />
```

### PageMeta extension for OG and canonical

Extend the `PageMeta` component from L1 to accept:

```text
PageMeta
  props:
    title: string
    description?: string
    canonicalPath?: string          — path segment, e.g. "/about"
    ogType?: "website" | "article"  — defaults to "website"
    ogImage?: string                — defaults to "/og-default.png"
```

The component renders:

- `<title>{title} | Civitas</title>`
- `<meta name="description" content="{description}" />`
- `<link rel="canonical" href="https://civitas.uk{canonicalPath}" />`
- `<meta property="og:title" content="{title}" />`
- `<meta property="og:description" content="{description}" />`
- `<meta property="og:image" content="{ogImage}" />`
- `<meta property="og:url" content="https://civitas.uk{canonicalPath}" />`
- `<meta property="og:type" content="{ogType}" />`
- `<meta property="og:site_name" content="Civitas" />`
- `<meta name="twitter:card" content="summary_large_image" />`

The canonical base URL is read from an environment variable (`VITE_PUBLIC_URL`) so development and production diverge cleanly.

### School profile dynamic meta

On the school profile route (`/schools/:urn`), `PageMeta` receives:

- `title`: School name (e.g. "Oakwood Academy")
- `description`: "{School name} — {type of establishment}, {phase}, Ofsted: {rating}. View demographics, trends, and area context on Civitas."
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
   - Create with `robots.txt`, `sitemap.xml`, `site.webmanifest`.
   - Add favicon files and `og-default.png` (placeholder asset until branding finalised).

2. `apps/web/index.html`
   - Add favicon, apple-touch-icon, and manifest `<link>` elements.
   - Add fallback meta description: `<meta name="description" content="Civitas — independent school research for England. Demographics, trends, Ofsted, and area context." />`

3. `apps/web/src/components/layout/PageMeta.tsx`
   - Extend with `canonicalPath`, `ogType`, `ogImage` props and OG/Twitter Card/canonical `<meta>` output.

4. `apps/web/src/components/seo/SchoolJsonLd.tsx` (new)
   - Renders JSON-LD `School` structured data from profile data props.

5. `apps/web/src/features/school-profile/` (existing profile page)
   - Wire `PageMeta` with dynamic title, description, and canonical path from API data.
   - Render `SchoolJsonLd` below the profile content.

6. `apps/web/src/app/routes.tsx` (existing routes)
   - Ensure every route provides `PageMeta`. The home route gets a generic Civitas title and description.

7. `apps/web/src/components/seo/school-json-ld.test.tsx` (new)
   - Test JSON-LD output matches Schema.org `School` type structure.
   - Test missing address fields produce valid (minimal) output.

8. `apps/web/src/components/layout/page-meta.test.tsx` (extend)
   - Test OG tags, canonical link, and Twitter Card meta are rendered.

## Testing And Quality Gates

### Required tests

- `PageMeta` renders `og:title`, `og:description`, `og:image`, `og:url`, and `twitter:card` meta tags.
- `PageMeta` renders `<link rel="canonical">` with correct URL.
- `SchoolJsonLd` outputs valid JSON-LD with `@type: "School"`.
- School profile page passes the OG tags through from API data.
- `robots.txt` and `sitemap.xml` are served by Vite dev server from `public/`.

### Quality gate

- `npm run lint` passes.
- `npm run typecheck` passes.
- `npm run test` passes.
- Manual validation: paste a school profile URL into the Facebook Sharing Debugger or Twitter Card Validator and confirm preview renders.

## Acceptance Criteria

- Every route renders meaningful OG meta tags and a canonical URL.
- School profile pages include JSON-LD `School` structured data.
- `robots.txt` and `sitemap.xml` are accessible at root.
- Favicon and web manifest render correctly (browser tab icon, mobile home-screen).
- No existing route regresses in layout or functionality.

## Rollback

Per-file: `git checkout -- <file>`

Static assets in `public/` can be removed without side effects on application logic.
