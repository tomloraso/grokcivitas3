# School Compare

## Overview

Phase 9 adds a dedicated multi-school compare flow across backend and web:

- backend contract: `GET /api/v1/schools/compare?urns=<urn1>,<urn2>,...`
- frontend route: `/compare?urns=<urn1>,<urn2>,...`

The backend OpenAPI contract is the source of truth for aligned compare rows. The web app augments that payload only with client-side selection context such as search-derived `distance_miles`.

## Backend Shape

The compare response is split into two top-level blocks:

- `schools`: ordered column headers for each selected URN
- `sections`: ordered compare sections containing aligned metric rows and per-school cells

Each compare cell carries:

- formatted display text
- raw numeric value where relevant
- year or snapshot metadata
- availability state
- completeness state
- benchmark context when supported

Phase 9 compare rows are assembled in the application layer from existing school profile and benchmark repositories. Request order is preserved in the final payload.

## Frontend State

Compare selection lives in the app shell via `CompareSelectionContext`.

Rules:

- compare supports two to four schools
- duplicate schools are rejected
- local storage preserves selection across route changes
- URL query order is authoritative on the compare route
- storage is only a fallback when `/compare` is opened without explicit `urns`

When the compare route loads successfully, the web app refreshes local compare selection metadata from the canonical API school headers while preserving any existing distance context captured from search.

## UX States

The compare page renders explicit states for:

- loading
- empty
- underfilled
- error
- ready

The ready state shows:

- a selected-school header strip with remove actions
- sectioned compare matrices with sticky metric labels and school headers
- profile links that carry `fromCompare` route state so the profile page can offer a return affordance
