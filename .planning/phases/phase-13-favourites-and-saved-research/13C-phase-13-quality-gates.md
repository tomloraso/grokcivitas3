# 13C - Phase 13 Quality Gates

## Goal

Define the evidence required before favourites and saved research are considered complete.

## Backend Verification

- domain and use-case tests for save, remove, duplicate-save, and list behavior
- repository integration tests for `saved_schools` and `saved_school_events`
- integration coverage for:
  - `GET /api/v1/account/favourites`
  - `PUT /api/v1/account/favourites/{urn}`
  - `DELETE /api/v1/account/favourites/{urn}`
  - viewer-aware `saved_state` on `GET /api/v1/schools`
  - viewer-aware `saved_state` on `GET /api/v1/schools/search`
  - viewer-aware `saved_state` on `GET /api/v1/schools/{urn}`
- access-evaluation tests if favourites are premium-scoped
- migration test or upgrade rehearsal proving the favourites schema applies cleanly from the current head

Recommended backend assertions:

- repeat `PUT` is idempotent
- repeat `DELETE` is idempotent
- anonymous read routes return `requires_auth` saved-state rather than leaking active saved rows
- one user cannot observe another user's saved-state
- account-library rows are ordered latest-saved first

## Frontend Verification

- component coverage for save or unsave actions on postcode search, name-search, and profile surfaces
- route or feature tests for the account library in:
  - empty
  - loading
  - error
  - locked
  - populated
- auth-aware tests proving `requires_auth` save actions send the user through sign-in with the correct `returnTo`
- cache invalidation tests proving profile saved-state refreshes correctly after save or remove
- sign-in and sign-out tests proving saved-state refreshes correctly when session context changes

## End-To-End Verification

- sign in
- save a school from postcode results
- save a school from name-search results
- confirm the same school renders as saved on its profile
- confirm it appears in the account library
- remove it from the account library
- confirm the saved state clears on the profile and in search on refresh

Playwright coverage should extend the existing critical-journey suite under `apps/web/e2e/` rather than rely on manual-only validation.

## Repository Gates

Run the canonical repository gates from the repo root:

- `make lint`
- `make test`

If the backend OpenAPI changes:

- regenerate frontend contract types with `cd apps/web && npm run generate:types`
- keep `apps/backend/src/civitas/api/contract_checks.py` aligned with the new contract shape if the saved-state fields are asserted there later

## Acceptance Criteria

- Favourites work consistently across the agreed saved-state surfaces.
- Saved-state access rules are enforced server-side.
- Repository lint, tests, and critical journeys pass in one repository state.
- The account library is backed by the agreed lightweight summary contract, not an accidental full-profile dependency.
