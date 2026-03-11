# Phase 17 / 17A Design - Join-Key Foundation And Source Contract

## Document Control

- Status: Implemented (2026-03-11)
- Last updated: 2026-03-11
- Depends on:
  - `.planning/project-brief.md`
  - `.planning/phases/phase-0/0B-gias-pipeline.md`

## Objective

Persist the school identifiers required for admissions joins and freeze the source contract for the verified school-level admissions CSV.

## Verified External Source

Release page:

- `https://explore-education-statistics.service.gov.uk/find-statistics/primary-and-secondary-school-applications-and-offers/2025-26`

Verified release version id:

- `5ed40264-1835-4848-a29b-446ed6c075c2`

Verified school-level content endpoint:

- `https://content.explore-education-statistics.service.gov.uk/api/releases/5ed40264-1835-4848-a29b-446ed6c075c2/files/7c9894e4-9038-4213-823c-bf50bc993cec`

## Verified Source Header

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
- `school_phase`
- `school_laestab_as_used`
- `number_preferences_la`
- `school_name`
- `total_number_places_offered`
- `number_preferred_offers`
- `number_1st_preference_offers`
- `number_2nd_preference_offers`
- `number_3rd_preference_offers`
- `times_put_as_any_preferred_school`
- `times_put_as_1st_preference`
- `times_put_as_2nd_preference`
- `times_put_as_3rd_preference`
- `proportion_1stprefs_v_1stprefoffers`
- `proportion_1stprefs_v_totaloffers`
- `all_applications_from_another_LA`
- `offers_to_applicants_from_another_LA`
- `establishment_type`
- `denomination`
- `FSM_eligible_percent`
- `admissions_policy`
- `urban_rural`
- `allthrough_school`
- `parliamentary_constituency_code`
- `parliamentary_constituency_name`
- `school_urn`
- `entry_year`

## Join-Key Foundation

The current school model is URN-led, but admissions needs both URN and a stable establishment join key.

Add or persist on the school dimension:

- `establishment_number text null`
- `school_laestab text null`

Rules:

1. `school_laestab = <numeric DfE local authority code><4-digit establishment number>`.
2. Use the numeric DfE local authority code that aligns with admissions `old_la_code`, not the ONS `new_la_code`.
3. Zero-pad establishment number to four digits before concatenation.
4. Preserve the exact admissions source value `school_laestab_as_used` in Silver for auditability.
5. Join precedence:
   - first by `school_urn` when present
   - then validate against `school_laestab`
   - reject ambiguous mismatches into pipeline diagnostics

## Repository File Plan

Add or edit:

- `apps/backend/src/civitas/infrastructure/pipelines/gias.py`
- `apps/backend/alembic/versions/<new>_phase_17_gias_join_keys.py`
- `apps/backend/tests/integration/test_gias_pipeline.py`
- `apps/backend/tests/unit/test_gias_contract.py`

## Acceptance Criteria

1. School rows persist both URN and `school_laestab`.
2. Admissions rows can be matched deterministically to existing school rows.
3. Mismatched join keys are visible in run diagnostics.
