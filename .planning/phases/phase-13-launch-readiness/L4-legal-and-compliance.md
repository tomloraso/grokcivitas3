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

- **Privacy Policy** must be live before collecting any personal data or processing payments.
- **Terms of Use** must be live before authenticated users interact with paid features.
- **Cookie Consent** must be functional before any non-essential cookies are set in production, including session cookies from Phase 10 Stage 10A.

L4 should be completed and merged before Stage 10B begins implementation. Cookie consent should ideally be live before Stage 10A ships to any non-local environment.

## Objective

Deliver the legal and compliance pages required for a publicly accessible UK web product: Privacy Policy, Terms of Use, Accessibility Statement, and a cookie consent mechanism. These pages are not optional extras — they are legal obligations under UK GDPR, the Privacy and Electronic Communications Regulations (PECR), and the Equality Act 2010.

## Scope

### In scope

- **Privacy Policy** page — what data Civitas collects, why, legal basis, retention, and user rights.
- **Terms of Use** page — conditions for using Civitas, disclaimers, intellectual property.
- **Accessibility Statement** page — conformance level, known issues, contact for accessibility concerns.
- **Cookie Consent banner** — UI component that requests consent before setting non-essential cookies.
- Route registration, footer link activation, and PageMeta wiring for all three pages.

### Out of scope

- Legal review — the content in this document is a technical implementation plan. Final copy MUST be reviewed by a qualified legal professional before publication.
- Cookie management platform (e.g. OneTrust, CookieBot) — the initial implementation is a lightweight custom banner. A third-party platform can be adopted later if cookie complexity increases.
- DPIA (Data Protection Impact Assessment) — may be required depending on the scope of personal data processing in Phase 10, but is a separate operational document.

## Decisions

1. **Custom cookie consent banner, not a third-party widget.** Civitas currently sets zero non-essential cookies. The only cookies anticipated are session cookies from Phase 10 authentication. A lightweight banner that records consent in `localStorage` is proportionate. If analytics or advertising cookies are added later, evaluate a managed platform.
2. **Cookie consent state stored in `localStorage`.** A `civitas-cookie-consent` key with values `accepted`, `rejected`, or absent (not yet responded). The banner re-appears if the key is absent.
3. **Privacy Policy and Terms of Use are prose pages.** They use `ContentPageLayout` from L1. Content is maintained inline in the component files. If legal text changes frequently, a Markdown file sourced at build time can be evaluated.
4. **Accessibility Statement follows the GDS model.** The UK Government Digital Service publishes a recommended format for accessibility statements. Civitas follows this structure.

## Content Outline

### Privacy Policy

**Route:** `/privacy`

1. **Who we are.** Civitas operator name and contact details. Data controller identity.
2. **What data we collect.**
   - **Before Phase 10:** No personal data is collected. No cookies are set. No analytics or tracking. Usage is fully anonymous.
   - **After Phase 10:** Email address, authentication tokens, session cookies, payment data (processed by third-party payment provider — Civitas does not store card details).
3. **Why we collect it.** Legal basis for each category (consent for cookies, contract for account features, legitimate interest for service operation).
4. **How long we keep it.** Retention periods per data category.
5. **Who we share it with.** Third-party processors (auth provider, payment provider). No data is sold.
6. **Your rights.** Right to access, rectify, erase, restrict processing, data portability, and object. Contact details for exercising rights.
7. **Cookies.** What cookies are set, their purpose, and how to control them. Cross-reference the cookie consent banner.
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
7. **Payment terms (Phase 10).** Subscription terms, cancellation, and refund policy. Placeholder section until Phase 10 pricing is finalised.
8. **Limitation of liability.** Standard limitation clause appropriate for a free/freemium information service.
9. **Governing law.** Laws of England and Wales.
10. **Changes to terms.** How updates are communicated.

### Accessibility Statement

**Route:** `/accessibility`

Following the GDS recommended structure:

1. **How accessible Civitas is.** Target conformance level: WCAG 2.1 AA.
2. **What we do to meet accessibility standards.** Semantic HTML, keyboard navigation, ARIA labels, colour contrast, screen reader compatibility.
3. **Known issues.** List any known accessibility gaps honestly. For launch, this likely includes:
   - Map interaction is not fully keyboard accessible (MapLibre GL limitation; text search is the accessible alternative).
   - Complex data visualisations may not be fully described for screen readers (data tables provide the accessible alternative).
4. **How to report accessibility problems.** Contact email.
5. **Enforcement procedure.** Link to the Equality Advisory Support Service (EASS) for users who are not satisfied with the response.
6. **Technical information.** Browser and assistive technology compatibility.
7. **Last reviewed date.**

### Cookie Consent Banner

Not a page — a UI component that appears on first visit.

**Behaviour:**

