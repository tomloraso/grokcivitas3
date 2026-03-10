# 10E - Premium API Boundaries And Web Paywall

## Goal

Wire feature-tier premium access into the product surface by enforcing backend data boundaries and adding a clear, typed paywall experience in the web app.

This deliverable is where the premium model becomes visible to users. It must stay contract-driven and should not move access policy into the frontend.

## Scope

### Backend

- protect premium-only sections and workflow features across profile, compare, and premium AI surfaces
- return the allowed free subset when the user lacks the required entitlement
- expose access state and paywall-relevant metadata through Civitas API schemas
- provide account-facing endpoints for current premium access state

### Frontend

- sign-in and upgrade entry points
- locked-state and preview-state rendering
- compare teaser modal and direct locked-route handling
- post-purchase refresh flow that reflects reconciled backend state
- account view for current premium state if needed for purchase recovery and clarity

Phase 10 premium enforcement in this document is limited to three launch surfaces:

1. AI analyst
2. compare
3. neighbourhood context

Benchmark context remains free in this phase, including inline benchmark cues and the benchmark dashboard drill-down.

## Current Implementation Snapshot

This is the implementation baseline the premium plan must actually land on.

| Concern | Current implementation | Phase 10 implication |
|---|---|---|
| Session transport | `SessionResponse` currently carries auth state, user, expiry, and anonymous reason only. | The shell cannot currently render premium status or invalidate caches on entitlement changes. |
| Profile summaries | `GET /api/v1/schools/{urn}` currently exposes `overview_text` and `analyst_text` as plain nullable strings end to end. | The analyst surface cannot distinguish `locked` from `unavailable`; null means too many things. |
| Profile area context | `GET /api/v1/schools/{urn}` currently exposes `area_context` directly as a free baseline payload. | Neighbourhood context cannot currently be premium without a typed wrapper that separates `locked` from missing data. |
| Compare route | The existing compare API and web route assume compare is fully available. | Compare needs a premium-aware locked response shape and locked web state before the paywall can ship safely. |
| Contract enforcement | `apps/backend/src/civitas/api/contract_checks.py` currently asserts the legacy profile fields. | Contract checks must change in the same slice as the schema change; otherwise the new OpenAPI contract will be blocked. |
| Web cache keys | `apps/web/src/api/client.ts` currently caches profile, compare, trends, and dashboard responses by method + URL only. | Upgrade and sign-out state cannot safely share those keys once access becomes user-specific. |
| Auth provider | `apps/web/src/features/auth/AuthProvider.tsx` clears caches only when the mapped auth session changes. | It needs to react to access-state changes as well, not only anonymous vs authenticated transitions. |
| Header chrome | `SiteHeader` currently knows about account email and sign-in state only. | Premium status styling has no current data path into the shell. |

## Intended API Contract Strategy

### Public Read Routes Should Stay Readable

For public research routes, prefer:

- `200` with free-baseline payload plus access metadata

Over:

- `403` plus no useful response body

Reason:

- the product experience needs to show users what exists before purchase
- the UI still needs contract-stable paywall copy and locked-section state
- profile navigation should not degrade into generic error handling

### Access Metadata Shape

Each premium-sensitive response should expose a typed access block that can answer:

- is the user anonymous, signed in, or premium-entitled?
- is this response a free baseline or does it include premium data?
- what portion is locked?
- which upgrade target or premium product is relevant?

Implementation-aligned recommendation:

- keep `/api/v1/session` as the app-shell boot payload and extend it with the lightweight access fields the shell needs immediately, specifically `account_access_state`, `capability_keys`, and `access_epoch`
- keep richer product, billing, and renewal detail in an authenticated account endpoint such as `GET /api/v1/account/access`
- this preserves the current `AuthProvider` as the central boot loader rather than forcing a second mandatory app-shell fetch

Recommended section-state enum:

- `available`
- `locked`
- `unavailable`

Use `locked` when a premium surface exists but the viewer lacks access. Use `unavailable` when the artefact is not published, not supported, or absent for product reasons.

## Surface-Specific Behavior

The exact rules come from `10G-premium-access-matrix.md`. This document defines the enforcement shape.

### Search

- Search remains free at the route level.
- Compare entry points in search remain visible, but free viewers should hit a locked action state or teaser modal instead of entering the compare workflow.

