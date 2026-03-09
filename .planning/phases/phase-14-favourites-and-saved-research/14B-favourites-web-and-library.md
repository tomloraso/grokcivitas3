# 14B - Favourites Web And Library

## Goal

Expose favourites in the web app through clear saved-state actions and one account-owned library view.

## Scope

- save or unsave actions on school cards and profile pages
- account library route for saved schools
- clear empty, loading, locked, and error states
- no attempt to build a broader research workspace in this phase

## Solution Fit With Current Web Architecture

Phase 14 should extend the existing React ownership model rather than scatter save state across shared primitives.

- Network calls stay under `apps/web/src/api/*`.
- Session state remains bootstrapped through `apps/web/src/features/auth/AuthProvider.tsx`.
- Search already renders school-card actions through `ResultCard.actions`.
- Profile headers already expose an `actions` slot through `ProfileHeader`.
- Compare shortlist state currently lives in `CompareSelectionContext` and must remain separate from account-owned favourites.

## UX Requirements

- Save actions should appear where users already shortlist schools:
  - postcode results
  - school profile header
- The account library should support:
  - latest saved first ordering
  - navigation back to the school profile
  - remove from favourites
- If favourites remain premium-scoped:
  - render the action visibly
  - use a lock state or teaser modal rather than silently hiding the feature

## Technical Approach

- Keep network calls under `apps/web/src/api/*`.
- Own saved-state UI under a dedicated `features/favourites/` boundary.
- Reuse the Phase 10 session and access context for gating.
- Keep compare and favourites as separate concepts in UI state and route design.

Recommended feature ownership:

```text
apps/web/src/features/favourites/
  FavouritesLibraryFeature.tsx
  SaveSchoolButton.tsx
  hooks/
  mappers/
  types.ts
```

Recommended route additions:

- `/account/favourites`
- `paths.accountFavourites()`

Recommended API additions in `apps/web/src/api/client.ts`:

- `getAccountFavourites()`
- `saveFavourite(urn: string)`
- `removeFavourite(urn: string)`

## Contract And State Model

The web app should consume one shared `saved_state` contract mapped from backend OpenAPI types.

Recommended mapped states:

- `saved`
- `not_saved`
- `requires_auth`
- `locked`

Recommended web behavior per state:

- `saved`
  - render the active state of the button
  - account library includes the school
- `not_saved`
  - render the normal save affordance
- `requires_auth`
  - route the user into sign-in with `returnTo` set to the current page
- `locked`
  - show the lock state and Phase 10 paywall treatment if favourites remain premium-scoped

Do not infer saved state from the current button label or from stale local component state.

## Surface Integration

### Search

- Keep ownership in `features/schools-search/`.
- Inject the save control through `ResultCard.actions`; do not teach the shared `ResultCard` primitive about favourites directly.
- Use the `saved_state` returned by the postcode search response as the initial state for each card.

### Profile

- Keep ownership in `features/school-profile/`.
- Inject the save control through the existing `actions` prop on `ProfileHeader`.
- Use the profile response `saved_state` as the initial state for the header action.

### Header And Navigation

- Add a signed-in navigation path to the favourites library from the existing shell, likely through `SiteHeader`.
- Do not turn this phase into a broader account-dashboard redesign; one clear link is enough.

### Account Library

- Build one dedicated route component under `features/favourites/`.
- Reuse the same summary-style data language users already know from search:
  - school name
  - phase
  - type
  - postcode
  - latest Ofsted headline when available
  - academic headline metric when available
  - saved timestamp
- Latest saved first is the default ordering.

## Mutation And Cache Rules

Current API caching is lightweight and hand-rolled. Phase 14 must account for that explicitly.

- Profile responses are cached by URL only in `apps/web/src/api/client.ts`.
- Save and remove mutations must clear stale viewer-specific cache entries after success.
- A session change already clears caches through `AuthProvider`; save and remove flows must also invalidate cached profile responses in-session.
- If postcode search later becomes cached, its cache key must vary by viewer access or be cleared by favourites mutations as well.

Recommended default:

- call `resetApiRequestCache()` after successful save or remove
- then update local feature state from the mutation result or trigger a local refresh where needed

This is simpler and safer than trying to hand-edit cached profile payloads across multiple surfaces.

## UX Interaction Rules

- Show a pending state during save or remove mutations so repeated clicks do not issue duplicate requests.
- Optimistic button flips are acceptable only if failure rolls back and shows an explicit error.
- Anonymous clicks should preserve `returnTo` and land the user back on the same search or profile route after sign-in.
- Empty-library copy should point the user back to postcode search or school profiles, not to a generic account page.
- Locked-library copy, if favourites remain premium, should reuse the same `Premium` language and CTA patterns already planned in Phase 10.

## Guardrails

- Do not overload the compare button to behave like save.
- Do not invent a client-only favourites cache that can drift from backend state.
- Keep account library types derived from backend OpenAPI contracts.
- Do not move favourites state into `CompareSelectionContext`.
- Do not require a full page reload to see save-state changes reflected.
- Do not hide the save affordance entirely when the state is `requires_auth` or `locked`; the user should still see that the feature exists.

## Acceptance Criteria

- Users can save and unsave schools from the intended entry points.
- The account library reflects backend truth after refresh, sign-in, and sign-out.
- Locked favourites states, if configured, render clearly and consistently.
- Search cards, profile headers, and the account library all agree on the same saved-state contract.
