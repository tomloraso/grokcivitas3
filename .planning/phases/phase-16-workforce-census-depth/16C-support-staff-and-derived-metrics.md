# Phase 16 / 16C Design - Support Staff And Derived Metrics

## Document Control

- Status: Planned
- Last updated: 2026-03-09
- Depends on:
  - `.planning/phases/phase-16-workforce-census-depth/16A-source-catalog-and-schema-freeze.md`
  - `.planning/phases/phase-16-workforce-census-depth/16B-teacher-characteristics-pipeline.md`

## Objective

Model support-staff composition and extend `school_workforce_yearly` with pay, absence, vacancy, and external-support metrics.

## Gold Tables

Create `school_support_staff_yearly` keyed by `(urn, academic_year, post, sex, ethnicity_major)`:

- `urn bigint not null`
- `academic_year text not null`
- `post text not null`
- `sex text not null`
- `ethnicity_major text not null`
- `support_staff_fte numeric(12,2) null`
- `support_staff_headcount numeric(12,2) null`

Extend `school_workforce_yearly` with:

- `support_staff_headcount_total numeric(12,2) null`
- `support_staff_fte_total numeric(12,2) null`
- `teaching_assistant_headcount numeric(12,2) null`
- `teaching_assistant_fte numeric(12,2) null`
- `administrative_staff_headcount numeric(12,2) null`
- `auxiliary_staff_headcount numeric(12,2) null`
- `school_business_professional_headcount numeric(12,2) null`
- `leadership_non_teacher_headcount numeric(12,2) null`
- `teacher_average_mean_salary_gbp numeric(14,2) null`
- `teacher_average_median_salary_gbp numeric(14,2) null`
- `teachers_on_leadership_pay_range_pct numeric(7,4) null`
- `teacher_absence_pct numeric(7,4) null`
- `teacher_absence_days_total numeric(12,2) null`
- `teacher_absence_days_average numeric(12,2) null`
- `teacher_absence_days_average_all_teachers numeric(12,2) null`
- `teacher_vacancy_count numeric(12,2) null`
- `teacher_vacancy_rate numeric(7,4) null`
- `teacher_tempfilled_vacancy_count numeric(12,2) null`
- `teacher_tempfilled_vacancy_rate numeric(7,4) null`
- `third_party_support_staff_headcount numeric(12,2) null`

## Source Mapping

Support-staff ZIP:

- `post = 'Teaching assistants'` -> TA totals
- `post = 'Administrative staff'` -> admin totals
- `post = 'Auxiliary staff'` -> auxiliary totals
- `post = 'School business professionals'` -> business-professional totals
- `post = 'Leadership - Non Teacher'` -> non-teacher leadership totals
- `post = 'Other school support staff'` -> residual support totals

Teacher pay CSV:

- `average_mean` -> `teacher_average_mean_salary_gbp`
- `average_median` -> `teacher_average_median_salary_gbp`
- `teachers_on_leadership_pay_range_percent` -> `teachers_on_leadership_pay_range_pct`

Teacher absence CSV:

- `percentage_taking_absence`
- `total_number_of_days_lost`
- `average_number_of_days_taken`
- `average_number_of_days_all_teachers`

Teacher vacancies CSV:

- `vacancy`
- `rate`
- `tempfilled`
- `temprate`

Third-party support CSV:

- use `post = 'Total'` for total contracted support headcount
- retain detailed `post` rows in Silver for auditability

## Repository File Plan

Add or edit:

- `apps/backend/src/civitas/infrastructure/pipelines/dfe_workforce.py`
- `apps/backend/alembic/versions/<new>_phase_16_support_staff_metrics.py`
- `apps/backend/tests/integration/test_dfe_workforce_pipeline.py`
- `apps/backend/tests/unit/test_dfe_workforce_contract.py`

## Vertical Slice Sequence

1. Slice 16C.1:
   - support-staff ZIP ingest and Gold table
2. Slice 16C.2:
   - pay and absence metrics into `school_workforce_yearly`
3. Slice 16C.3:
   - vacancies and third-party support metrics
   - completeness wiring for empty or suppressed values

## Acceptance Criteria

1. Support-staff composition is available historically at school-year grain.
2. New workforce metrics come only from verified school-level files.
3. Existing summary workforce metrics are preserved and not overwritten incorrectly by new joins.