### Profile

- Free users still see school identity and approved free sections.
- Premium-only sections should be wrapped in typed `available`, `locked`, or `unavailable` state.
- Section-level access decisions should be driven by named capabilities, not by one giant route-wide premium flag.

Recommended contract changes:

- `GET /api/v1/schools/{urn}`
  - keep the free baseline fields already used by the profile page
  - replace the current raw nullable `analyst_text` field with a typed `analyst` section wrapper
  - wrap neighbourhood context in its own premium-aware `neighbourhood` section rather than exposing `area_context` as an always-free flat payload
  - keep the free overview field unchanged unless a shared wrapper design clearly reduces total churn

For the launch analyst summary, the API contract should distinguish:

- `available`: return the analyst text plus disclaimer metadata
- `locked`: return `teaser_text` (first 2-3 sentences of the analyst text) plus paywall metadata including the school name for contextual CTA rendering
- `unavailable`: no analyst artefact has been published for this school yet

For the launch neighbourhood section, the API contract should distinguish:

- `available`: return the full deprivation, crime, and house-price payload
- `locked`: return a short `teaser_text` or `teaser_payload` plus paywall metadata including the school name for contextual CTA rendering
- `unavailable`: no neighbourhood artefact exists for this school

The backend must never send the full premium payload to unauthorized viewers. The teaser fields are deliberately limited preview content designed for the premium-preview frontend pattern.

### Compare

- Compare is a premium workflow in the launch bundle.
- Compare entry points must stay visible so the value is obvious before purchase.
- The compare API and direct compare route must still enforce access server-side.

Recommended compare behavior:

- the compare endpoint returns full compare data only when the viewer has `premium_comparison`
- when locked, the endpoint returns a typed locked response with requested school context and paywall metadata rather than a generic hard failure
- search, profile, and results-table compare actions should open a teaser modal or locked affordance for free viewers
- a direct visit to the compare route should render a locked page state rather than a broken route
- in the current codebase, keep this on the existing `GET /api/v1/schools/compare` route and current `routes.py` module rather than inventing a parallel compare route tree

### Trends And Benchmark Dashboard

- Baseline trends and benchmark context remain free in the Phase 10 launch bundle.
- Do not make the benchmark dashboard the paywall anchor in this slice.

## Migration Sequence Aligned To Current Codebase

1. Extend the shell session contract before touching paywall UI.
   - Update backend auth schemas and DTOs to carry lightweight access state and `access_epoch`.
   - Keep `CurrentSessionDto` as auth-owned, and compose access metadata into the API response inside the auth route boundary rather than moving billing or entitlement logic into the identity slice.
   - Update `apps/web/src/features/auth/types.ts` and `apps/web/src/features/auth/AuthProvider.tsx` so the existing auth provider can propagate premium status into the shell and cache layer.
2. Change the profile contract only where the premium boundary actually exists.
   - Update backend school-profile DTOs and schemas so the analyst surface becomes a typed section wrapper.
   - Wrap neighbourhood context in a second premium-aware section contract.
   - Keep the free overview field unchanged unless a shared wrapper design is measurably simpler.
   - Update `apps/backend/src/civitas/api/contract_checks.py` in the same slice.
   - Keep route ownership in the current `apps/backend/src/civitas/api/routes.py` module, but move any large presentation mapping into helper functions if needed to avoid further bloating the route file.
3. Make compare premium-aware without relying on button-level guards.
   - Update compare DTOs, schemas, and route handlers so the current full compare payload becomes the `available` branch of a premium-aware response.
   - Return a `locked` compare payload with paywall metadata when the viewer lacks `premium_comparison`.
   - Keep access decisions in backend application code by extending the compare/profile use-case seam or adding application-level wrappers; do not encode capability checks directly in React or as route-only conditionals.
4. Make access-sensitive caching access-epoch-aware.
   - Update `apps/web/src/api/client.ts` so profile and compare cache keys vary by access epoch, or are cleared whenever the access epoch changes.
   - Treat profile and compare routes as access-sensitive from day one.
5. Add a dedicated premium-access slice instead of scattering paywall logic.
   - Create `apps/web/src/features/premium-access/` for shared preview gating, CTA copy mapping, upgrade entry points, and compare teaser modal behavior.
   - Keep school-profile and compare as consumers, not owners, of paywall mechanics.
