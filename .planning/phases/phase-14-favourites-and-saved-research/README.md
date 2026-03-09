# Phase 14 Design Index - Favourites And Saved Research

## Document Control

- Status: Planned, deferred post-launch candidate
- Last updated: 2026-03-09
- Phase owner: Product + Engineering
- Source phase: `.planning/phased-delivery.md`

## Purpose

This folder contains the follow-on planning for account-owned school favourites and a lightweight saved research library.

Phase 14 exists because favourites are valuable, but they are not required to prove the first premium launch. The launch bundle for Phase 10 therefore stays focused on identity, entitlements, checkout, AI analyst, compare, and neighbourhood gating. Favourites can be pulled forward only if launch blockers are already closed and capacity remains.

## Solution Grounding

Phase 14 should extend the solution that already exists in the repo, not invent a parallel account stack.

- Authentication and session transport already live behind Civitas-owned routes:
  - `POST /api/v1/auth/start`
  - `GET /api/v1/auth/callback`
  - `GET /api/v1/session`
  - `POST /api/v1/auth/signout`
- The web shell already loads current session state through `apps/web/src/features/auth/AuthProvider.tsx`.
- Postcode search already reads from the `school_search_summary` projection via `PostgresSchoolSearchRepository`; the saved-library route should reuse that same lightweight read model instead of hydrating full school profiles.
- Compare shortlist state currently lives in browser local storage under `CompareSelectionContext`. That pattern is compare-only and must not become the source of truth for favourites.
- Phase 10 already defines the capability-based access model. If favourites are later treated as paid, Phase 14 should consume that access slice and capability registry rather than add bespoke entitlement logic.

## Core Design Decisions

- Create a dedicated backend `favourites` feature slice. Do not fold favourites into `identity`, `schools`, or `school_compare`.
- Use explicit idempotent save and remove actions. Do not make the API contract depend on a generic toggle mutation.
- Embed viewer-specific `saved_state` into existing search and profile read contracts so search cards, profile headers, and the account library all agree on the same source of truth.
- Keep the account library narrow in scope: saved schools only, backed by lightweight summary data, not a general notes or workspace product.
- If product later keeps favourites premium-only, reuse Phase 10 access evaluation with a `premium_favourites` capability rather than redesigning persistence or frontend state.

## Delivery Model

Phase 14 is split into three deliverables:

1. `14A-account-favourites-foundation.md`
2. `14B-favourites-web-and-library.md`
3. `14C-phase-14-quality-gates.md`

## Execution Sequence

1. Complete `14A` first to freeze the domain model, access policy, and persistence contract.
2. Complete `14B` once the backend contract is agreed so search, profile, header, and account-library UI stay aligned.
3. Complete `14C` as final quality closeout and sign-off.

## Implementation Readiness Checklist

Before implementation starts, the phase should already assume these concrete extension points:

- Backend auth-aware read routes resolve the current viewer through a shared dependency in `apps/backend/src/civitas/api/dependencies.py` instead of reading cookies ad hoc in each handler.
- New favourites routes live in a dedicated router module, similar to `auth_routes.py`, and are registered in `apps/backend/src/civitas/api/main.py`.
- Search and profile use cases accept optional viewer context so saved-state can be mapped in the application layer rather than bolted onto route handlers.
- The web app owns favourites UI under `apps/web/src/features/favourites/`.
- Viewer-specific cache invalidation is handled deliberately in `apps/web/src/api/client.ts` and `apps/web/src/features/auth/AuthProvider.tsx`; save or remove actions must not leave stale saved-state behind.

## Definition Of Done

- Signed-in users can save and remove schools from a personal favourites library.
- If favourites remain premium-scoped, backend entitlement checks enforce that boundary consistently.
- Search, profile, and account surfaces all render the same saved-state model.
- Repository lint, tests, and critical saved-research journeys pass.
