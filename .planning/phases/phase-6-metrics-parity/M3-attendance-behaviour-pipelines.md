# M3 - Attendance and Behaviour Pipelines

## Status

- Implementation completed on 2026-03-05.
- Backend unit/integration quality gate passed.
- Post-M6 full pipeline/API end-to-end validation completed on 2026-03-05.
- Milestone handover state: ready for frontend testing.

## Goal

Introduce attendance and behaviour metrics with three-year history.

## Gap Coverage

- Overall attendance rate
- Persistent absence rate (trend)
- Suspensions and permanent exclusions (trend)

## Source Strategy

- New external sources required (DfE statistics data-sets for attendance and exclusions).
- Mandatory pre-build step: call source endpoints directly and capture real schema keys before contract design.

## Bronze -> Silver -> Gold Plan

1. Bronze:
   - add source pipelines for attendance and exclusions dataset downloads;
   - persist manifests with dataset id/version, indicator/filter ids, and checksums.
2. Silver:
   - normalize to school-level yearly rows with explicit suppression handling.
3. Gold:
   - add `school_attendance_yearly` and `school_behaviour_yearly` tables keyed by `(urn, academic_year)`.

## API Plan

1. Extend profile response with latest attendance/behaviour slice.
2. Extend trends endpoint for attendance and behaviour series.
3. Add completeness section metadata for both domains.

## Frontend Plan

1. Add attendance/behaviour panels with latest values + sparkline deltas.
2. Integrate with existing completeness notice and unsupported messaging.
3. Add regression tests for mixed coverage schools.

## Validation and Gates

- Endpoint schema evidence committed to planning notes.
- Pipeline unit tests for filter/indicator mapping and suppression parsing.
- Integration tests for profile + trends payload additions.
- Data quality gates for reject ratio, row counts, and freshness SLA.

## Source Validation Evidence

- Attendance publication and release page schema inspected directly:
  - `https://explore-education-statistics.service.gov.uk/find-statistics/pupil-absence-in-schools-in-england/<release-slug>`
  - Parsed `__NEXT_DATA__` release payload keys used by implementation:
    - `props.pageProps.releaseVersion.id`
    - `props.pageProps.releaseVersion.downloadFiles[]`
- Behaviour publication and release page schema inspected directly:
  - `https://explore-education-statistics.service.gov.uk/find-statistics/suspensions-and-permanent-exclusions-in-england/<release-slug>`
  - Parsed `__NEXT_DATA__` release payload keys used by implementation:
    - `props.pageProps.releaseVersion.id`
    - `props.pageProps.releaseVersion.downloadFiles[]`
- School-level CSV row normalization contract implemented and tested for:
  - URN validation
  - academic-year normalization
  - suppression token handling
  - metric-level numeric validation/rejection

## Implementation Notes

1. Gold schema extended via migration `20260305_16_phase_m3_attendance_behaviour.py`:
   - Added `school_attendance_yearly` keyed by `(urn, academic_year)`.
   - Added `school_behaviour_yearly` keyed by `(urn, academic_year)`.
2. Added new source pipelines and contracts:
   - `dfe_attendance` with contract `dfe_attendance.v1`.
   - `dfe_behaviour` with contract `dfe_behaviour.v1`.
3. Extended profile payload:
   - `attendance_latest`
   - `behaviour_latest`
   - completeness sections for attendance/behaviour.
4. Extended trends payload:
   - attendance series (`overall_attendance_pct`, `overall_absence_pct`, `persistent_absence_pct`)
   - behaviour series (`suspensions_count`, `suspensions_rate`, `permanent_exclusions_count`, `permanent_exclusions_rate`)
   - section completeness for demographics/attendance/behaviour.
5. Extended data-quality coverage:
   - Added attendance and behaviour sections in operations models/repository mapping.
6. Extended settings/pipeline wiring:
   - Added publication/release/lookback/strict-mode config
   - Added source-specific reject-ratio and freshness-SLA config.
7. 2026-03-05 QA regression fix:
   - Updated default behaviour publication slug to `suspensions-and-permanent-exclusions-in-england`.
   - Relaxed release-slug validation to support live slug formats (for example `2024-25-autumn-term`).

## Validation Evidence

- Command:
  - `uv run --project apps/backend pytest apps/backend/tests/unit/test_dfe_attendance_contract.py apps/backend/tests/unit/test_dfe_behaviour_contract.py apps/backend/tests/unit/test_pipeline_contract_metadata.py apps/backend/tests/unit/test_pipeline_cli.py apps/backend/tests/unit/test_get_school_profile_use_case.py apps/backend/tests/unit/test_get_school_trends_use_case.py apps/backend/tests/unit/test_cached_school_profile_repository.py apps/backend/tests/unit/test_api_contract_checks.py apps/backend/tests/unit/test_settings.py apps/backend/tests/integration/test_dfe_attendance_pipeline.py apps/backend/tests/integration/test_dfe_behaviour_pipeline.py apps/backend/tests/integration/test_school_profile_repository.py apps/backend/tests/integration/test_school_profile_api.py apps/backend/tests/integration/test_school_trends_repository.py apps/backend/tests/integration/test_school_trends_api.py apps/backend/tests/integration/test_data_quality_repository.py -q`
- Result:
  - `81 passed`

## Post-M6 Validation Evidence

- Command:
  - `uv run --project apps/backend pytest apps/backend/tests/unit/test_demographics_spc_contract.py apps/backend/tests/unit/test_demographics_sen_contract.py apps/backend/tests/unit/test_dfe_attendance_contract.py apps/backend/tests/unit/test_dfe_behaviour_contract.py apps/backend/tests/unit/test_dfe_workforce_contract.py apps/backend/tests/unit/test_uk_house_prices_contract.py apps/backend/tests/unit/test_ons_imd_transforms.py apps/backend/tests/unit/test_pipeline_cli.py apps/backend/tests/unit/test_pipeline_contract_metadata.py apps/backend/tests/unit/test_settings.py apps/backend/tests/integration/test_demographics_release_files_pipeline.py apps/backend/tests/integration/test_dfe_characteristics_pipeline.py apps/backend/tests/integration/test_dfe_attendance_pipeline.py apps/backend/tests/integration/test_dfe_behaviour_pipeline.py apps/backend/tests/integration/test_dfe_workforce_pipeline.py apps/backend/tests/integration/test_ons_imd_pipeline.py apps/backend/tests/integration/test_uk_house_prices_pipeline.py apps/backend/tests/integration/test_data_quality_repository.py apps/backend/tests/integration/test_school_profile_repository.py apps/backend/tests/integration/test_school_profile_api.py apps/backend/tests/unit/test_get_school_profile_use_case.py apps/backend/tests/unit/test_cached_school_profile_repository.py apps/backend/tests/integration/test_school_trends_repository.py apps/backend/tests/integration/test_school_trends_api.py apps/backend/tests/unit/test_get_school_trends_use_case.py apps/backend/tests/unit/test_api_contract_checks.py -q`
- Result:
  - `129 passed`
