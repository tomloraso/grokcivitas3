# Phase 15 / 15C Design - Serving Contract And Benchmark Integration

## Document Control

- Status: Planned
- Last updated: 2026-03-09
- Depends on:
  - `.planning/phases/phase-15-school-financial-benchmarks/15B-aar-pipeline-and-gold-schema.md`

## Objective

Expose finance metrics through the existing profile, trends, and benchmark surfaces without introducing finance-specific request paths.

Because the current profile and trends APIs use stable response shapes, finance should be added as explicit nullable contract fields plus finance completeness metadata. Finance availability must not depend on returning different response shapes for academy versus non-academy schools.

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

Profile completeness additions:

- `completeness.finance`

Trend additions:

- `finance.total_income_gbp`
- `finance.total_expenditure_gbp`
- `finance.income_per_pupil_gbp`
- `finance.expenditure_per_pupil_gbp`
- `finance.total_staff_costs_gbp`
- `finance.staff_costs_pct_of_expenditure`
- `finance.revenue_reserve_per_pupil_gbp`

Trend completeness additions:

- `section_completeness.finance`

## Benchmark Registration

Add finance metrics to the metric catalog used by benchmark materialization:

- `finance_income_per_pupil_gbp`
- `finance_expenditure_per_pupil_gbp`
- `finance_staff_costs_pct_of_expenditure`
- `finance_revenue_reserve_per_pupil_gbp`
- `finance_teaching_staff_costs_per_pupil_gbp`

These metrics should flow through the existing `metric_benchmarks_yearly` materialization before Phase 20 redesigns the benchmark model.

This phase does not add finance rows to the compare API or compare UI. The benchmark keys above should use stable naming so Phase 20 or a later compare-focused phase can register them without renaming.

## Repository File Plan

Backend serving files expected to change:

- `apps/backend/src/civitas/domain/school_profiles/models.py`
- `apps/backend/src/civitas/domain/school_trends/models.py`
- `apps/backend/src/civitas/infrastructure/persistence/postgres_school_profile_repository.py`
- `apps/backend/src/civitas/infrastructure/persistence/cached_school_profile_repository.py`
- `apps/backend/src/civitas/infrastructure/persistence/postgres_school_trends_repository.py`
- `apps/backend/src/civitas/application/school_profiles/`
- `apps/backend/src/civitas/application/school_trends/`
- `apps/backend/src/civitas/api/schemas/school_profiles.py`
- `apps/backend/src/civitas/api/schemas/school_trends.py`
- `apps/backend/src/civitas/infrastructure/persistence/postgres_data_quality_repository.py`

Tests expected to change:

- `apps/backend/tests/integration/test_school_profile_repository.py`
- `apps/backend/tests/integration/test_school_profile_api.py`
- `apps/backend/tests/integration/test_school_trends_repository.py`
- `apps/backend/tests/integration/test_school_trends_api.py`
- `apps/backend/tests/integration/test_data_quality_repository.py`

## Completeness Rules

1. `finance_latest` and finance trend collections are nullable but contract-stable for all schools.
2. `completeness.finance` and `section_completeness.finance` are present for all schools.
3. Non-academy schools use explicit finance completeness reasons rather than a school-type-specific response shape.
4. Academy schools with no matched AAR row surface an explicit finance completeness reason rather than silent nulls.
5. No API fallback to trust-level `Central Services` values.
6. Benchmark materialization excludes null metrics and records school counts as usual.

## Acceptance Criteria

1. Finance metrics appear in school profile and trends payloads for academy schools with AAR data.
2. Finance metrics benchmark successfully with the current benchmark cache process.
3. Non-academy schools receive explicit finance completeness semantics that do not imply maintained-school source coverage.
4. Profile and trends API schemas remain shape-stable across school types.
