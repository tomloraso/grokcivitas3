# Testing Strategy

## Unit

- Domain + application logic (fast, deterministic).

## Integration

- Backend integration tests run against a real Postgres database and are destructive by design.
- Prefer `CIVITAS_TEST_DATABASE_URL` for integration suites; only fall back to
  `CIVITAS_DATABASE_URL` when it already points at an obviously test-scoped database.
- Integration-test database selection must go through the shared settings module
  (`civitas.infrastructure.config.settings`). Do not parse `.env` directly inside fixtures or test
  helpers.
- If test configuration is wrong, fix `AppSettings` or shared pytest bootstrap. Do not paper over
  the problem with shell-only exports or duplicated dotenv loading.

## Boundary

- Import-layer tests enforce architecture direction.
- Boundary checks also enforce transport-contract isolation (API schemas are API-only).

## Frontend

- Unit/component tests via Vitest + Testing Library.
- Optional E2E coverage via Playwright scaffold.
- ESLint rules enforce frontend network/import boundaries.

## CI quality gates

- Backend: ruff, mypy, pytest.
- Web: eslint, typecheck, vitest, build.
