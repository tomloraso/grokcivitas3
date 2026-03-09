# Phase 20 / 20B Design - Materialization And Backfill

## Document Control

- Status: Planned
- Last updated: 2026-03-09
- Depends on:
  - `.planning/phases/phase-20-similar-school-benchmarking/20A-cohort-model-and-benchmark-schema.md`

## Objective

Implement benchmark cohort construction, distribution materialization, and percentile backfill without moving work into the request path.

## Materialization Workflow

1. Select benchmarkable metric rows from Gold yearly tables.
2. Build legacy scopes:
   - national
   - local authority district
   - phase
3. Build similar-school scopes from the cohort signature rules defined in `20A`.
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
