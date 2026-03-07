# 10E - Premium API Boundaries And Web Paywall

## Goal

Wire research-area entitlements into the product surface by enforcing backend data boundaries and adding a clear, typed paywall experience in the web app.

This deliverable is where the premium model becomes visible to users. It must stay contract-driven and should not move access policy into the frontend.

## Scope

### Backend

- protect premium-only search, profile, trends, dashboard, and compare data paths
- return the allowed free subset when no entitlement exists
- expose access state and paywall-relevant metadata through Civitas API schemas
- provide account-facing endpoints for active research-area unlocks

### Frontend

- sign-in and upgrade entry points
- locked-state and preview-state rendering
- post-purchase refresh flow that reflects reconciled backend state
- account view for active unlocks if needed for purchase recovery and clarity

## Intended API Contract Strategy

### Public Read Routes Should Stay Readable

For public research routes, prefer:

- `200` with preview payload plus access metadata

Over:

- `403` plus no useful response body

Reason:

- the product experience needs to show users what exists locally before purchase
- the UI still needs contract-stable paywall copy and counts
- public search and profile navigation should not degrade into error handling

### Access Metadata Shape

Each premium-sensitive response should expose a typed access block that can answer:

- is the user anonymous, signed in, or entitled?
- is this response a free preview or full premium data?
- what portion is locked?
- what research area is being offered for purchase?

Minimum fields to consider:

- `access_level`
- `requires_auth`
- `requires_purchase`
- `locked_sections`
- `preview_limit`
- `research_area`
- `available_products`

Exact schema names can evolve, but the contract should be explicit enough that web features do not infer state from missing fields alone.

## Surface-Specific Behavior

### Search

- Search response should expose total result count plus preview-visible count.
- Preview limit must come from backend configuration or product rules.
- Upgrade CTA should carry the normalized research-area parameters that checkout requires.

### Profile And Trends

- Free users should still see school identity and approved free sections.
- Premium-only sections should be omitted or marked locked with explicit metadata.
- The same access-decision service used for search should decide whether a school lies inside any active research area.

### Compare

- Compare responses must indicate which selected schools or metrics are locked.
- Do not silently drop locked schools from compare state.
- If compare ships before premium, this contract extension should layer onto the existing compare schema instead of creating a separate ad hoc endpoint.

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
- typed API calls for session, unlock listing, and checkout creation
- post-purchase refresh or polling flow against Civitas endpoints, not optimistic local unlocks

## Caching And Consistency Rules

The current web API client caches profile and trends responses by URL. Once access becomes user-specific, that is no longer sufficient.

Implementation planning must therefore include one of these strategies:

1. make cache keys include an access-state fingerprint
2. bypass cache on premium-sensitive routes
3. clear premium-sensitive caches whenever session or entitlement state changes

Without this, a newly paid user may continue seeing a stale free preview, or a signed-out browser may reuse a premium response.

## Guardrails

- Premium enforcement must happen server-side.
- Free and paid states must remain understandable to the user.
- Paywall copy should explain what unlocks without overstating unsupported metrics.
- Frontend must not decide entitlement status from provider redirects or browser storage.

## Acceptance Criteria

- Free users cannot access protected data through API or UI loopholes.
- Paid users receive the unlocked data set immediately after backend reconciliation and cache refresh.
- Search, profile, trends, and compare surfaces render a consistent paywall model where relevant.
- OpenAPI-derived frontend types remain the source of truth for access metadata.