6. Add premium-aware routes and shell chrome last.
   - Update routes, path helpers, root layout, and `SiteHeader` for `/account`, `/account/upgrade`, and the locked compare state.

## Web Technical Approach

Recommended feature ownership:

```text
apps/web/src/features/auth/
apps/web/src/features/premium-access/
apps/web/src/features/school-compare/
apps/web/src/features/school-profile/
apps/web/src/features/schools-search/
```

Implementation note for the current repo:

- `apps/web/src/app/routes.tsx` is the route registry today, so `/account` and `/account/upgrade` should be added there rather than introducing a separate pages router abstraction first.
- `apps/web/src/components/layout/SiteHeader.tsx` already owns shell account chrome, so premium ambient status should flow through its existing props rather than a second shell provider.

Recommended web responsibilities:

- central session state loader in app shell
- premium preview gate component and contextual CTA wiring owned by `premium-access`
- compare teaser modal or locked action state owned by `premium-access` and consumed by compare entry points
- typed API calls for session, account access, and checkout creation
- post-purchase refresh or polling flow against Civitas endpoints, not optimistic local unlocks
- ambient premium styling driven by session or access context from auth feature

### Premium Preview Gate Component

The frontend needs a single shared premium UX primitive for section-level premium content. Recommended component name: `PremiumPreviewGate`.

Responsibilities:

- accept children, capability key, school name, section state, and preview variant
- when `state=available`: render children at full density with a thin brand-purple accent border
- when `state=locked` for narrative text: render teaser content clearly visible, apply a progressive CSS gradient mask, and overlay an inline contextual CTA card
- when `state=locked` for neighbourhood context: render the teaser line or section framing, then a blur or fade treatment with an inline contextual CTA overlay
- when `state=unavailable`: render nothing or a minimal "not available" notice

Compare uses a related locked-action treatment rather than a blur block:

- keep the compare button or entry point visible
- show a lock icon and open a contextual teaser modal when the viewer lacks access
- keep the direct compare route aligned with the same paywall copy and product target

CTA copy must be school-specific and action-oriented. Avoid generic copy like "Unlock Premium" or "Upgrade Now".

### Premium Ambient Styling

When the session context indicates active premium access:

- `SiteHeader` renders the word `Premium` near the account email in brand purple
- `PremiumPreviewGate` in `available` state renders a thin brand-purple accent border on the section container
- compare entry points render as normal enabled workflow actions for entitled users

Do not use badges, gold palettes, or celebratory unlock animations.

## Caching And Consistency Rules

The current web API client caches profile and compare responses by URL. Once access becomes user-specific, that is no longer sufficient.

Recommended implementation default:

- maintain a session or access epoch in the auth feature state
- include that epoch in cache keys for premium-sensitive GET routes, or clear those caches whenever the epoch changes
- treat profile and compare endpoints as access-sensitive from day one

Without this, a newly upgraded user may continue seeing stale locked state, or a signed-out browser may reuse a premium response.

## Guardrails

- Premium enforcement must happen server-side.
- Free and paid states must remain understandable to the user.
- Paywall copy should explain what unlocks without overstating unsupported metrics.
- Frontend must not decide premium status from provider redirects or browser storage.
- `10G-premium-access-matrix.md` is the product source of truth for what each route or section requires.
- Locked-state UI must not reuse the same copy path as genuinely unavailable or unpublished content.
- Mutation endpoints such as checkout creation may use normal auth status codes, but public read routes should keep the `200` plus typed-access-metadata pattern.
- All user-facing premium copy must use `Premium`, never `Pro`. `Pro` is reserved for a future B2B tier.
- Compare entry points should stay visible even when locked; do not hide the workflow entirely for free viewers.
- Premium copy must not imply hidden facts or advice. Paid access is deeper interpretation and workflow support, not privileged truth.

## Acceptance Criteria

- Free users cannot access protected analyst, neighbourhood, or compare data through API or UI loopholes.
- Premium users receive the unlocked data set immediately after backend reconciliation and cache refresh.
- Profile, compare, and premium AI surfaces render a consistent paywall model where relevant.
- OpenAPI-derived frontend types remain the source of truth for access metadata.
- Compare entry points remain visible in search or profile journeys even when the workflow is locked.
