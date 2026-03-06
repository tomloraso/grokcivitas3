# Phase 3 / H3 Design - Historical Demographics Backfill With Configurable Lookback

## Document Control

- Status: Implemented
- Last updated: 2026-03-03
- Depends on:
 - `.planning/phases/phase-3-hardening/H2-source-normalization-contracts.md`
  - `.planning/phases/phase-1/1B-dfe-characteristics-pipeline.md`
  - `.planning/phases/phase-1/1E-school-trends-api.md`
  - `.planning/project-brief.md`
  - `docs/architecture/backend-conventions.md`

## Objective

Provide multi-year demographics history through a repeatable backfill process with configurable lookback years, enabling robust trend deltas where source data exists.

## Scope

### In scope

- Discover available historical DfE demographics datasets or releases.
- Backfill into `school_demographics_yearly` with deterministic year normalization.
- Add configurable lookback horizon (`X` years) for controlled backfill depth.
- Keep daily incremental ingest separate from historical backfill operation.

### Out of scope

- New trend metrics beyond existing demographics columns.
- URN lineage bridge for predecessor/successor schools (future extension).

## Decisions

1. Backfill and daily incremental are separate execution modes.
2. Lookback horizon is config-driven, not hardcoded.
3. Missing years remain explicit gaps; no interpolation.
4. Backfill is idempotent and can be rerun safely.

## Configuration

Add settings:

- `CIVITAS_DFE_CHARACTERISTICS_LOOKBACK_YEARS` (default `5`)
- `CIVITAS_DFE_CHARACTERISTICS_BACKFILL_ENABLED` (default `false`)
- `CIVITAS_DFE_CHARACTERISTICS_DATASET_CATALOG` (optional explicit dataset id list)

## File-Oriented Implementation Plan

1. `apps/backend/src/civitas/infrastructure/config/settings.py`
   - add lookback and backfill controls.
2. `apps/backend/src/civitas/infrastructure/pipelines/dfe_characteristics.py`
   - support explicit multi-source/year ingestion in backfill mode.
   - include source release/year provenance per row.
3. `apps/backend/src/civitas/cli/main.py`
   - add command:
     - `civitas pipeline backfill --source dfe_characteristics --lookback-years N`
4. `tools/scripts/discover_dfe_characteristics_history.py` (new)
   - enumerate candidate source years/dataset versions and write inventory.
5. `apps/backend/alembic/versions/*_hardening_dfe_source_inventory.py` (new)
   - optional `dfe_source_inventory` table for auditable source-year catalog (deferred).
6. `apps/backend/tests/unit/test_dfe_characteristics_transforms.py`
   - add multi-year normalization and provenance tests.
7. `apps/backend/tests/integration/test_dfe_characteristics_pipeline.py`
   - add backfill mode idempotency and lookback coverage tests.
8. `docs/runbooks/local-development.md`
   - add historical backfill commands and safety notes.

## Testing And Quality Gates

### Required tests

- lookback `N` backfills only target years.
- rerun with same lookback is idempotent.
- trends endpoint returns `years_count >= 2` for at least one fixture school with historical source data.
- provenance fields correctly record source dataset id/version by academic year.

### Required gates

- `uv run --project apps/backend pytest apps/backend/tests/unit/test_dfe_characteristics_transforms.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/integration/test_dfe_characteristics_pipeline.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/integration/test_school_trends_repository.py -q`
- `make lint`
- `make test`

## Acceptance Criteria

1. Backfill command supports configurable lookback and deterministic output.
2. `school_demographics_yearly` can hold multi-year history for schools where sources provide it.
3. Trends API uses backfilled history without additional API shape changes.
4. Missing years remain explicit and measurable for completeness reporting.

## Risks And Mitigations

- Risk: historic source access is inconsistent across years.
  - Mitigation: source inventory table plus explicit year-level coverage reporting.
- Risk: backfill runtime is long.
  - Mitigation: chunked year execution and resumable runs from `H6`.

## Implementation Notes (2026-03-03)

1. Backfill mode is implemented as a dedicated CLI command (`civitas pipeline backfill`) that is intentionally separate from daily `pipeline run` execution.
2. Historical dataset discovery is implemented via `tools/scripts/discover_dfe_characteristics_history.py`, and runtime backfill prefers explicit dataset catalogs for deterministic operations.
3. The optional `dfe_source_inventory` table is deferred; per-row provenance in `school_demographics_yearly` and Bronze backfill manifest metadata provide current audit coverage.
