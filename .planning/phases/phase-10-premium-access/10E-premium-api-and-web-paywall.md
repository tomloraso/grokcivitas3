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

## Current Implementation Snapshot

This is the implementation baseline the premium plan must actually land on.

| Concern | Current implementation | Phase 10 implication |
|---|---|---|
| Session transport | `SessionResponse` currently carries auth state, user, expiry, and anonymous reason only. | The shell cannot currently render premium status or invalidate caches on entitlement changes. |
| Profile summaries | `GET /api/v1/schools/{urn}` currently exposes `overview_text` and `analyst_text` as plain nullable strings end to end. | The analyst surface cannot distinguish `locked` from `unavailable`; null means too many things. |
| Dashboard route | `GET /api/v1/schools/{urn}/trends/dashboard` currently returns either the full dashboard payload or an error. | The route needs an explicit `locked` response shape before any paywall UI can exist. |
| Contract enforcement | `apps/backend/src/civitas/api/contract_checks.py` currently asserts the legacy profile fields. | Contract checks must change in the same slice as the schema change; otherwise the new OpenAPI contract will be blocked. |
| Web cache keys | `apps/web/src/api/client.ts` currently caches profile, compare, trends, and dashboard responses by method + URL only. | Upgrade and sign-out state cannot safely share those keys once access becomes user-specific. |
| Auth provider | `apps/web/src/features/auth/AuthProvider.tsx` clears caches only when the mapped auth session changes. | It needs to react to access-state changes as well, not only anonymous vs authenticated transitions. |
| Profile boot path | `apps/web/src/features/school-profile/hooks/useSchoolProfile.ts` currently loads profile first, then background-loads trends and dashboard. | The premium dashboard must stop hydrating on the free profile boot path. |
| Benchmark view model | `apps/web/src/features/school-profile/mappers/profileMapper.ts` merges free snapshot benchmarks and dashboard data into one `benchmarkDashboard` VM consumed by free sections. | That abstraction is too coupled for a premium boundary. Free inline benchmark mapping and premium drill-down mapping must separate. |
| Header chrome | `SiteHeader` currently knows about account email and sign-in state only. | Premium status styling has no current data path into the shell. |
| Routes | Current web routes cover `/sign-in`, `/compare`, and `/schools/:urn`. | Account and premium drill-down routes still need to be added. |

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

Implementation-aligned recommendation:

- keep `/api/v1/session` as the app-shell boot payload and extend it with the lightweight access fields the shell needs immediately, specifically `account_access_state`, `capability_keys`, and `access_epoch`
- keep richer product, billing, and renewal detail in account-facing endpoints such as `AccountAccessResponse`
- this preserves the current `AuthProvider` as the central boot loader rather than forcing a second mandatory app-shell fetch

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
  - replace the current raw nullable `analyst_text` field with a typed section wrapper; keep `overview_text` free unless a shared summary-wrapper design clearly reduces total churn
  - add a top-level access block or section-level access blocks describing which premium surfaces are locked
- `GET /api/v1/schools/{urn}/trends/dashboard`
  - become an explicitly premium-aware response rather than returning the current full dashboard schema to every viewer
  - return `state=locked` plus paywall metadata when the viewer lacks `premium_benchmark_dashboard`
  - return full metric sections only when unlocked

The free profile route should not depend on the dashboard endpoint for its baseline benchmark rendering path. Latest benchmark snapshot data that already powers inline profile cues should remain available in the main profile response.

Current-code implication:

- the existing web profile mapper currently folds `profile.benchmarks` and `/trends/dashboard` into the same `benchmarkDashboard` view model
- Phase 10 should split that into:
  - a free inline benchmark mapping sourced from `GET /api/v1/schools/{urn}` only
  - a premium dashboard preview/full-response mapping sourced from the premium-aware dashboard route
- do not keep one merged benchmark object serving both concerns

### Compare

- Core compare can remain free while advanced compare features, premium metric packs, or AI commentary are capability-gated.
- Compare responses must indicate which features or sections are locked.
- Do not silently drop premium sections from compare state without metadata.

### Premium AI Artifacts

- Premium AI outputs should be treated as premium sections with the same access metadata pattern as any other locked section.
- The disclaimer and provenance requirements remain identical regardless of whether the artifact is free or premium.

For the launch analyst summary, the API contract should distinguish:

- `available`: return the analyst text plus disclaimer metadata
- `locked`: return `teaser_text` (first 2-3 sentences of the analyst text) plus paywall metadata including the school name for contextual CTA rendering
- `unavailable`: no analyst artifact has been published for this school yet

For the launch benchmark dashboard, the API contract should distinguish:

- `available`: return full metric sections, charts, and drill-down data
- `locked`: return `teaser_payload` (layout structure plus limited real preview content) plus paywall metadata including the school name for contextual CTA rendering
- `unavailable`: no benchmark data exists for this school

