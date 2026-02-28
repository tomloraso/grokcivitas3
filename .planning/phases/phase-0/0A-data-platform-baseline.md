# Phase 0A Design - Data Platform Baseline

## Document Control

- Status: Implemented
- Last updated: 2026-02-27
- Depends on:
  - `.planning/project-brief.md`
  - `.planning/data-architecture.md`
  - `.planning/deployment-strategy.md`
  - `docs/architecture.md`
  - `docs/architecture/principles.md`
  - `docs/architecture/boundaries.md`
  - `docs/architecture/testing-strategy.md`

## Objective

Establish the runtime and schema foundation required to execute Phase 0 safely and repeatedly:

1. PostgreSQL + PostGIS runtime for local development.
2. Schema migration baseline.
3. Shared pipeline interfaces and orchestration entrypoint.
4. CLI command surface for pipeline execution.

No source-specific business logic is implemented in 0A.

## Scope

### In scope

- Docker Compose database service using PostGIS.
- Migration framework setup and initial migration for shared platform tables.
- Pipeline base abstractions (`download`, `stage`, `promote`) and run lifecycle.
- CLI `pipeline` command group with `run --source` and `run --all`.
- Pipeline run metadata tables for observability and troubleshooting.

### Out of scope

- GIAS source parsing or transformation logic (0B).
- Search API endpoint behavior (0C).
- Web implementation (0D).

## Decisions

1. **Migration tool**: use Alembic as the migration source of truth.
2. **Local DB image**: use `postgis/postgis:16-3.4` instead of plain Postgres image.
3. **Pipeline lifecycle model**: standard three-step contract (`download`, `stage`, `promote`) with a shared run context.
4. **Entrypoint model**: keep `civitas.cli.main` thin; pipeline wiring lives in bootstrap and infrastructure.

## Implementation Progress (2026-02-27)

- Completed: PostGIS local runtime baseline (`docker-compose.yml`).
- Completed: Alembic initialized under `apps/backend/alembic` with baseline migration for `pipeline_runs`, `pipeline_rejections`, and `staging` schema.
- Completed: Pipeline abstractions and runner (`infrastructure/pipelines/base.py`, `infrastructure/pipelines/runner.py`).
- Completed: Placeholder `gias` pipeline registration and bootstrap wiring.
- Completed: CLI `pipeline run --source` and `pipeline run --all` command surface.
- Completed: Unit tests for pipeline runner and CLI wiring.

## Design

### Runtime and schema baseline

- Update root `docker-compose.yml`:
  - `postgres` image -> `postgis/postgis:16-3.4`
  - preserve existing credentials for local dev unless `.env` overrides are introduced.
- Initialize Alembic in `apps/backend` and commit:
  - `apps/backend/alembic.ini`
  - `apps/backend/alembic/env.py`
  - `apps/backend/alembic/versions/<timestamp>_phase0_platform_baseline.py`
- Initial migration creates:
  - `pipeline_runs`
  - `pipeline_rejections`
  - base schemas (`staging` and any shared schema names needed by 0B+)

### Pipeline abstractions

Add infrastructure pipeline modules:

- `apps/backend/src/civitas/infrastructure/pipelines/base.py`
- `apps/backend/src/civitas/infrastructure/pipelines/runner.py`

Required concepts:

- `PipelineSource` enum or literal registry (`gias` now, extensible later).
- `PipelineRunContext`:
  - `run_id`
  - `source`
  - `started_at`
  - file/system paths for Bronze output
  - db session/connection factory
- `PipelineResult`:
  - status
  - row counts by stage
  - rejection counts
  - duration

### CLI and composition

- Extend `apps/backend/src/civitas/cli/main.py` with a `pipeline` Typer group:
  - `civitas pipeline run --source gias`
  - `civitas pipeline run --all`
- Extend `apps/backend/src/civitas/bootstrap/container.py` with factories for pipeline runner and source registry.
- Keep route/API layers unchanged in 0A.

## File-Oriented Implementation Plan

1. `docker-compose.yml`
   - switch DB image to PostGIS variant and keep volume compatibility.
2. `apps/backend/pyproject.toml`
   - add Alembic + DB driver deps required for migrations.
3. `apps/backend/alembic.ini`
   - create base Alembic config.
4. `apps/backend/alembic/env.py`
   - configure migration metadata loading.
5. `apps/backend/alembic/versions/*_phase0_platform_baseline.py`
   - create baseline schemas and shared pipeline metadata tables.
6. `apps/backend/src/civitas/infrastructure/pipelines/base.py`
   - define shared contracts and base types.
7. `apps/backend/src/civitas/infrastructure/pipelines/runner.py`
   - define orchestration and result logging.
8. `apps/backend/src/civitas/bootstrap/container.py`
   - wire pipeline runner factory without breaking existing task scaffold.
9. `apps/backend/src/civitas/cli/main.py`
   - add `pipeline` commands.

## Testing And Quality Gates

### Tests to add

- `apps/backend/tests/unit/test_pipeline_runner.py`
  - verifies lifecycle ordering and failure handling.
- `apps/backend/tests/unit/test_pipeline_cli.py`
  - verifies Typer command wiring and source resolution.
- extend `apps/backend/tests/unit/test_import_boundaries.py` only if new package paths require explicit coverage updates.

### Required gates

- `make lint`
- `make test`

## Acceptance Criteria

1. Running migrations creates shared pipeline metadata and staging schema.
2. `civitas pipeline run --source gias` executes a placeholder pipeline contract path without runtime wiring errors.
3. Run metadata persists success/failure states for each invocation.
4. Architecture boundary tests remain green.

## Risks And Mitigations

- **Risk**: pipeline runner grows domain logic.
  - **Mitigation**: keep business transforms inside source modules only.
- **Risk**: migration setup adds friction on Windows environments.
  - **Mitigation**: document canonical root commands in implementation PR notes and use repo tooling paths.
