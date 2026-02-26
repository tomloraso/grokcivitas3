# Testing Guide

## Backend

- Tests live in `apps/backend/tests`.
- Run focused tests while iterating, then full suite:
  - `uv run --project apps/backend pytest apps/backend/tests/unit -q`
  - `uv run --project apps/backend pytest`
- Always run import-boundary test when moving modules:
  - `uv run --project apps/backend pytest apps/backend/tests/unit/test_import_boundaries.py`

## Web

- `cd apps/web && npm run test`
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run lint`

## CI gates

PRs must pass lint, typecheck, tests, and build.
