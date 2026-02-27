# Architecture Guardrails

Before any non-trivial change, read `docs/architecture.md`.

## Package ownership

- `apps/backend/src/civitas/domain`: business rules and entities.
- `apps/backend/src/civitas/application`: use-cases, orchestration, and ports.
- `apps/backend/src/civitas/infrastructure`: persistence and external integrations.
- `apps/backend/src/civitas/api` and `cli`: transport entrypoints only.
- `apps/backend/src/civitas/bootstrap`: dependency composition/wiring.

## Dependency direction (non-negotiable)

- Domain must not import `application`, `infrastructure`, `api`, `cli`, or `bootstrap`.
- Application may import domain but must not import infrastructure or transport layers.
- Infrastructure implements application/domain ports.
- API/CLI depend on application contracts and bootstrap wiring.

## Utility ownership split

- Domain-owned helpers: `domain/shared/helpers`.
- Application-owned helpers: `application/shared/utils`.
- Do not add a global `utils` package at root.

## Import style

- Use explicit leaf imports.
- No barrel imports (`__init__.py` re-export chains).
- Keep one canonical import path per concept.

## Enforcement

- `apps/backend/tests/unit/test_import_boundaries.py` verifies layer boundaries.
- `ruff` tidy-import rules backstop banned imports.

