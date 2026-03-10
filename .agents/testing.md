# Testing Guide

## Backend

- Tests live in `apps/backend/tests`.
- Run focused tests while iterating, then full suite:
  - `uv run --project apps/backend pytest apps/backend/tests/unit -q`
  - `uv run --project apps/backend pytest`
- Backend integration tests are destructive. Prefer a dedicated `CIVITAS_TEST_DATABASE_URL`
  such as `postgresql+psycopg://app:app@localhost:5432/app_test`; do not run them against the
  same database the app uses.
- Integration-test DB selection must go through `AppSettings` in
  `civitas.infrastructure.config.settings`. Do not add fixture-local `.env` parsing or direct
  `os.getenv` fallbacks for new settings.
- If `CIVITAS_TEST_DATABASE_URL` is unset, backend integration tests only run when
  `CIVITAS_DATABASE_URL` already points at a clearly test-scoped database. Otherwise they skip by
  design.
- If tests only pass after ad hoc shell exports, stop and fix the shared settings/bootstrap path
  instead. Deterministic test-only overrides belong in `apps/backend/tests/conftest.py`.
- Always run import-boundary test when moving modules:
  - `uv run --project apps/backend pytest apps/backend/tests/unit/test_import_boundaries.py`

## Web

- `cd apps/web && npm run test`
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run lint`

## CI gates

PRs must pass lint, typecheck, tests, and build.
