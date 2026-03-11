# 14A - Account Favourites Foundation

## Goal

Add a first-class backend model for school favourites so Civitas can support a saved research library without mixing that state into compare, billing, or browser-only storage.

## Solution Fit With Current Codebase

This slice should extend the existing backend seams, not create a separate account subsystem.

- Identity and session ownership already exist under `domain/identity`, `application/identity`, and the Civitas session routes.
- Search currently reads from the `school_search_summary` projection through `PostgresSchoolSearchRepository`.
- School profile responses are assembled through `GetSchoolProfileUseCase`.
- The web shell resolves the current user through `/api/v1/session`, so favourites should key off the internal Civitas `user_id`, never off provider subject IDs or frontend-only state.

## Scope

### Domain Scope

- account-owned saved schools
- optional entitlement guard for `premium_favourites` if product keeps favourites paid
- stable saved-state queries for search, profile, and account surfaces
- audit-safe create or remove behavior

### Persistence Scope

- active-state table for saved schools
- append-only event history for save and remove actions
- uniqueness rules preventing duplicate active saves for the same user and school
- timestamps needed for latest-saved ordering and support visibility

## Intended Backend Feature Boundary

Create a dedicated backend feature slice:

```text
civitas/
  domain/favourites/
    models.py
    services.py                 # optional
  application/favourites/
    use_cases.py
    dto.py
    ports/
      favourite_repository.py
      favourite_event_repository.py
  infrastructure/persistence/
    postgres_favourite_repository.py
    postgres_favourite_event_repository.py
  api/
    schemas/favourites.py
    favourites_routes.py
```

Keep favourites separate from:

- `identity`: authentication and session ownership
- `school_compare`: browser shortlist workflow
- `schools` and `school_profiles`: public read models that will only be enriched with viewer-specific saved-state

## Intended Model

Recommended concepts:

- `SavedSchool`
- `SavedSchoolState`
- `SavedSchoolEvent`
- `SaveSchoolUseCase`
- `RemoveSavedSchoolUseCase`
- `ListSavedSchoolsUseCase`
- `GetSavedSchoolStatesUseCase`

Recommended minimum fields on the active-state row:

- internal saved-school ID
- `user_id`
- `school_urn`
- `created_at`

Recommended event fields:

- internal event ID
- `saved_school_id` or `(user_id, school_urn)` reference
- `event_type` with `saved` and `removed`
- `occurred_at`
- optional `actor_type` or `reason_code` if support needs later expand

Recommended constraints:

- unique active save per `(user_id, school_urn)` on `saved_schools`
- index supporting latest-saved-first account views on `(user_id, created_at DESC)`
- foreign key from `saved_schools.user_id` to `users.id`
- foreign key from `saved_schools.school_urn` to `schools.urn`

## Why Explicit Save And Remove Beats Toggle

Do not make the backend contract hinge on a generic toggle mutation.

- `PUT /.../favourites/{urn}` is idempotent and safe to retry.
- `DELETE /.../favourites/{urn}` is idempotent and safe to retry.
- Explicit actions make audit events, race handling, and client rollback logic clearer.
- The UI can still render one button that flips between save and remove, but the transport contract should remain explicit.

## API Contract Strategy

Expose one dedicated account route plus viewer-aware saved-state on the read routes users already visit.

Recommended routes:

- `GET /api/v1/account/favourites`
- `PUT /api/v1/account/favourites/{urn}`
- `DELETE /api/v1/account/favourites/{urn}`

Recommended read-contract additions:

- `GET /api/v1/schools`
  - each result row carries a `saved_state` block
- `GET /api/v1/schools/search`
  - each result row carries the same `saved_state` block
- `GET /api/v1/schools/{urn}`
  - the profile response carries the same `saved_state` block for that school

Recommended `saved_state` shape:

- `status`: `saved`, `not_saved`, `requires_auth`, or `locked`
- `saved_at`: populated when `status=saved`
- `capability_key`: populated when `status=locked`
- `reason_code`: optional for account-library or CTA mapping

