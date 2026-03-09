# L4 - Legal And Compliance

## Document Control

- Status: Planned
- Last updated: 2026-03-09
- Depends on:
  - `L1-content-page-foundation.md` (ContentPageLayout, PageMeta, prose styles, route paths)
  - `.planning/phases/phase-10-premium-access/10A-provider-boundary-gate.md` (session cookie scope)
  - `.planning/phases/phase-10-premium-access/10B-auth-session-foundation.md` (authentication prerequisites)

## Phase 10 Prerequisite

This deliverable is a **hard prerequisite** for Phase 10 Stage 10B (billing, webhooks, and premium enforcement).

- **Privacy Policy** must be live before production collection of personal data or payment data.
- **Terms of Use** must be live before paid features and billing flows go live.
- **Cookie disclosures** must be live before production sign-in.
- A **cookie preferences banner** becomes mandatory only if Civitas introduces non-essential cookies such as analytics, advertising, or experimentation cookies.

L4 should be completed and merged before Stage 10B begins implementation. Privacy and cookie disclosures should merge before Stage 10A ships to any non-local environment.

## Objective

Deliver the legal and transparency pages required or strongly recommended for a publicly accessible UK web product: Privacy Policy, Terms of Use, and an Accessibility Statement. This slice also makes the sign-in flow disclose the legal documents before account creation begins. It does not attempt to gate the backend-issued Phase 10 session cookie from React state.

## Scope

### In scope

- **Privacy Policy** page - what data Civitas collects, why, legal basis, retention, and user rights.
- **Terms of Use** page - conditions for using Civitas, disclaimers, intellectual property.
- **Accessibility Statement** page - conformance level, known issues, and contact for accessibility concerns.
- **Sign-in disclosure copy** linking to Privacy Policy and Terms of Use before the user submits email.
- **Cookie disclosure content** covering strictly necessary auth cookies at launch and the policy for any future non-essential cookies.
- Route registration, footer link activation, and PageMeta wiring for all three pages.

### Out of scope

- Legal review - the content in this document is a technical implementation plan. Final copy MUST be reviewed by a qualified legal professional before publication.
- Cookie management platform (for example, OneTrust or CookieBot). Evaluate this later if cookie complexity increases.
- A cookie banner or preferences UI while Civitas only uses strictly necessary first-party auth cookies at launch.
- DPIA (Data Protection Impact Assessment), which may still be required operationally depending on the scope of Phase 10 processing.

## Decisions

1. **No consent banner for launch while Civitas only uses strictly necessary auth cookies.** If non-essential cookies are introduced later, ship a cookie preferences banner in that same change set.
2. **Do not gate the Phase 10 session cookie on client-side state.** The auth cookie remains backend-owned, per Phase 10, and is disclosed in the Privacy Policy rather than controlled by `localStorage`.
3. **Privacy Policy and Terms of Use are prose pages.** They use `ContentPageLayout` from L1. Content is maintained inline in the component files. If legal text changes frequently, a Markdown or MDX source can be evaluated later.
4. **Accessibility Statement follows the GDS model.** Civitas uses the GDS structure as a launch transparency document, without claiming public-sector status.
5. **The sign-in flow must surface document links before auth starts.** Footer links alone are not sufficient once the product begins collecting account data.

## Content Outline

### Privacy Policy

**Route:** `/privacy`

1. **Who we are.** Civitas operator name and contact details. Data controller identity.
2. **What data we collect.**
   - **Before Phase 10:** Browsing is anonymous from a product-account perspective, but standard server or infrastructure logs may still capture IP address, user agent, and request metadata for security and operations.
   - **After Phase 10:** Email address, auth-provider identifiers, strictly necessary session cookies, and payment data handled by a third-party payment provider (Civitas does not store card details).
3. **Why we collect it.** Legal basis for each category (contract for account features, legitimate interests for security and service operation, and consent only if optional cookies are introduced later).
4. **How long we keep it.** Retention periods per data category.
5. **Who we share it with.** Third-party processors (auth provider, payment provider, infrastructure services where relevant). No data is sold.
6. **Your rights.** Right to access, rectify, erase, restrict processing, data portability, and object. Contact details for exercising rights.
7. **Cookies.** Which strictly necessary cookies are set at launch, their purpose, and their duration. State clearly that Civitas does not use analytics or advertising cookies at launch, and explain that any future optional cookies will be introduced with a preferences mechanism.
8. **Changes to this policy.** How updates are communicated.
9. **Contact.** Email address for privacy enquiries.

### Terms Of Use

**Route:** `/terms`

1. **Acceptance.** By using Civitas, users agree to these terms.
2. **What Civitas provides.** An independent research tool presenting publicly available school data. Not advice, not a recommendation service.
3. **Data accuracy disclaimer.** Civitas aggregates public data and presents it as-is. While reasonable care is taken, accuracy cannot be guaranteed. Users should verify important information with original sources.
4. **Intellectual property.** Civitas owns the presentation, design, and tooling. Underlying data is Crown Copyright or published under open licences. Source attribution is provided on the Data Sources page.
5. **Acceptable use.** No scraping, no automated access beyond reasonable personal use, no redistribution of aggregated datasets.
6. **Account terms (Phase 10).** Account holders are responsible for their credentials. Civitas may suspend accounts that violate terms.
7. **Payment terms (Phase 10).** Subscription terms, cancellation, and refund policy. These clauses must be finalised before Stage 10B goes live; do not ship placeholder commercial language with production billing.
8. **Limitation of liability.** Standard limitation clause appropriate for a free/freemium information service.
9. **Governing law.** Laws of England and Wales.
10. **Changes to terms.** How updates are communicated.

