# L5 - Quality Gates

## Goal

Define the sign-off evidence required before Phase 13 (Product Foundation and Launch Readiness) is considered complete.

## MVP In Scope

### L1 - Content Page Foundation

- `ContentPageLayout` shared prose component renders heading, article wrapper, and prose styles.
- `PageMeta` component manages `<title>`, `<meta name="description">`, and pass-through for OG/canonical.
- `HelmetProvider` registered at app root.
- Prose typography styles work in dark and light themes.
- Content page paths registered in `paths.ts`.
- Footer links use `<Link>` with real paths instead of `href="#"`.
- Route entries registered in `routes.tsx`.

### L2 - SEO And Discoverability Infrastructure

- `robots.txt` and `sitemap.xml` served from `public/`.
- Favicon set (SVG + PNG fallback) and `site.webmanifest` present and rendering.
- `apple-touch-icon.png` present.
- `index.html` includes favicon, manifest, and fallback meta description `<link>`/`<meta>` tags.
- `PageMeta` extended with OG, Twitter Card, and canonical URL output.
- School profile pages render dynamic OG tags from API data.
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
- `/accessibility` renders Accessibility Statement following GDS format.
- Footer Privacy link navigates to `/privacy`; Terms and Accessibility links added.
- `CookieConsentBanner` component built and renders when no consent recorded.
- `useCookieConsent` hook returns consent status and accept/decline actions.
- Accept and Decline buttons update `localStorage` and dismiss banner.
- Banner does not block page interaction.

## Explicitly Out Of Scope

- Professional legal review of Privacy, Terms, and Accessibility content (required before production launch, but is an operational step, not an engineering deliverable).
- Dynamic sitemap generation enumerating all school URNs.
- Server-side rendering or pre-rendering.
- Location-based SEO pages (Phase 12).
- Contact form with backend processing.
- Third-party cookie management platform.
- OG image generation per school profile.

## Verification Requirements

### Frontend component coverage

- `ContentPageLayout` renders `<h1>`, prose wrapper, and `PageMeta`.
- `PageMeta` sets document `<title>`, `<meta name="description">`, OG tags, Twitter Card, and canonical link.
- `SchoolJsonLd` outputs valid JSON-LD with `@type: "School"`.
- `CookieConsentBanner` shows/hides based on `localStorage` state.
- `useCookieConsent` hook reads and writes consent correctly.
- Each content page (`AboutPage`, `DataSourcesPage`, `ContactPage`, `PrivacyPage`, `TermsPage`, `AccessibilityPage`) renders heading and primary content.
- `SiteFooter` links resolve to real paths — no `href="#"` remains.

### Static asset verification

- `robots.txt` accessible at `/robots.txt`.
- `sitemap.xml` accessible at `/sitemap.xml` and lists all static routes.
- `site.webmanifest` accessible at `/site.webmanifest` with valid JSON.
- Favicon renders in browser tab.
- Apple Touch Icon present at expected path.

### Theme parity

- All content pages readable in both dark and light themes.
- Cookie consent banner styled correctly in both themes.
- Prose typography (headings, paragraphs, lists, links, tables) renders legibly in both themes.

### Responsive verification

- All content pages render without horizontal overflow at 375px.
- Cookie consent banner does not overlap critical UI at mobile widths.
- Source table on Data Sources page scrolls or stacks gracefully on mobile.

## Performance Gates

- No new route adds a bundle chunk larger than 20 KB gzipped (content pages are text-heavy, not code-heavy).
- No new network request on the critical search or profile path — content pages are independent routes.
- Favicon and manifest requests do not introduce render-blocking resources.

## Acceptance Criteria

- All footer placeholder links (`#`) resolve to real routed pages.
- Every route has a meaningful `<title>` and `<meta name="description">`.
- School profile pages include Open Graph tags and JSON-LD `School` structured data.
- `robots.txt` and `sitemap.xml` are served for crawler access.
- Favicon and web manifest render correctly across browsers and mobile home-screen add.
- Privacy Policy and Terms of Use are published and linked from footer and sign-up flows.
- Cookie consent banner is functional before any non-essential cookies are set.
- Accessibility statement is published.
- `npm run lint` passes.
- `npm run typecheck` passes.
- `npm run test` passes.
- No new horizontal overflow or layout regression at 375px.
- No regression on existing routes (search, school profile, compare).

## Sign-Off Evidence

Phase 13 is complete when the following evidence is recorded in a `signoff-YYYY-MM-DD.md` file in the phase folder:

1. `npm run lint` — clean output.
2. `npm run typecheck` — clean output.
3. `npm run test` — all tests pass.
4. Manual verification of all six content page routes in both themes.
5. Manual verification of cookie consent banner show/accept/decline cycle.
6. Manual verification of school profile OG tags (Facebook Sharing Debugger or equivalent).
7. Manual verification of favicon and manifest in Chrome, Firefox, and Safari.
8. Confirmation that no `href="#"` remains in the footer.
9. Confirmation that `robots.txt`, `sitemap.xml`, and `site.webmanifest` are accessible.