The backend must never send the full premium payload to unauthorized viewers. The `teaser_text` and `teaser_payload` fields are deliberately truncated preview excerpts designed for the premium-preview frontend pattern.

For the benchmark dashboard specifically, `teaser_payload` should include limited real preview content rather than a fully blurred fake dashboard. The frontend should show structure plus sample rows or sample values, then a fade or lock boundary.

## Migration Sequence Aligned To Current Codebase

1. Extend the shell session contract before touching paywall UI.
   - Update `apps/backend/src/civitas/api/schemas/auth.py`, `apps/backend/src/civitas/application/identity/dto.py`, and `apps/backend/src/civitas/api/auth_routes.py` to carry lightweight access state and `access_epoch`.
   - Update `apps/web/src/features/auth/types.ts` and `apps/web/src/features/auth/AuthProvider.tsx` so the existing auth provider can propagate premium status into the shell and cache layer.
2. Change the profile contract only where the premium boundary actually exists.
   - Update `apps/backend/src/civitas/application/school_profiles/dto.py`, `apps/backend/src/civitas/api/schemas/school_profiles.py`, and `apps/backend/src/civitas/api/routes.py` so the analyst surface becomes a typed section wrapper with `available`, `locked`, and `unavailable`.
   - Keep the free overview field unchanged unless a shared summary-wrapper design is measurably simpler.
   - Update `apps/backend/src/civitas/api/contract_checks.py` in the same slice.
3. Make the dashboard route premium-aware without destabilizing free profile rendering.
   - Update `apps/backend/src/civitas/api/schemas/school_trends.py` and the dashboard route/use case so the current full dashboard payload becomes the `available` branch of a premium-aware response.
   - Add `teaser_payload` support for locked viewers and preserve `unavailable` when benchmark data does not exist.
4. Split the current web benchmark abstraction.
   - Update `apps/web/src/features/school-profile/mappers/profileMapper.ts`, `apps/web/src/features/school-profile/types.ts`, and the owning section components so free inline benchmark slots come from `profile.benchmarks` only.
   - Do not keep using the current merged `benchmarkDashboard` object for both free cards and premium drill-down state.
5. Remove dashboard hydration from the free profile boot path.
   - Update `apps/web/src/features/school-profile/hooks/useSchoolProfile.ts` so the baseline profile path loads profile and optional trends only.
   - This should align the hook with the existing `prefetchSchoolProfile()` behavior and tests, which already treat the dashboard as lazy.
6. Add a dedicated premium-access slice instead of scattering paywall logic.
   - Create `apps/web/src/features/premium-access/` for shared preview gating, CTA copy mapping, upgrade entry points, and account-access view-model mapping.
   - Keep school-profile and future dashboard routes as consumers, not owners, of paywall mechanics.
7. Add premium-aware routes and shell chrome last.
   - Update `apps/web/src/app/routes.tsx`, `apps/web/src/shared/routing/paths.ts`, `apps/web/src/app/RootLayout.tsx`, and `apps/web/src/components/layout/SiteHeader.tsx` for `/account`, `/account/upgrade`, and the benchmark dashboard route if it is full-page.
8. Regenerate contracts and then fix the tests that currently encode the free-all-the-way-through behavior.
   - Regenerate `apps/web/src/api/openapi.json`, `apps/web/src/api/generated-types.ts`, and `apps/web/src/api/types.ts`.
   - Update `apps/web/src/api/client.test.ts`, `apps/web/src/features/auth/AuthProvider.test.tsx`, and `apps/web/src/features/school-profile/school-profile.test.tsx`.

## Web Technical Approach

Recommended feature ownership:

```text
apps/web/src/features/auth/
apps/web/src/features/premium-access/
apps/web/src/features/benchmark-dashboard/
apps/web/src/features/school-compare/
apps/web/src/features/school-profile/
apps/web/src/features/schools-search/
```

Recommended web responsibilities:

- central session state loader in app shell
- premium preview gate component and contextual CTA wiring owned by `premium-access`
- typed API calls for session, account access, and checkout creation
- post-purchase refresh or polling flow against Civitas endpoints, not optimistic local unlocks
- ambient premium styling driven by session or access context from auth feature

### Premium Preview Gate Component

The frontend needs a single shared premium UX primitive. Recommended component name: `PremiumPreviewGate`.

Responsibilities:

- Accept children (the teaser content), capability key, school name, section state, and preview variant.
- When `state=available`: render children at full density with a thin brand-purple accent border (2px left border or top accent line).
- When `state=locked` for narrative text: render teaser content clearly visible, apply a progressive CSS gradient mask (clear to fully blurred over ~60px, then fully blurred), and overlay an inline contextual CTA card.
- When `state=locked` for structured benchmark preview: render real preview rows or sample values, then a fade or lock boundary with an inline contextual CTA card. Do not blur fabricated chart values or fake a full hidden dashboard.
- When `state=unavailable`: render nothing or a minimal "not available" notice. Do not show blur or CTA.
- CTA copy must be school-specific and action-oriented, derived from the school name included in the locked-section metadata. Examples: "Get the full analyst view for [School Name]" or "See how [School Name] compares across all benchmarks".
- Do not use generic copy like "Unlock Premium", "Upgrade Now", or "Go Premium".

