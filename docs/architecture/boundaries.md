# Boundaries

## Backend package map

- `bootstrap_app.domain`: entities and pure rules.
- `bootstrap_app.application`: use-cases and port protocols.
- `bootstrap_app.adapters`: repository/IO implementations.
- `bootstrap_app.contracts`: request/response DTOs.
- `bootstrap_app.api`: HTTP routes and dependency wiring.
- `bootstrap_app.cli`: CLI wrappers around application services.

## Rules

- Domain must not import application/adapters/api/cli.
- Application must not import adapters.
- Adapters may import application ports and domain types.
- API/CLI may import adapters for composition.

## Frontend boundary

Frontend depends on backend API contracts only; business rules remain backend-owned.
