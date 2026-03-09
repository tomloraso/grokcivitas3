# L5 - Quality Gates

## Goal

Define the sign-off evidence required before Phase 13 (Product Foundation and Launch Readiness) is considered complete.

## MVP In Scope

### L1 - Content Page Foundation

- `ContentPageLayout` shared prose component renders heading, article wrapper, and prose styles.
- `PageMeta` component manages `<title>`, `<meta name="description">`, and canonical output.
- `HelmetProvider` registered at app root.
- Prose typography styles work in dark and light themes.
- Content page paths registered in `paths.ts`.
- Footer links use `<Link>` with real paths instead of `href="#"`.
- Route entries registered in `routes.tsx`.

### L2 - SEO And Discoverability Infrastructure

- `robots.txt` and `sitemap.xml` served from `public/`.
- Favicon set (SVG + PNG fallback) and `site.webmanifest` present and rendering.
- `apple-touch-icon.png` present.
- `index.html` includes favicon, manifest, fallback meta description, and generic OG/Twitter tags.
- `PageMeta` manages document title, description, and canonical URL output.
- `SchoolJsonLd` renders valid JSON-LD `School` structured data on profile pages.
- Default OG share image (`og-default.png`) present.

### L3 - About And Data Sources

- `/about` renders full About Civitas content.
- `/data-sources` renders source table listing all sources with publisher links.
- `/contact` renders contact information with working `mailto:` link.
- All three pages use `ContentPageLayout` with correct `PageMeta`.
- Footer About and Contact links navigate to the correct pages.

### L4 - Legal And Compliance

- `/privacy` renders structurally complete Privacy Policy.
- `/terms` renders structurally complete Terms of Use.
- `/accessibility` renders Accessibility Statement following the GDS format.
- Footer Privacy link navigates to `/privacy`; Terms and Accessibility links added.
- Sign-in flow links to Privacy Policy and Terms of Use before auth starts.
- Privacy Policy discloses the launch auth/session cookie plus auth/payment processors.

## Explicitly Out Of Scope

- Professional legal review of Privacy, Terms, and Accessibility content (required before production launch, but is an operational step, not an engineering deliverable).
- Dynamic sitemap generation enumerating all school URNs.
- Reliable route-specific social share cards for dynamic SPA routes.
- Server-side rendering or prerendering.
- Location-based SEO pages (Phase 12).
- Contact form with backend processing.
- Third-party cookie management platform.
- Cookie preferences banner while launch uses only strictly necessary first-party auth cookies.
- OG image generation per school profile.

## Verification Requirements

### Frontend component coverage

- `ContentPageLayout` renders `<h1>`, prose wrapper, and `PageMeta`.
- `PageMeta` sets document `<title>`, `<meta name="description">`, and canonical link.
- `SchoolJsonLd` outputs valid JSON-LD with `@type: "School"`.
- Each content page (`AboutPage`, `DataSourcesPage`, `ContactPage`, `PrivacyPage`, `TermsPage`, `AccessibilityPage`) renders heading and primary content.
- `SignInFeature` exposes Privacy Policy and Terms of Use links on the anonymous sign-in view.
- `SiteFooter` links resolve to real paths; no `href="#"` remains.

### Static asset verification

- `robots.txt` accessible at `/robots.txt`.
- `sitemap.xml` accessible at `/sitemap.xml` and lists all static routes.
- `site.webmanifest` accessible at `/site.webmanifest` with valid JSON.
- Favicon renders in the browser tab.
- Apple Touch Icon present at the expected path.
- Built `index.html` contains the generic fallback OG/Twitter tags and `og-default.png` reference.

### Theme parity

- All content pages readable in both dark and light themes.
- Prose typography (headings, paragraphs, lists, links, tables) renders legibly in both themes.
- Sign-in disclosure copy remains legible and unobtrusive in both themes.

### Responsive verification

- All content pages render without horizontal overflow at 375px.
- Source table on the Data Sources page scrolls or stacks gracefully on mobile.
- Sign-in disclosure copy does not crowd the submit controls at mobile widths.

## Performance Gates

- No new route adds a bundle chunk larger than 20 KB gzipped (content pages are text-heavy, not code-heavy).
- No new network request on the critical search or profile path; content pages are independent routes.
- Favicon and manifest requests do not introduce render-blocking resources.

## Acceptance Criteria

- All footer placeholder links (`#`) resolve to real routed pages.
- Launch-managed routes have meaningful browser-visible `<title>` and `<meta name="description">`.
- Static content routes and school profile routes include canonical URLs where appropriate.
- School profile pages include JSON-LD `School` structured data.
- `robots.txt` and the static-route `sitemap.xml` are served for crawler entry points.
- Favicon and web manifest render correctly across browsers and mobile home-screen add.
- Privacy Policy and Terms of Use are published and linked from footer and sign-in flows.
- Privacy Policy discloses the launch auth/session cookie and the auth/payment processors.
- A cookie preferences banner is only required before any non-essential cookies are introduced.
- Accessibility statement is published.
- `make lint` passes.
- `make test` passes.
- `cd apps/web && npm run build` passes.
- No new horizontal overflow or layout regression at 375px.
- No regression on existing routes (search, school profile, compare).

## Sign-Off Evidence

Phase 13 is complete when the following evidence is recorded in a `signoff-YYYY-MM-DD.md` file in the phase folder:

1. `make lint` - clean output.
2. `make test` - all tests pass.
3. `cd apps/web && npm run build` - clean output.
4. Manual verification of all six content page routes in both themes.
5. Manual verification of browser-visible title, description, and canonical tags on home, search, sign-in, compare, and school profile routes.
6. Manual verification of `SchoolJsonLd` in the rendered DOM (or equivalent structured-data check).
7. Manual verification of favicon and manifest in Chrome, Firefox, and Safari.
8. Confirmation that no `href="#"` remains in the footer.
9. Confirmation that `robots.txt`, `sitemap.xml`, and `site.webmanifest` are accessible.
10. Confirmation that `SignInFeature` links to Privacy Policy and Terms of Use.
