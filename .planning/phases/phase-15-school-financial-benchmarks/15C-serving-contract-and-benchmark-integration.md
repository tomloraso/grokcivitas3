# Phase 15 / 15C Design - Serving Contract And Benchmark Integration

## Document Control

- Status: Planned
- Last updated: 2026-03-09
- Depends on:
  - `.planning/phases/phase-15-school-financial-benchmarks/15B-aar-pipeline-and-gold-schema.md`

## Objective

Expose finance metrics through the existing profile, trends, and benchmark surfaces without introducing finance-specific request paths.

## Serving Model

Profile latest additions:

- `finance_latest.total_income_gbp`
- `finance_latest.total_expenditure_gbp`
- `finance_latest.income_per_pupil_gbp`
- `finance_latest.expenditure_per_pupil_gbp`
- `finance_latest.total_staff_costs_gbp`
- `finance_latest.staff_costs_pct_of_expenditure`
- `finance_latest.revenue_reserve_gbp`
- `finance_latest.revenue_reserve_per_pupil_gbp`
- `finance_latest.source_academic_year`

Trend additions:

- `finance.total_income_gbp`
- `finance.total_expenditure_gbp`
- `finance.income_per_pupil_gbp`
- `finance.expenditure_per_pupil_gbp`
- `finance.total_staff_costs_gbp`
- `finance.staff_costs_pct_of_expenditure`
- `finance.revenue_reserve_per_pupil_gbp`

## Benchmark Registration

Add finance metrics to the metric catalog used by benchmark materialization:

- `finance_income_per_pupil_gbp`
- `finance_expenditure_per_pupil_gbp`
- `finance_staff_costs_pct_of_expenditure`
- `finance_revenue_reserve_per_pupil_gbp`
- `finance_teaching_staff_costs_per_pupil_gbp`

These metrics should flow through the existing `metric_benchmarks_yearly` materialization before Phase 20 redesigns the benchmark model.

## Repository File Plan

Backend serving files expected to change:

- `apps/backend/src/civitas/infrastructure/persistence/postgres_school_profile_repository.py`
- `apps/backend/src/civitas/infrastructure/persistence/cached_school_profile_repository.py`
- `apps/backend/src/civitas/infrastructure/persistence/postgres_school_trends_repository.py`
- `apps/backend/src/civitas/application/school_profiles/`
- `apps/backend/src/civitas/application/school_trends/`
- `apps/backend/src/civitas/infrastructure/persistence/postgres_data_quality_repository.py`

Tests expected to change:

- `apps/backend/tests/integration/test_school_profile_repository.py`
- `apps/backend/tests/integration/test_school_profile_api.py`
- `apps/backend/tests/integration/test_school_trends_repository.py`
- `apps/backend/tests/integration/test_school_trends_api.py`
- `apps/backend/tests/integration/test_data_quality_repository.py`

## Completeness Rules

1. Finance section is absent for non-academy schools until a maintained-school source is added.
2. Finance section is present with explicit completeness reason for academies where AAR row is unavailable.
3. No API fallback to trust-level `Central Services` values.
4. Benchmark materialization excludes null metrics and records school counts as usual.

## Acceptance Criteria

1. Finance metrics appear in school profile and trends payloads for academy schools with AAR data.
2. Finance metrics benchmark successfully with the current benchmark cache process.
3. Non-academy schools do not receive misleading null-filled finance sections that imply source coverage.
