# M6 - Benchmarks and Cross-Metric Trend Dashboard

## Status

- Implementation completed on 2026-03-05.
- Backend quality gate passed (tests + lint).
- Post-M6 full pipeline/API end-to-end validation completed on 2026-03-05.
- Milestone handover state: ready for frontend testing.

## Goal

Provide consistent benchmark context and trend presentation across all metric families.

## Gap Coverage

- "Historical trends dashboard" for all implemented metrics
- National/local benchmark storage and exposure for each metric

## Source Strategy

- Primarily derived from already ingested metric tables.
- Additional reference datasets may be required for local benchmark geographies.

## Bronze -> Silver -> Gold Plan

1. Silver:
   - derive benchmark-ready aggregates per metric/year/geography.
2. Gold:
   - add `metric_benchmarks_yearly` keyed by `(metric_key, academic_year, benchmark_scope, benchmark_area)`;
   - optionally materialize comparison views for API performance.

## API Plan

1. Add benchmark block to profile metric payloads.
2. Extend trends endpoint with benchmark companion series.
3. Add a dedicated dashboard endpoint for multi-domain trend slices.

## Frontend Plan

1. Add unified trend dashboard section combining demographics, performance, attendance, workforce, and area metrics.
2. Display school vs benchmark deltas with clear scope labels.
3. Keep rendering resilient to partial coverage by section.

## Implementation Notes

1. Gold schema extended via migration `20260305_19_phase_m6_metric_benchmarks.py`:
   - Added `metric_benchmarks_yearly` keyed by `(metric_key, academic_year, benchmark_scope, benchmark_area)`.
2. Domain/application contracts extended:
   - Added benchmark domain models and repository port method `get_metric_benchmark_series`.
   - Extended trends/profile DTOs with benchmark blocks and dashboard response types.
3. Repository implementation completed:
   - Added benchmark aggregation query from existing metric tables.
   - Added benchmark snapshot persistence into `metric_benchmarks_yearly`.
4. API implementation completed:
   - Extended `/api/v1/schools/{urn}/trends` with benchmark companion series.
   - Extended `/api/v1/schools/{urn}` with benchmark summary block.
   - Added `/api/v1/schools/{urn}/trends/dashboard`.
5. Contract checks and tests updated:
   - Benchmarks included in API schema/contract assertions.
   - New trends dashboard use-case + API integration coverage.

## Validation and Gates

- Deterministic benchmark aggregation tests.
- API contract tests for benchmark payload shape.
- Frontend tests for mixed benchmark availability and missing-data UX.

## Validation Evidence

- Command:
  - `uv run --project apps/backend pytest apps/backend/tests/unit/test_get_school_trends_use_case.py apps/backend/tests/integration/test_school_trends_api.py apps/backend/tests/integration/test_school_profile_api.py apps/backend/tests/integration/test_school_trends_repository.py apps/backend/tests/unit/test_api_contract_checks.py -q`
- Result:
  - `23 passed`
- Lint gate:
  - `uv run --project apps/backend ruff check apps/backend/src/civitas/application/school_trends/dto.py apps/backend/src/civitas/application/school_trends/use_cases.py apps/backend/src/civitas/infrastructure/persistence/postgres_school_trends_repository.py apps/backend/src/civitas/application/school_profiles/dto.py apps/backend/src/civitas/application/school_profiles/use_cases.py apps/backend/src/civitas/api/schemas/school_trends.py apps/backend/src/civitas/api/schemas/school_profiles.py apps/backend/src/civitas/api/routes.py apps/backend/tests/integration/test_school_trends_repository.py apps/backend/tests/unit/test_get_school_trends_use_case.py apps/backend/tests/integration/test_school_trends_api.py apps/backend/tests/integration/test_school_profile_api.py apps/backend/tests/unit/test_api_contract_checks.py apps/backend/tests/unit/test_get_school_profile_use_case.py`
  - Result: `All checks passed`
- Post-M6 cross-milestone validation command:
  - `uv run --project apps/backend pytest apps/backend/tests/unit/test_demographics_spc_contract.py apps/backend/tests/unit/test_demographics_sen_contract.py apps/backend/tests/unit/test_dfe_attendance_contract.py apps/backend/tests/unit/test_dfe_behaviour_contract.py apps/backend/tests/unit/test_dfe_workforce_contract.py apps/backend/tests/unit/test_uk_house_prices_contract.py apps/backend/tests/unit/test_ons_imd_transforms.py apps/backend/tests/unit/test_pipeline_cli.py apps/backend/tests/unit/test_pipeline_contract_metadata.py apps/backend/tests/unit/test_settings.py apps/backend/tests/integration/test_demographics_release_files_pipeline.py apps/backend/tests/integration/test_dfe_characteristics_pipeline.py apps/backend/tests/integration/test_dfe_attendance_pipeline.py apps/backend/tests/integration/test_dfe_behaviour_pipeline.py apps/backend/tests/integration/test_dfe_workforce_pipeline.py apps/backend/tests/integration/test_ons_imd_pipeline.py apps/backend/tests/integration/test_uk_house_prices_pipeline.py apps/backend/tests/integration/test_data_quality_repository.py apps/backend/tests/integration/test_school_profile_repository.py apps/backend/tests/integration/test_school_profile_api.py apps/backend/tests/unit/test_get_school_profile_use_case.py apps/backend/tests/unit/test_cached_school_profile_repository.py apps/backend/tests/integration/test_school_trends_repository.py apps/backend/tests/integration/test_school_trends_api.py apps/backend/tests/unit/test_get_school_trends_use_case.py apps/backend/tests/unit/test_api_contract_checks.py -q`
  - Result: `129 passed`
