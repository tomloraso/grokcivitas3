# Backend Conventions

This page defines concrete conventions for backend implementation so features stay consistent and architecture boundaries remain enforceable.

## Scope

Applies to `apps/backend/src/civitas/*` for all new features.

## Feature Layout

Use the same folder shape for each backend feature:

```text
civitas/
  domain/<feature>/
    models.py
    value_objects.py            # optional
    services.py                 # optional pure domain services

  application/<feature>/
    use_cases.py
    dto.py                      # optional app request/response models
    ports/
      <port_name>.py

  infrastructure/
    persistence/
      <feature>_repository.py
    http/
      <feature>_client.py       # optional external API adapters
    pipelines/
      <feature>.py              # optional source pipeline

  api/
    schemas/
      <feature>.py
    routes/
      <feature>.py              # preferred for larger route sets
```

`bootstrap` owns composition and wiring for use cases + concrete adapters.

## Model Types

Keep model roles explicit and separate:

1. Domain models
   - Location: `civitas.domain.<feature>`
   - Purpose: business state + invariants
   - Allowed deps: stdlib and other domain modules only
   - Must not be Pydantic or framework-bound
2. Application DTOs
   - Location: `civitas.application.<feature>.dto` (optional)
   - Purpose: use-case input/output contracts internal to backend
   - Must not include transport concerns (HTTP codes, FastAPI types)
3. API schemas
   - Location: `civitas.api.schemas.<feature>`
   - Purpose: request/response wire contracts only
   - Pydantic models live here, not in domain/application
4. Persistence/external records
   - Location: infrastructure adapters
   - Purpose: DB rows and external payload shapes
   - Must not leak directly beyond infrastructure

## Port Conventions

1. Port location
   - `civitas.application.<feature>.ports.*`
2. Port type
   - Python `Protocol` definitions
3. Port naming
   - Use role-based names (`SchoolSearchRepository`, `PostcodeResolver`, `OfstedSourceClient`)
4. Port boundaries
   - Ports return domain models, value objects, or application DTOs
   - Ports never return API schemas
5. Port error semantics
   - Raise domain/application exceptions
   - Do not raise transport exceptions (HTTPException) from ports

## Mapping Ownership

1. API layer
   - Maps application/domain outputs to API schemas
   - Maps API request schemas to application input DTOs/primitives
2. Application layer
   - Orchestrates calls across ports and domain logic
   - Does not map SQL rows or external JSON directly
3. Infrastructure layer
   - Maps DB/external payloads to domain/application contracts
4. Domain layer
   - No mapping to transport/storage formats

## Contract Rules

1. Backend OpenAPI is the contract source of truth.
2. Frontend consumes generated/typed clients from backend OpenAPI.
3. Avoid hand-maintained duplicate API types in the frontend when generated types exist.

## Configuration And Settings

1. Environment-backed configuration must flow through `civitas.infrastructure.config.settings`.
2. Runtime code, CLI entrypoints, scripts, and test fixtures must use `AppSettings` or `get_settings()`
   instead of reading `.env` or `os.environ` ad hoc.
3. Repo-root `.env` discovery belongs in the shared settings module, not in individual callers.
4. If a new setting is needed for tests or operations, add it to `AppSettings` and reuse the shared
   settings path. Do not add fixture-local `.env` parsing as a workaround.
5. Test-only environment overrides that need to be deterministic across the suite belong in shared
   pytest bootstrap such as `apps/backend/tests/conftest.py`, not in one-off shell commands.

## Thin Entrypoints

API and CLI layers must remain thin:

1. No SQL queries in API/CLI modules.
2. No direct external HTTP calls in API/CLI modules.
3. API/CLI should orchestrate dependencies through bootstrap/application use cases.
4. Business rules belong in domain/application, not route handlers.

## Import Rules

1. Imports point inward.
2. `civitas.api.schemas` must only be imported by API modules.
3. Keep leaf imports explicit; avoid barrel re-exports.
