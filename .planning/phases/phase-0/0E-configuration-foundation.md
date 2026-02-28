# Phase 0E Design - Configuration Foundation

## Document Control

- Status: Implemented
- Last updated: 2026-02-27
- Depends on:
  - `.planning/phases/phase-0/0A-data-platform-baseline.md`
  - `.planning/project-brief.md`
  - `docs/architecture.md`
  - `docs/architecture/backend-conventions.md`

## Objective

Establish a single, typed configuration model early so new Phase 0 work does not accumulate ad-hoc environment access and inconsistent defaults.

## Scope

### In scope

- Centralized backend settings model and loader.
- Explicit settings ownership for database, pipeline, and external HTTP configuration.
- Local development `.env` workflow and sample configuration.
- Refactor current direct `os.environ` reads in infrastructure modules to use the centralized settings boundary.

### Out of scope

- Cloud secret-store integration (provider-specific).
- Frontend runtime configuration.
- Production deployment automation changes beyond documenting required environment variables.

## Decisions

1. **Single configuration boundary**: backend runtime configuration is accessed through one typed settings object.
2. **Typed validation**: invalid/missing required settings fail fast at process start.
3. **No ad-hoc env access**: `os.environ` reads are restricted to the configuration module.
4. **Local developer ergonomics**: support `.env`-driven local setup and commit `.env.example`.
5. **Bootstrap ownership**: `bootstrap` provides settings to infrastructure factories (DB, pipelines, API dependencies).

## Implementation Progress (2026-02-27)

- Completed: introduced typed settings loader at `infrastructure/config/settings.py` with `database`, `pipeline`, and `http_clients` group accessors.
- Completed: refactored `database.py`, pipeline registry wiring, and `gias.py` to remove direct environment access.
- Completed: updated `bootstrap/container.py` to own settings resolution and inject configured values into DB and pipeline factories.
- Completed: added `.env.example` and updated `docs/runbooks/local-development.md` for canonical local configuration setup.
- Completed: added unit coverage in `test_settings.py`, including a guard to prevent `os.environ` access outside the settings module.

## Configuration Domains (Phase 0)

Minimum settings groups:

- `database`
  - `CIVITAS_DATABASE_URL`
- `pipeline`
  - `CIVITAS_BRONZE_ROOT`
  - `CIVITAS_GIAS_SOURCE_CSV` (optional)
  - `CIVITAS_GIAS_SOURCE_ZIP` (optional)
- `http_clients`
  - request timeout/retry settings for external API calls used in Phase 0+

## File-Oriented Implementation Plan

1. `apps/backend/src/civitas/infrastructure/config/settings.py`
   - define typed settings models and loader.
2. `apps/backend/src/civitas/infrastructure/persistence/database.py`
   - consume settings instead of direct environment access.
3. `apps/backend/src/civitas/infrastructure/pipelines/gias.py`
   - consume settings inputs through injected configuration rather than direct env reads.
4. `apps/backend/src/civitas/bootstrap/container.py`
   - expose cached settings factory and inject settings into infrastructure components.
5. `apps/backend/tests/unit/test_settings.py`
   - add validation/default/override tests for settings loader behavior.
6. `.env.example`
   - add local baseline variables and comments.
7. `docs/runbooks/local-development.md`
   - update with canonical configuration setup flow.

## Testing And Quality Gates

### Required tests

- Settings loader uses defaults where expected.
- Required settings validation fails with clear errors.
- Pipeline and DB wiring resolves configuration only through settings injection.

### Required gates

- `make lint`
- `make test`

## Acceptance Criteria

1. New backend features in Phase 0+ can read runtime config only through the shared settings boundary.
2. No direct `os.environ` reads remain outside the settings module.
3. Local setup is reproducible via `.env.example` plus runbook steps.
4. Existing Phase 0 behavior continues to work with settings-backed configuration.

## Risks And Mitigations

- **Risk**: introducing a settings layer could delay nearby feature work.
  - **Mitigation**: keep scope focused on Phase 0 variables and refactor only touched modules.
- **Risk**: dual configuration paths during transition create confusion.
  - **Mitigation**: remove legacy direct env reads in the same change as settings rollout.