This keeps search and profile expressive without forcing the web app to make a second per-school favourites request after every read.

## Viewer Context Integration

Current school routes are anonymous-only from an application perspective. Phase 13 should make them viewer-aware through a shared API dependency.

Recommended backend additions:

- add an optional current-user dependency in `apps/backend/src/civitas/api/dependencies.py`
- resolve the current session through the existing session cookie and `GetCurrentSessionUseCase`
- pass `viewer_user_id: UUID | None` into:
  - `SearchSchoolsByPostcodeUseCase.execute(...)`
  - `SearchSchoolsByNameUseCase.execute(...)`
  - `GetSchoolProfileUseCase.execute(...)`

Do not duplicate session resolution logic inside each route handler.

## Read-Model Integration

### Search

- Extend the postcode search repository query with an optional left join from `school_search_summary` to `saved_schools` filtered by `viewer_user_id`.
- Keep the search route public and readable; anonymous viewers should get `saved_state.status=requires_auth`.
- Do not add an N+1 follow-up repository call per school card.

### Name search

- Extend the name-search read path so `GET /api/v1/schools/search` returns the same `saved_state` contract as postcode search.
- Keep the route public and readable; anonymous viewers should get `saved_state.status=requires_auth`.
- Avoid an N+1 favourite-state lookup per returned school row.

### Profile

- Add one favourite-state lookup to the profile use case based on the current `viewer_user_id` and `urn`.
- Keep the free profile payload unchanged except for the added `saved_state` contract.

### Account Library

- Back the library route with summary-level school data, not full profile hydration.
- Prefer reusing the existing `school_search_summary` projection plus the `saved_schools.created_at` timestamp for ordering.
- This keeps the library aligned with the same school identity and headline signals users already see in search.

## Access Decision

- The phase must support either of these product policies without redesign:
  - favourites are a signed-in helper available to every authenticated user
  - favourites require the `premium_favourites` capability
- The default implementation path should be the signed-in helper model.
- If product flips favourites to paid later, the access decision belongs in the existing Phase 10 access slice, not in route handlers or frontend storage rules.

Recommended access behavior:

- anonymous viewer
  - search or profile returns `saved_state.status=requires_auth`
  - account-library route returns an auth-required response shape or standard authenticated-route behavior
- authenticated viewer without required capability
  - search or profile returns `saved_state.status=locked`
  - account-library route returns a typed locked state with paywall metadata
- authenticated entitled viewer
  - save, remove, and list work normally

## Guardrails

- Saving a school must never depend on compare state.
- Browser local storage is not the source of truth for favourites.
- API contracts must distinguish `saved`, `not_saved`, `requires_auth`, and `locked` clearly when needed.
- If favourites are premium-scoped, locked save actions should use the same paywall metadata patterns introduced in Phase 10.
- Do not put favourites data into `/api/v1/session`; session remains shell bootstrap state, not an account-library payload.
- Do not hydrate full school profiles just to render the account library.

## Concrete Implementation Touchpoints

The implementation is expected to touch these existing seams:

- `apps/backend/src/civitas/api/dependencies.py`
- `apps/backend/src/civitas/api/main.py`
- `apps/backend/src/civitas/api/routes.py`
- `apps/backend/src/civitas/application/schools/use_cases.py`
- `apps/backend/src/civitas/application/school_profiles/use_cases.py`
- `apps/backend/src/civitas/infrastructure/persistence/postgres_school_search_repository.py`
- `apps/backend/alembic/versions/`

## Acceptance Criteria

- Backend can save, list, and remove favourites deterministically through explicit idempotent actions.
- Search and profile contracts expose the same viewer-specific saved-state model.
- Postcode search and name-search results expose the same viewer-specific saved-state model.
- The account library is backed by a lightweight summary read path rather than full profile loading.
- Access policy for favourites can change later without redesigning persistence or API shape.
