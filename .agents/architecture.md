# Architecture Guardrails

Before any non-trivial change, read `docs/architecture.md`.

## Package ownership

- `apps/backend/src/bootstrap_app/domain`: business rules and entities.
- `apps/backend/src/bootstrap_app/application`: use-cases, orchestration, and ports.
- `apps/backend/src/bootstrap_app/adapters`: infrastructure implementations.
- `apps/backend/src/bootstrap_app/contracts`: API/event DTOs and schemas.
- `apps/backend/src/bootstrap_app/api` and `cli`: transport/composition roots only.

## Dependency direction (non-negotiable)

- Domain must not import `application`, `adapters`, `api`, or `cli`.
- Application may import domain/contracts but must not import adapters.
- Adapters implement application/domain ports.
- API/CLI depend on application and adapters for wiring.

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
