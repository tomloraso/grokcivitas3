# Phase H5 Design - Operational Observability For Freshness And Coverage Drift

## Document Control

- Status: Proposed
- Last updated: 2026-03-03
- Depends on:
  - `.planning/phases/phase-hardening/H1-pipeline-run-policy-quality-gates.md`
  - `.planning/phases/phase-hardening/H4-data-completeness-contract-api-ui.md`
  - `.planning/phases/phase-0/0A-data-platform-baseline.md`
  - `docs/architecture/backend-conventions.md`
  - `docs/runbooks/local-development.md`

## Objective

Provide production-grade observability for pipeline freshness, coverage drift, and run health so data quality regressions are detected before users encounter empty or misleading school pages.

## Scope

### In scope

- Define a canonical metrics model for pipeline health, freshness lag, and section-level coverage.
- Persist daily coverage snapshots for trend analysis and drift alerting.
- Add strict alert policies for freshness breaches, coverage regression, and repeated quality-gate failures.
- Expose internal operations visibility for support and incident response.

### Out of scope

- Third-party APM migration.
- UI redesign beyond H4 completeness rendering.

## Observability Contract

### Core telemetry dimensions

- `source`
- `dataset`
- `section`
- `academic_year` (where relevant)
- `run_status`
- `contract_version`

### Required metric families

1. Pipeline run health:
   - `pipeline_run_duration_seconds`
   - `pipeline_downloaded_rows`
   - `pipeline_staged_rows`
   - `pipeline_promoted_rows`
   - `pipeline_rejected_ratio`
2. Freshness:
   - `source_freshness_lag_hours`
   - `section_freshness_lag_hours`
3. Coverage:
   - `section_coverage_ratio`
   - `schools_with_section_count`
   - `trends_years_distribution` (`0`, `1`, `2+`)
4. Reliability:
   - `quality_gate_failures_total`
   - `consecutive_failed_runs`

## Alert Policy

1. Freshness SLA breach:
   - trigger when `source_freshness_lag_hours` exceeds source SLA for two consecutive checks.
2. Coverage drift:
   - trigger when `section_coverage_ratio` drops by more than configured threshold day-over-day.
3. Quality gate instability:
   - trigger when the same source fails hard gate more than `N` consecutive runs.
4. Silent sparse trend risk:
   - trigger when schools with `0` or `1` trend years exceed expected baseline threshold.

## File-Oriented Implementation Plan

1. `apps/backend/alembic/versions/*_hardening_data_quality_snapshots.py` (new)
   - add `data_quality_snapshots` and `pipeline_run_events` tables.
2. `apps/backend/src/civitas/domain/operations/models.py` (new)
   - add domain models for freshness and coverage snapshot records.
3. `apps/backend/src/civitas/application/operations/ports/data_quality_repository.py` (new)
   - define repository contract for writing snapshots and querying drift.
4. `apps/backend/src/civitas/application/operations/use_cases.py` (new)
   - add use cases for snapshot generation and alert evaluation.
5. `apps/backend/src/civitas/infrastructure/persistence/postgres_data_quality_repository.py` (new)
   - implement persistence and drift queries.
6. `apps/backend/src/civitas/infrastructure/pipelines/runner.py`
   - emit standardized run telemetry after each pipeline execution.
7. `apps/backend/src/civitas/cli/main.py`
   - add operations command:
     - `civitas ops data-quality snapshot --strict`
8. `tools/scripts/check_data_quality_slo.py` (new)
   - evaluate freshness/coverage thresholds in CI or scheduled ops jobs.
9. `docs/runbooks/local-development.md`
   - document freshness and coverage drift triage workflow.
10. `apps/backend/tests/unit/test_data_quality_use_cases.py` (new)
    - unit tests for freshness and drift evaluation logic.
11. `apps/backend/tests/integration/test_data_quality_repository.py` (new)
    - integration coverage for snapshot and drift queries.

## Testing And Quality Gates

### Required tests

- freshness lag is computed consistently from source timestamps.
- coverage ratio is computed per section and persists daily snapshots.
- coverage drift threshold breach raises deterministic alert state.
- repeated hard failures raise consecutive-failure alerts.

### Required gates

- `uv run --project apps/backend pytest apps/backend/tests/unit/test_data_quality_use_cases.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/integration/test_data_quality_repository.py -q`
- `uv run --project apps/backend python tools/scripts/check_data_quality_slo.py --strict`
- `make lint`
- `make test`

## Acceptance Criteria

1. Freshness and coverage drift are measurable daily for every active profile section.
2. Operational alerts trigger on real regressions and include actionable source/section context.
3. Support and engineering can identify whether a sparse school page is source-limited or pipeline-regressed within one runbook flow.
4. Observability behavior is test-covered and reproducible in local and CI environments.

## Risks And Mitigations

- Risk: alert fatigue from noisy thresholds.
  - Mitigation: per-source thresholds, consecutive breach requirement, and runbook tuning.
- Risk: snapshot generation becomes expensive on large datasets.
  - Mitigation: incremental aggregation and indexed snapshot tables.