This component lives in `apps/web/src/features/premium-access/` and is consumed by profile, dashboard, and future premium-aware feature slices.

### Premium Ambient Styling

When the session context indicates active premium access:

**Header indicator:**

- `SiteHeader` renders the word `Premium` in brand purple, Space Grotesk display typeface, small scale, near the account email. This is status, not advertising.
- Do not use `Pro`. `Pro` is reserved for a future B2B tier.

**Unlocked premium sections:**

- `PremiumPreviewGate` in `available` state renders a thin 2px brand-purple left border or top accent line on the section container.
- The section renders at full content density. The visual presence of richer content is itself the premium signal.
- No per-section `Premium` badges, lock/unlock icons, or unlock transitions.

**Upgrade reveal:**

- After successful backend reconciliation, show one explicit unlock moment: route or scroll to the newly unlocked surface and briefly highlight it once.
- After that, return to the ambient styling rules above.

**Design constraints:**

- No gold or separate premium color palette. The existing brand purple is the sole premium accent.
- No confetti, glow, gradient borders, or celebratory animations on unlock.
- Free and premium profile pages are structurally identical. Premium sections have content instead of blur. That is the entire difference.

Concrete web implementation guidance:

- `apps/web/src/app/RootLayout.tsx`
  - load current session once on shell boot
  - expose an auth or session context to descendant features
- `apps/web/src/features/auth/`
  - own the session loader hook, sign-in start mutation, sign-out mutation, post-callback refresh, and access-epoch propagation into the API client cache key state
- `apps/web/src/features/premium-access/`
  - own `PremiumPreviewGate` component, preview CSS utilities, contextual CTA card, paywall copy mapping, and account-status view-model mapping
  - CTA copy must use school name from locked-section metadata, not derive it from route params
- `apps/web/src/features/school-profile/`
  - map the new typed analyst section state into UI components
  - stop interpreting `null` premium fields as both "locked" and "not published"
  - stop eager-loading the premium dashboard route during the baseline profile boot path unless the user opens the drill-down or already has access
  - split the current merged benchmark mapping so free metric cards consume only the free profile payload
- `apps/web/src/features/benchmark-dashboard/`
  - own the dedicated premium dashboard route or drawer, including locked preview rendering and unlocked drill-down presentation
- `apps/web/src/api/client.ts`
  - make access-sensitive caching access-epoch-aware instead of URL-only
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

Recommended implementation default (frozen):

- maintain a session or access epoch in the auth feature state
- include that epoch in cache keys for premium-sensitive GET routes, or clear those caches whenever the epoch changes
- treat profile, dashboard, compare-plus, and future premium AI endpoints as access-sensitive from day one
- this is the locked-in strategy; do not reopen the decision during implementation

Implementation-aligned note:

- `apps/web/src/api/client.ts` currently builds cache keys as `method:url`
- Phase 10 should add a module-level access-epoch input to those keys for access-sensitive requests
- `AuthProvider` should push the latest access epoch into that client state whenever the shell session/access payload changes

## Guardrails

- Premium enforcement must happen server-side.
- Free and paid states must remain understandable to the user.
- Paywall copy should explain what unlocks without overstating unsupported metrics.
- Frontend must not decide premium status from provider redirects or browser storage.
- `10G-premium-access-matrix.md` is the product source of truth for what each route or section requires.
- Locked-state UI must not reuse the same copy path as genuinely unavailable or unpublished content.
- Mutation endpoints such as checkout creation may use normal auth status codes, but public read routes should keep the `200` plus typed-access-metadata pattern.
- All user-facing premium copy must use `Premium`, never `Pro`. `Pro` is reserved for a future B2B tier.
- CTA copy must be contextual and school-specific. Generic upgrade language is not acceptable.
- The premium-preview pattern requires backend support: locked responses must include `teaser_text` or `teaser_payload` fields. The frontend must not fabricate teaser content from cached or previous responses.
- Do not reuse the current merged `benchmarkDashboard` view model as both free inline benchmark data and premium dashboard state.
- Premium copy must not imply hidden facts or advice. Paid access is deeper interpretation of public evidence, not privileged truth.
- Structured dashboard previews must use real teaser payload only. Do not render blurred or fabricated chart values the backend never sent.

## Acceptance Criteria

- Free users cannot access protected data or premium features through API or UI loopholes.
- Premium users receive the unlocked data set immediately after backend reconciliation and cache refresh.
- Search, profile, trends, compare, and premium AI surfaces render a consistent paywall model where relevant.
- OpenAPI-derived frontend types remain the source of truth for access metadata.
- The free profile boot path does not call the premium dashboard route unless the user explicitly opens that premium surface.
