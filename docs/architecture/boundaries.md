# Boundaries

## Backend package map

- `civitas.domain`: entities and pure rules.
- `civitas.application`: use-cases and port protocols.
- `civitas.infrastructure`: repository/IO implementations.
- `civitas.api.schemas`: request/response DTOs.
- `civitas.api`: HTTP routes and dependency injection bindings.
- `civitas.cli`: CLI wrappers around application services.
- `civitas.bootstrap`: composition root for infrastructure + use-case wiring.

## Rules

- Domain must not import application/infrastructure/api/cli/bootstrap.
- Application must not import infrastructure/api/cli/bootstrap.
- Infrastructure may import application ports and domain types.
- API/CLI must remain thin and use bootstrap for composition.
- API/CLI must not import infrastructure modules directly.
- API schemas (`civitas.api.schemas`) are transport-only and imported by API modules only.

## Frontend boundary

Frontend depends on backend API contracts only; business rules remain backend-owned.

- UI modules must consume typed API functions, not raw network calls.
- Only `apps/web/src/api/*` performs HTTP calls.
- Frontend wire contracts are derived from backend OpenAPI (`src/api/generated-types.ts`) via `src/api/types.ts`.
- Avoid hand-maintained duplicate API payload types when generated contracts exist.