### Accessibility Statement

**Route:** `/accessibility`

Following the GDS recommended structure:

1. **How accessible Civitas is.** Target conformance level: WCAG 2.1 AA.
2. **What we do to meet accessibility standards.** Semantic HTML, keyboard navigation, ARIA labels, colour contrast, and screen-reader-compatible alternatives where feasible.
3. **Known issues.** List any known accessibility gaps honestly. For launch, this likely includes:
   - Map interaction is not fully keyboard accessible (MapLibre GL limitation; text search is the accessible alternative).
   - Complex data visualisations may not be fully described for screen readers (data tables provide the accessible alternative).
4. **How to report accessibility problems.** Contact email.
5. **Enforcement procedure.** Link to the Equality Advisory Support Service (EASS) for users who are not satisfied with the response.
6. **Technical information.** Browser and assistive technology compatibility.
7. **Last reviewed date.**

### Cookie disclosures and future preferences

Launch behaviour:

1. Do not render a consent banner solely for the strictly necessary sign-in session cookie.
2. The Privacy Policy includes a cookie table describing the auth/session cookie name, purpose, and lifetime.
3. The sign-in flow links to Privacy Policy and Terms of Use before auth starts.
4. If non-essential cookies are added later, introduce a `CookiePreferencesBanner` in that same change set.
5. That future banner may store consent in `localStorage` or a first-party cookie, but it must gate only optional scripts. It must not block backend session cookie issuance.

## Frontend Design

### Legal pages

Each page uses `ContentPageLayout` from L1 with route-appropriate `PageMeta`.

### Sign-in disclosure

Add a short disclosure block below the email field or submit controls in `SignInFeature`:

```text
By continuing, you agree to the Terms of Use and acknowledge the Privacy Policy.
```

Implementation notes:

- `Terms of Use` and `Privacy Policy` are internal `<Link>` elements.
- Keep the copy concise and non-marketing.
- Do not imply optional cookie consent when the only launch cookie is strictly necessary for sign-in.

## File-Oriented Implementation Plan

1. `apps/web/src/pages/PrivacyPage.tsx` (new)
   - Privacy Policy content in `ContentPageLayout`.

2. `apps/web/src/pages/TermsPage.tsx` (new)
   - Terms of Use content in `ContentPageLayout`.

3. `apps/web/src/pages/AccessibilityPage.tsx` (new)
   - Accessibility Statement content in `ContentPageLayout`.

4. `apps/web/src/app/routes.tsx`
   - Register `/privacy`, `/terms`, and `/accessibility` routes.

5. `apps/web/src/components/layout/SiteFooter.tsx`
   - Confirm Privacy link points to the real path.
   - Add Terms and Accessibility links if not already present.

6. `apps/web/src/features/auth/SignInFeature.tsx`
   - Add concise Privacy Policy and Terms of Use links near the sign-in submit action.

7. `apps/web/src/pages/privacy-page.test.tsx` (new)
   - Render heading and key sections.
   - Assert the page includes the cookies/session disclosure section.
   - Assert `PageMeta` sets the correct title.

8. `apps/web/src/pages/terms-page.test.tsx` (new)
   - Render heading and key sections.
   - Assert `PageMeta` sets the correct title.

9. `apps/web/src/pages/accessibility-page.test.tsx` (new)
   - Render heading and key sections.
   - Assert `PageMeta` sets the correct title.

10. `apps/web/src/features/auth/SignInFeature.test.tsx`
    - Assert Privacy Policy and Terms of Use links are rendered on the anonymous sign-in view.

## Testing And Quality Gates

### Required tests

- Each legal page renders its heading and `PageMeta` title.
- Privacy Policy includes a cookies/session disclosure section.
- The anonymous sign-in view renders Privacy Policy and Terms of Use links.
- Pages render correctly in dark and light themes.

### Quality gate

- `make lint` passes.
- `make test` passes.
- `cd apps/web && npm run build` passes.
- No layout regression at 375px mobile width.
- Sign-in disclosure copy does not crowd or obscure the submit controls on mobile.

## Acceptance Criteria

- `/privacy`, `/terms`, and `/accessibility` routes render full content.
- Footer links for Privacy navigate to the correct page; Terms and Accessibility links are added.
- The sign-in flow links to Privacy Policy and Terms of Use before auth starts.
- Privacy Policy discloses the launch auth/session cookie and the auth/payment processors.
- All pages use `ContentPageLayout` with correct `PageMeta`.
- Content is structurally complete, but final legal copy and commercial clauses still require professional review before production.

## Important Note

**The content outlined in this document is a structural template, not legal advice.** Final Privacy Policy, Terms of Use, Accessibility Statement, and any payment/refund clauses must be reviewed and approved by a qualified legal professional before publication. Do not ship these pages to production with placeholder legal or commercial language.

## Rollback

Per-file: `git checkout -- <file>`

If non-essential cookies are introduced later, the follow-on preferences banner can be shipped behind a feature flag until the rollout is ready.
