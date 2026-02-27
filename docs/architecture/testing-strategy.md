# Testing Strategy

## Unit

- Domain + application logic (fast, deterministic).

## Integration

- API endpoint behavior with in-memory infrastructure adapters.

## Boundary

- Import-layer tests enforce architecture direction.
- Boundary checks also enforce transport-contract isolation (API schemas are API-only).

## Frontend

- Unit/component tests via Vitest + Testing Library.
- Optional E2E coverage via Playwright scaffold.

## CI quality gates

- Backend: ruff, mypy, pytest.
- Web: eslint, typecheck, vitest, build.
