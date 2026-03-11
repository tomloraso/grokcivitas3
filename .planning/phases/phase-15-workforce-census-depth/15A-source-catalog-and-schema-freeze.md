# Phase 15 / 15A Design - Source Catalog And Schema Freeze

## Document Control

- Status: Implemented (2026-03-11)
- Last updated: 2026-03-11
- Depends on:
  - `.planning/project-brief.md`
  - `docs/runbooks/pipelines.md`
  - `.planning/phases/phase-6-metrics-parity/M4-workforce-leadership-pipelines.md`

## Objective

Freeze the exact live workforce source catalog and field-level contracts before extending the existing workforce pipeline.

## Verified Release Metadata

Release page:

- `https://explore-education-statistics.service.gov.uk/find-statistics/school-workforce-in-england/2024`

Verified release version id:

- `ba5318f9-2f18-4ef5-8c71-a4db8546758c`

## Approved Bronze Sources

Teacher characteristics ZIP:

- content endpoint:
  - `https://content.explore-education-statistics.service.gov.uk/api/releases/ba5318f9-2f18-4ef5-8c71-a4db8546758c/files/43ec3624-b83f-47e4-8941-2fd2fd6bfd3f`
- ZIP entries include yearly CSVs through:
  - `workforce_teacher_characteristics_school_202425.csv`
- header verified from `workforce_teacher_characteristics_school_202425.csv`:
  - `time_period`
  - `time_identifier`
  - `geographic_level`
  - `country_code`
  - `country_name`
  - `region_code`
  - `region_name`
  - `old_la_code`
  - `new_la_code`
  - `la_name`
  - `school_laestab`
  - `school_urn`
  - `school_name`
  - `school_type`
  - `characteristic_group`
  - `characteristic`
  - `grade`
  - `sex`
  - `age_group`
  - `working_pattern`
  - `qts_status`
  - `on_route`
  - `ethnicity_major`
  - `full_time_equivalent`
  - `headcount`
  - `fte_school_percent`
  - `headcount_school_percent`

Support-staff characteristics ZIP:

- content endpoint:
  - `https://content.explore-education-statistics.service.gov.uk/api/releases/ba5318f9-2f18-4ef5-8c71-a4db8546758c/files/89cc4c08-611b-4dd6-a370-184a205fe9d6`
- ZIP entries include yearly CSVs through:
  - `workforce_support_staff_characteristics_school_202425.csv`
- header verified from `workforce_support_staff_characteristics_school_202425.csv`:
  - `time_period`
  - `time_identifier`
  - `geographic_level`
  - `country_code`
  - `country_name`
  - `region_code`
  - `region_name`
  - `old_la_code`
  - `new_la_code`
  - `la_name`
  - `school_laestab`
  - `school_urn`
  - `school_name`
  - `school_type`
  - `post`
  - `sex`
  - `ethnicity_major`
  - `full_time_equivalent`
  - `headcount`

Teacher pay CSV:

- content endpoint:
  - `https://content.explore-education-statistics.service.gov.uk/api/releases/ba5318f9-2f18-4ef5-8c71-a4db8546758c/files/05001215-c1c7-4210-f9db-08dd8e3a5799`
- verified header:
  - `time_period`
  - `time_identifier`
  - `geographic_level`
  - `country_code`
  - `country_name`
  - `region_code`
  - `region_name`
  - `old_la_code`
  - `new_la_code`
  - `la_name`
  - `school_laestab`
  - `school_urn`
  - `school_name`
  - `school_type`
  - `headcount_all`
  - `average_mean`
  - `average_median`
  - `teachers_on_leadership_pay_range_percent`

Teacher sickness absence CSV:

- content endpoint:
  - `https://content.explore-education-statistics.service.gov.uk/api/releases/ba5318f9-2f18-4ef5-8c71-a4db8546758c/files/9be449b9-57cf-4199-9410-08dd97c8935b`
- verified header:
  - `time_period`
  - `time_identifier`
  - `geographic_level`
  - `country_code`
  - `country_name`
  - `region_code`
  - `region_name`
  - `old_la_code`
  - `new_la_code`
  - `la_name`
  - `school_laestab`
  - `school_urn`
  - `school_name`
  - `school_type`
  - `total_teachers_taking_absence`
  - `percentage_taking_absence`
  - `total_number_of_days_lost`
  - `average_number_of_days_taken`
  - `average_number_of_days_all_teachers`

Teacher vacancies CSV:

- content endpoint:
  - `https://content.explore-education-statistics.service.gov.uk/api/releases/ba5318f9-2f18-4ef5-8c71-a4db8546758c/files/0edf6802-1d84-4a9d-f9bd-08dd8e3a5799`
- verified header:
  - `time_period`
  - `time_identifier`
  - `geographic_level`
  - `country_code`
  - `country_name`
  - `region_code`
  - `region_name`
  - `old_la_code`
  - `new_la_code`
  - `la_name`
  - `school_laestab`
  - `school_urn`
  - `school_name`
  - `school_type`
  - `vacancy`
  - `rate`
  - `tempfilled`
  - `temprate`

Third-party support-staff CSV:

- content endpoint:
  - `https://content.explore-education-statistics.service.gov.uk/api/releases/ba5318f9-2f18-4ef5-8c71-a4db8546758c/files/d9fbbe2a-8106-452f-f9a7-08dd8e3a5799`
- verified header:
  - `time_period`
  - `time_identifier`
  - `geographic_level`
  - `country_code`
  - `country_name`
  - `region_name`
  - `region_code`
  - `la_name`
  - `old_la_code`
  - `new_la_code`
  - `school_laestab`
  - `school_urn`
  - `school_name`
  - `post`
  - `headcount`

## Explicitly Source-Limited Files

Current 2024 size file:

- `https://content.explore-education-statistics.service.gov.uk/api/releases/ba5318f9-2f18-4ef5-8c71-a4db8546758c/files/ed1c5650-9e67-453d-0d91-08ddcde6ffdc`
- verified on 2026-03-09 as a zero-byte CSV payload

Current 2024 teacher-turnover file:

- `https://content.explore-education-statistics.service.gov.uk/api/releases/ba5318f9-2f18-4ef5-8c71-a4db8546758c/files/8aab402f-9fc3-44bf-c16d-08ddd67d4d79`
- verified on 2026-03-09 as a zero-byte CSV payload

Rule:

- do not block the phase on these files
- do not fabricate backfills from undocumented calculations
- keep existing turnover metric behavior unchanged until a non-empty published source is available

## Repository Implementation Plan

1. Extend `apps/backend/src/civitas/infrastructure/pipelines/dfe_workforce.py`.
2. Extend `apps/backend/src/civitas/infrastructure/pipelines/contracts/dfe_workforce.py` or add sub-contract helpers under `contracts/`.
3. Add source config in `apps/backend/src/civitas/infrastructure/config/settings.py`.
4. Add unit tests for each newly approved file contract.

## Acceptance Criteria

1. Every file used by the phase has a verified endpoint and header contract in tests.
2. Empty files are captured as explicit source limitations, not silent parse failures.
3. Existing workforce pipeline behavior remains stable while new files are added.
