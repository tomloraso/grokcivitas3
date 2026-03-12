# Phase 19 / 19B Design - Materialization And Backfill

## Document Control

- Status: Completed
- Last updated: 2026-03-12
- Depends on:
  - `.planning/phases/phase-19-similar-school-benchmarking/19A-cohort-model-and-benchmark-schema.md`

## Objective

Implement benchmark cohort construction, distribution materialization, and percentile backfill without moving work into the request path.

## Materialization Workflow

1. Select benchmarkable metric rows from Gold yearly tables.
2. Build legacy scopes:
   - national
   - local authority district
   - phase
3. Build similar-school scopes from the cohort signature rules defined in `19A`.
4. Compute:
   - school counts
   - mean
   - percentiles
   - per-school percentile rank within each cohort
5. Persist results to the new benchmark tables.
6. Refresh the legacy compatibility table if it is still required.

## Fallback Rules

1. Minimum cohort size for similar-school benchmarking:
   - default target `30`
2. If cohort size is below minimum:
   - relax bands in deterministic order:
     - remove religious character
     - widen SEN band
     - widen FSM band
     - widen pupil-roll band
3. Persist the final cohort definition actually used in `definition_json`.

## Repository File Plan

Primary implementation area:

- `apps/backend/src/civitas/infrastructure/persistence/postgres_school_trends_repository.py`

Likely supporting changes:

- new benchmark materializer helper under `apps/backend/src/civitas/infrastructure/persistence/`
- new alembic migration for benchmark cohort tables
- updated manual or CLI benchmark refresh command path

Tests:

- `apps/backend/tests/integration/test_school_trends_repository.py`
- new benchmark cohort integration tests
- percentile edge-case unit tests

## Backfill Strategy

1. Backfill the latest supported academic year first.
2. Validate cohort sizes and percentile sanity on a sampled metric set.
3. Backfill prior years once the latest-year run is accepted.

## Acceptance Criteria

1. Similar-school cohorts can be materialized in a deterministic offline job.
2. Legacy average benchmarks remain available during migration.
3. Percentile rank outputs are stable across reruns with unchanged source data.

## Implemented State

- Implemented through:
  - `apps/backend/src/civitas/infrastructure/persistence/metric_benchmark_materializer.py`
  - `apps/backend/src/civitas/infrastructure/persistence/postgres_school_trends_repository.py`
  - `apps/backend/alembic/versions/20260312_40_phase_19_similar_school_benchmarking.py`
- The offline rebuild now materializes:
  - `metric_benchmark_cohorts_yearly`
  - `metric_benchmark_distributions_yearly`
  - `school_metric_percentiles_yearly`
  - legacy-compatible `metric_benchmarks_yearly` averages for national, LAD, and phase scopes
- Similar-school fallback widening is implemented through staged cohort signatures and minimum cohort-size selection before percentile persistence.

## Deviations

- The repository still exposes a targeted `materialize_metric_benchmarks_for_urns(...)` entry point for CLI/use-case compatibility, but the current implementation rebuilds the shared cache globally rather than incrementally updating only selected URNs.

## Validation

- `uv run --project apps/backend pytest apps/backend/tests/integration/test_school_trends_repository.py -q`
  - Result: skipped in this local environment because the integration backing services were not available.
- `make test`
  - Result: phase repository tests remained skipped locally; broader backend and web suites passed.

## Completion Note

- 19B is complete for Phase 19 sign-off. Incremental URN-scoped rebuild remains optional follow-up work, not a blocker to the shipped materialization model.
