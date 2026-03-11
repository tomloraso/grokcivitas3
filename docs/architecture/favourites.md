# Saved Schools

Phase 13 adds account-owned saved schools across backend and web.

## Scope

- save or unsave a school from:
  - postcode results
  - name-search results
  - school profile header
- browse saved schools on `/account/favourites`
- keep compare selection separate from saved schools

## Contract Surface

Saved-state is now part of the main school read contracts:

- `GET /api/v1/schools`
- `GET /api/v1/schools/search`
- `GET /api/v1/schools/{urn}`

The shared contract is `saved_state` with these states:

- `saved`
- `not_saved`
- `requires_auth`
- `locked`

The account-owned library lives on:

- `GET /api/v1/account/favourites`
- `PUT /api/v1/account/favourites/{urn}`
- `DELETE /api/v1/account/favourites/{urn}`

Backend OpenAPI remains the source of truth. Frontend consumes the generated contracts through `apps/web/src/api/generated-types.ts` and `apps/web/src/api/types.ts`.

## Ownership

Backend ownership:

- dedicated favourites application slice
- Postgres persistence for current saved rows and save/remove audit events
- viewer-aware `saved_state` projection layered onto search and profile reads

Frontend ownership:

- `apps/web/src/features/favourites/*` owns saved-school UI, mapping, and account-library loading
- `apps/web/src/features/schools-search/*` injects save actions into result cards and postcode analysis results
- `apps/web/src/features/school-profile/*` injects save actions into the profile header

## Web State Rules

- Save and remove mutations call `resetApiRequestCache()` after success.
- Search results keep local saved-state overrides so the same school stays in sync across the card list and postcode analysis overlay without a full reload.
- Profile keeps a local saved-state override so background trends/dashboard hydration does not revert the header button to stale state.
- The account library removes a school from the visible list immediately after a successful unsave mutation.

## Current Product Policy

- Anonymous users can see the save affordance but are routed to sign-in.
- Signed-in users can use saved schools without Premium gating.
- The account library is an account route, not a compare shortlist or client-only bookmark cache.

## Guardrails

- Do not infer saved state from button text or local compare state.
- Do not move saved schools into `CompareSelectionContext`.
- Do not bypass the typed API client from feature code.
- Keep saved-school summaries aligned to `school_search_summary` style data rather than building a separate library payload shape on the web.
