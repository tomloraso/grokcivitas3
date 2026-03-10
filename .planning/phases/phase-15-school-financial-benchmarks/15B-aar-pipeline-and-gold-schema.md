# Phase 15 / 15B Design - AAR Pipeline And Gold Schema

## Document Control

- Status: Planned
- Last updated: 2026-03-09
- Depends on:
  - `.planning/phases/phase-15-school-financial-benchmarks/15A-source-contract-and-schema-freeze.md`

## Objective

Implement the Bronze ingest, Silver normalization, and Gold promotion path for annual academy finance metrics.

## Bronze -> Silver -> Gold Flow

1. Bronze:
   - download raw annual workbook into canonical `data/bronze/school_financial_benchmarks/<run-date>/`
   - keep academic year in the raw filename and manifest metadata, not in the Bronze directory shape
   - write manifest with workbook URL, downloaded timestamp, checksum, sheet names, and parsed row counts
2. Silver:
   - normalize `Academies` worksheet rows into `school_financials_aar_stage`
   - coerce numeric money fields and published percentages
   - reject rows with invalid URN or missing school name
   - preserve blank or suppressed numeric cells as `null`
3. Gold:
   - upsert into `school_financials_yearly`
   - compute derived per-pupil and ratio metrics into persisted Gold columns

## Gold Schema

Create `school_financials_yearly` keyed by `(urn, academic_year)` with:

- `urn bigint not null`
- `academic_year text not null`
- `finance_source text not null default 'aar'`
- `school_laestab text null`
- `school_name text not null`
- `trust_uid text null`
- `trust_name text null`
- `phase text null`
- `overall_phase text null`
- `pupils_fte numeric(12,2) null`
- `teachers_fte numeric(12,2) null`
- `total_income_gbp numeric(14,2) null`
- `total_expenditure_gbp numeric(14,2) null`
- `in_year_balance_gbp numeric(14,2) null`
- `revenue_reserve_gbp numeric(14,2) null`
- `total_grant_funding_gbp numeric(14,2) null`
- `total_self_generated_funding_gbp numeric(14,2) null`
- `teaching_staff_costs_gbp numeric(14,2) null`
- `supply_teaching_staff_costs_gbp numeric(14,2) null`
- `education_support_staff_costs_gbp numeric(14,2) null`
- `other_staff_costs_gbp numeric(14,2) null`
- `total_staff_costs_gbp numeric(14,2) null`
- `maintenance_improvement_costs_gbp numeric(14,2) null`
- `premises_costs_gbp numeric(14,2) null`
- `educational_supplies_costs_gbp numeric(14,2) null`
- `bought_in_professional_services_costs_gbp numeric(14,2) null`
- `catering_costs_gbp numeric(14,2) null`
- `income_per_pupil_gbp numeric(14,2) null`
- `expenditure_per_pupil_gbp numeric(14,2) null`
- `staff_costs_pct_of_expenditure numeric(7,4) null`
- `teaching_staff_costs_per_pupil_gbp numeric(14,2) null`
- `supply_staff_costs_pct_of_staff_costs numeric(7,4) null`
- `revenue_reserve_per_pupil_gbp numeric(14,2) null`
- `source_updated_at_utc timestamptz not null`

## Derived Gold Rules

1. `income_per_pupil_gbp = total_income_gbp / pupils_fte`
2. `expenditure_per_pupil_gbp = total_expenditure_gbp / pupils_fte`
3. `staff_costs_pct_of_expenditure = total_staff_costs_gbp / total_expenditure_gbp`
4. `teaching_staff_costs_per_pupil_gbp = teaching_staff_costs_gbp / pupils_fte`
5. `supply_staff_costs_pct_of_staff_costs = supply_teaching_staff_costs_gbp / total_staff_costs_gbp`
6. `revenue_reserve_per_pupil_gbp = revenue_reserve_gbp / pupils_fte`

Null-safe rule:

- return `null` for any derived metric where denominator is `0`, blank, or suppressed

## Repository File Plan

Add or edit:

- `apps/backend/src/civitas/infrastructure/pipelines/school_financial_benchmarks.py`
- `apps/backend/src/civitas/infrastructure/pipelines/contracts/school_financial_benchmarks.py`
- `apps/backend/src/civitas/infrastructure/config/settings.py`
- `apps/backend/src/civitas/infrastructure/pipelines/base.py`
- `apps/backend/src/civitas/infrastructure/pipelines/__init__.py`
- `apps/backend/src/civitas/cli/main.py`
- `apps/backend/alembic/versions/<new>_phase_15_school_financials_yearly.py`

Tests to add:

- `apps/backend/tests/unit/test_school_financial_benchmarks_contract.py`
- `apps/backend/tests/integration/test_school_financial_benchmarks_pipeline.py`

## Vertical Slice Sequence

1. Slice 15B.1:
   - Bronze download
   - workbook manifest
   - worksheet contract tests
2. Slice 15B.2:
   - Silver normalization
   - Gold table migration
   - finance upsert integration tests
3. Slice 15B.3:
   - derived metric computation
   - data-quality thresholds and reject-ratio handling

## Acceptance Criteria

1. Pipeline reruns are idempotent for the same workbook URL.
2. Gold rows only upsert for schools with valid URNs.
3. Derived metrics are deterministic and null-safe.
4. Bronze layout remains compliant with the canonical run-date pipeline root.
5. Finance source freshness is queryable through existing operational patterns.
