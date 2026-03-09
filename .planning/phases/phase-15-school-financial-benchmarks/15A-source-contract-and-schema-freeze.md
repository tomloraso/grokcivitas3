# Phase 15 / 15A Design - Source Contract And Schema Freeze

## Document Control

- Status: Planned
- Last updated: 2026-03-09
- Depends on:
  - `.planning/project-brief.md`
  - `docs/architecture.md`
  - `docs/architecture/backend-conventions.md`
  - `docs/runbooks/pipelines.md`
  - `.agents/pipelines.md`

## Objective

Freeze the exact annual workbook contract for academy finance ingest before any pipeline code is written.

## Verified External Source

Primary annual workbook:

- `https://financial-benchmarking-and-insights-tool.education.gov.uk/files/AAR_2023-24_download.xlsx`

Verification notes captured on 2026-03-09:

- workbook downloaded successfully
- sheet names present: `Index`, `Academies`, `Central Services`
- school-level rows live in `Academies`
- `Central Services` is trust-level and is out of scope for first implementation

## Approved Bronze Contract

1. Bronze asset format: raw `.xlsx` workbook exactly as published.
2. Bronze discovery rule: configured list of annual workbook URLs in settings.
3. Do not scrape HTML or guess future URLs at runtime.
4. Operator updates the configured annual workbook URL list when a new workbook is published.

## Exact Source Columns Used From `Academies`

Identity and join keys:

- `LAEstab`
- `LA`
- `Estab`
- `URN`
- `Academy UPIN`
- `School Name`
- `MAT/SAT`
- `UID`
- `Trust or Company Name`

School descriptors used for completeness or cohorting:

- `Overall Phase`
- `Phase`
- `Type`
- `Urban/Rural`
- `Region`
- `Admissions policy`
- `% of pupils eligible for FSM`
- `% of pupils with EHCP`
- `% of pupil with SEN support`
- `% of pupils with English as an additional language`
- `Has a 6th form`

Scale inputs:

- `Number of pupils in academy (FTE)`
- `Number of teachers in academy (FTE)`

Income fields:

- `Total Grant Funding`
- `Direct Grants`
- `Targeted Grants`
- `Total Self Generated Funding`
- `Total Income`

Expenditure and balance fields:

- `Teaching staff`
- `Supply teaching staff`
- `Education support staff`
- `Other staff`
- `Total Staff Costs`
- `Maintenance & Improvement Costs`
- `Premises Costs`
- `Total Costs of Educational Supplies`
- `Costs of Brought in Professional Services`
- `Catering Expenses`
- `Total Expenditure`
- `Revenue Reserve`
- `In year balance`

## Silver Staging Schema

Create `school_financials_aar_stage` keyed by `(run_id, academic_year, urn)` with these columns:

- `run_id uuid not null`
- `academic_year text not null`
- `urn bigint not null`
- `school_laestab text null`
- `school_name text not null`
- `trust_uid text null`
- `trust_name text null`
- `phase text null`
- `overall_phase text null`
- `admissions_policy text null`
- `urban_rural text null`
- `pupils_fte numeric(12,2) null`
- `teachers_fte numeric(12,2) null`
- `fsm_pct numeric(5,2) null`
- `ehcp_pct numeric(5,2) null`
- `sen_support_pct numeric(5,2) null`
- `eal_pct numeric(5,2) null`
- `total_grant_funding_gbp numeric(14,2) null`
- `total_self_generated_funding_gbp numeric(14,2) null`
- `total_income_gbp numeric(14,2) null`
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
- `total_expenditure_gbp numeric(14,2) null`
- `revenue_reserve_gbp numeric(14,2) null`
- `in_year_balance_gbp numeric(14,2) null`

## Source Rules

1. Ignore rows without a valid numeric `URN`.
2. Preserve workbook values before derivation; do not overwrite published totals with recomputed totals.
3. Convert percentage fields to numeric percentages in the same scale as source values.
4. Capture workbook year in manifest metadata and normalize `academic_year` as `2023/2024`.
5. Do not ingest `Central Services` in this phase.

## Repository Implementation Plan

1. Add source settings for explicit AAR workbook URLs.
2. Add `school_financial_benchmarks` source registration to:
   - `apps/backend/src/civitas/infrastructure/pipelines/base.py`
   - `apps/backend/src/civitas/infrastructure/pipelines/__init__.py`
   - `apps/backend/src/civitas/cli/main.py`
3. Add new contract module:
   - `apps/backend/src/civitas/infrastructure/pipelines/contracts/school_financial_benchmarks.py`
4. Add unit tests:
   - `apps/backend/tests/unit/test_school_financial_benchmarks_contract.py`

## Acceptance Criteria

1. Source workbook URL and sheet contract are frozen in code and tests.
2. Column-level parsing rules are deterministic and documented.
3. Non-academy or trust-only data is not silently mixed into school-level rows.