1. On first load, if `localStorage` key `civitas-cookie-consent` is absent, show a non-intrusive banner at the bottom of the viewport.
2. Banner text: "Civitas uses cookies to keep you signed in. See our [Privacy Policy](/privacy) for details."
3. Two buttons: "Accept" and "Decline".
4. On "Accept": set `localStorage` key to `accepted`, dismiss banner, allow session cookies.
5. On "Decline": set `localStorage` key to `rejected`, dismiss banner, do not set session cookies. Users can still browse the site as anonymous users.
6. Banner does not block page interaction (no modal overlay).
7. Banner respects the existing design system — uses existing Button component, respects dark/light theme.

**Pre-Phase 10 note:** Before Phase 10, no cookies are set, so the banner has no functional effect. It can be hidden behind a feature flag or shown with adjusted copy ("Civitas does not currently use cookies"). The simplest approach is to ship the banner with Phase 10 Stage 10A, not before. However, the component should be built in this phase so it is ready.

## Frontend Design

### Cookie consent component

```text
CookieConsentBanner
  state:
    consentStatus: "accepted" | "rejected" | null (from localStorage)
  
  renders:
    if consentStatus is null:
      fixed-bottom bar with message, Accept button, Decline button
    else:
      nothing
  
  on Accept:
    localStorage.setItem("civitas-cookie-consent", "accepted")
    setConsentStatus("accepted")
  
  on Decline:
    localStorage.setItem("civitas-cookie-consent", "rejected")
    setConsentStatus("rejected")
```

The banner is rendered in `App.tsx` alongside the router, outside the route tree so it appears on every page.

### Cookie consent hook

```text
useCookieConsent()
  returns:
    consentStatus: "accepted" | "rejected" | null
    acceptCookies: () => void
    declineCookies: () => void
```

Phase 10 auth code checks `consentStatus === "accepted"` before setting session cookies.

## File-Oriented Implementation Plan

1. `apps/web/src/pages/PrivacyPage.tsx` (new)
   - Privacy Policy content in `ContentPageLayout`.

2. `apps/web/src/pages/TermsPage.tsx` (new)
   - Terms of Use content in `ContentPageLayout`.

3. `apps/web/src/pages/AccessibilityPage.tsx` (new)
   - Accessibility Statement content in `ContentPageLayout`.

4. `apps/web/src/components/consent/CookieConsentBanner.tsx` (new)
   - Cookie consent banner UI component.

5. `apps/web/src/components/consent/useCookieConsent.ts` (new)
   - Hook for reading and setting cookie consent state.

6. `apps/web/src/App.tsx`
   - Render `CookieConsentBanner` at the app root level.

7. `apps/web/src/app/routes.tsx`
   - Register `/privacy`, `/terms`, `/accessibility` routes.

8. `apps/web/src/components/layout/SiteFooter.tsx`
   - Confirm Privacy link points to real path (initial wiring in L1).
   - Add Terms and Accessibility links if not already present.

9. `apps/web/src/pages/privacy-page.test.tsx` (new)
   - Renders heading and key sections.
   - PageMeta sets correct title.

10. `apps/web/src/pages/terms-page.test.tsx` (new)
    - Renders heading and key sections.
    - PageMeta sets correct title.

11. `apps/web/src/pages/accessibility-page.test.tsx` (new)
    - Renders heading and key sections.
    - PageMeta sets correct title.

12. `apps/web/src/components/consent/cookie-consent-banner.test.tsx` (new)
    - Banner shows when no consent in localStorage.
    - Accept button sets localStorage to "accepted" and dismisses banner.
    - Decline button sets localStorage to "rejected" and dismisses banner.
    - Banner does not show when consent already recorded.

## Testing And Quality Gates

### Required tests

- Each legal page renders its heading and PageMeta title.
- Cookie consent banner appears when localStorage key is absent.
- Accept/Decline buttons update localStorage and dismiss the banner.
- Banner does not reappear after consent is recorded.
- `useCookieConsent` hook returns correct consent status.
- Pages render correctly in dark and light themes.

### Quality gate

- `npm run lint` passes.
- `npm run typecheck` passes.
- `npm run test` passes.
- No layout regression at 375px mobile width.
- Cookie consent banner does not overlap or obscure page content.

## Acceptance Criteria

- `/privacy`, `/terms`, and `/accessibility` routes render full content.
- Footer links for Privacy navigate to the correct page; Terms and Accessibility links added.
- Cookie consent banner appears on first visit and records user choice.
- `useCookieConsent` hook is available for Phase 10 auth code to check before setting cookies.
- All pages use `ContentPageLayout` with correct PageMeta.
- Content is placeholder-quality but structurally complete — final legal copy requires professional review.

## Important Note

**The content outlined in this document is a structural template, not legal advice.** Final Privacy Policy, Terms of Use, and Accessibility Statement text must be reviewed and approved by a qualified legal professional before publication. Do not ship these pages to production with only the developer-written placeholder copy.

## Rollback

Per-file: `git checkout -- <file>`

Cookie consent banner can be conditionally hidden via a feature flag without removing code.
