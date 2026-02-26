# Testing Strategy

## Unit

- Domain + application logic (fast, deterministic).

## Integration

- API endpoint behavior with in-memory adapters.

## Boundary

- Import-layer tests enforce architecture direction.

## Frontend

- Unit/component tests via Vitest + Testing Library.
- Optional E2E coverage via Playwright scaffold.

## CI quality gates

- Backend: ruff, mypy, pytest.
- Web: eslint, typecheck, vitest, build.
