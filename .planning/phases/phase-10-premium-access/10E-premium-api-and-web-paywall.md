# 10E - Premium API Boundaries And Web Paywall

## Goal

Wire feature-tier premium access into the product surface by enforcing backend data boundaries and adding a clear, typed paywall experience in the web app.

This deliverable is where the premium model becomes visible to users. It must stay contract-driven and should not move access policy into the frontend.

## Scope

### Backend

- protect premium-only sections, analyses, and advanced workflow features across search, profile, trends, dashboard, compare, and premium AI surfaces
- return the allowed free subset when the user lacks the required entitlement
- expose access state and paywall-relevant metadata through Civitas API schemas
- provide account-facing endpoints for current premium access state

### Frontend

- sign-in and upgrade entry points
- locked-state and preview-state rendering
- post-purchase refresh flow that reflects reconciled backend state
- account view for current premium state if needed for purchase recovery and clarity

## Intended API Contract Strategy

### Public Read Routes Should Stay Readable

For public research routes, prefer:

- `200` with free-baseline payload plus access metadata

Over:

- `403` plus no useful response body

Reason:

- the product experience needs to show users what exists before purchase
- the UI still needs contract-stable paywall copy and locked-section state
- public search and profile navigation should not degrade into generic error handling

### Access Metadata Shape

Each premium-sensitive response should expose a typed access block that can answer:

- is the user anonymous, signed in, or premium-entitled?
- is this response a free baseline or does it include premium data?
- what portion is locked?
- which upgrade target or premium product is relevant?

Minimum fields to consider:

- `access_level`
- `requires_auth`
- `requires_purchase`
- `locked_sections`
- `available_products`
- `account_access_state`

Exact schema names can evolve, but the contract should be explicit enough that web features do not infer state from missing fields alone.

Recommended shared transport shapes:

- `SessionResponse`
- `AccountAccessResponse`
- `AvailablePremiumProductResponse`
- `LockedSectionResponse`
- `PaywallTargetResponse`

Recommended section-state enum:

- `available`
- `locked`
- `unavailable`

Use `locked` when a premium surface exists but the viewer lacks access. Use `unavailable` when the artifact is not published, not supported, or absent for product reasons.

## Surface-Specific Behavior

The exact rules come from `10G-premium-access-matrix.md`. This document defines the enforcement shape.

### Search

- Search remains free at the route level.
- If search gains premium enhancements such as advanced ranking, extra filter packs, or premium analysis, the API should express those as locked capabilities rather than introducing a separate premium-only search route.

### Profile And Trends

- Free users should still see school identity and approved free sections.
- Premium-only sections should be omitted or marked locked with explicit metadata.
- Section-level access decisions should be driven by named capabilities, not by one giant route-wide premium flag.

Recommended contract changes:

- `GET /api/v1/schools/{urn}`
  - keep the free baseline fields already used by the profile page
  - replace raw nullable premium fields such as `analyst_text` with typed section wrappers
  - add a top-level access block or section-level access blocks describing which premium surfaces are locked
- `GET /api/v1/schools/{urn}/trends/dashboard`
  - become an explicitly premium-aware response
  - return `state=locked` plus paywall metadata when the viewer lacks `premium_benchmark_dashboard`
  - return full metric sections only when unlocked

The free profile route should not depend on the dashboard endpoint for its baseline benchmark rendering path. Latest benchmark snapshot data that already powers inline profile cues should remain available in the main profile response.

### Compare

- Core compare can remain free while advanced compare features, premium metric packs, or AI commentary are capability-gated.
- Compare responses must indicate which features or sections are locked.
- Do not silently drop premium sections from compare state without metadata.

### Premium AI Artifacts

- Premium AI outputs should be treated as premium sections with the same access metadata pattern as any other locked section.
- The disclaimer and provenance requirements remain identical regardless of whether the artifact is free or premium.

For the launch analyst summary, the API contract should distinguish:

- `available`: return the analyst text plus disclaimer metadata
- `locked`: return paywall metadata and teaser copy only
- `unavailable`: no analyst artifact has been published for this school yet

## Web Technical Approach

Recommended feature ownership:

```text
apps/web/src/features/auth/
apps/web/src/features/premium-access/
apps/web/src/features/compare/
apps/web/src/features/school-profile/
apps/web/src/features/schools-search/
```

Recommended web responsibilities:

- central session state loader in app shell
- paywall banner or locked-section components owned by `premium-access`
- typed API calls for session, account access, and checkout creation
- post-purchase refresh or polling flow against Civitas endpoints, not optimistic local unlocks

Concrete web implementation guidance:

- `apps/web/src/app/RootLayout.tsx`
  - load current session once on shell boot
  - expose an auth or session context to descendant features
- `apps/web/src/features/auth/`
  - own the session loader hook, sign-in start mutation, sign-out mutation, and post-callback refresh
- `apps/web/src/features/premium-access/`
  - own locked-section panels, upgrade CTA wiring, paywall copy mapping, and account-status view-model mapping
- `apps/web/src/features/school-profile/`
  - map the new typed analyst and benchmark-dashboard section states into UI components
  - stop interpreting `null` premium fields as both "locked" and "not published"
  - stop eager-loading the premium dashboard route during the baseline profile boot path unless the user opens the drill-down or already has access
- `apps/web/src/api/client.ts`
  - make access-sensitive caching session-aware
  - expose a cache-clear helper that runs after sign-in, sign-out, or successful upgrade reconciliation
  - set credentials behavior explicitly if deployment uses a separate API origin

Recommended initial web routes:

- `/account`
- `/account/upgrade`
- a dedicated benchmark drill-down route such as `/schools/:urn/benchmark-dashboard` if the premium dashboard is a full-page experience rather than an in-page drawer

## Caching And Consistency Rules

The current web API client caches profile and trends responses by URL. Once access becomes user-specific, that is no longer sufficient.

Implementation planning must therefore include one of these strategies:

1. make cache keys include an access-state fingerprint
2. bypass cache on premium-sensitive routes
3. clear premium-sensitive caches whenever session or account-access state changes

Without this, a newly upgraded user may continue seeing a stale free baseline, or a signed-out browser may reuse a premium response.

Recommended implementation default:

- maintain a session or access epoch in the auth feature state
- include that epoch in cache keys for premium-sensitive GET routes, or clear those caches whenever the epoch changes
- treat profile, dashboard, compare-plus, and future premium AI endpoints as access-sensitive from day one

## Guardrails

- Premium enforcement must happen server-side.
- Free and paid states must remain understandable to the user.
- Paywall copy should explain what unlocks without overstating unsupported metrics.
- Frontend must not decide premium status from provider redirects or browser storage.
- `10G-premium-access-matrix.md` is the product source of truth for what each route or section requires.
- Locked-state UI must not reuse the same copy path as genuinely unavailable or unpublished content.
- Mutation endpoints such as checkout creation may use normal auth status codes, but public read routes should keep the `200` plus typed-access-metadata pattern.

## Acceptance Criteria

- Free users cannot access protected data or premium features through API or UI loopholes.
- Premium users receive the unlocked data set immediately after backend reconciliation and cache refresh.
- Search, profile, trends, compare, and premium AI surfaces render a consistent paywall model where relevant.
- OpenAPI-derived frontend types remain the source of truth for access metadata.
