# Boundaries

## Backend package map

- `civitas.domain`: entities and pure rules.
- `civitas.application`: use-cases and port protocols.
- `civitas.adapters`: repository/IO implementations.
- `civitas.contracts`: request/response DTOs.
- `civitas.api`: HTTP routes and dependency wiring.
- `civitas.cli`: CLI wrappers around application services.

## Rules

- Domain must not import application/adapters/api/cli.
- Application must not import adapters.
- Adapters may import application ports and domain types.
- API/CLI may import adapters for composition.

## Frontend boundary

Frontend depends on backend API contracts only; business rules remain backend-owned.

