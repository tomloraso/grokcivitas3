# M4 - Workforce and Leadership Pipelines

## Status

- Implementation completed on 2026-03-05.
- Backend unit/integration quality gate passed.
- Post-M6 full pipeline/API end-to-end validation completed on 2026-03-05.
- Milestone handover state: ready for frontend testing.
- Source-limited metrics explicitly marked and exposed via completeness metadata.

## Goal

Add staffing and leadership context metrics from workforce publications and existing school metadata.

## Gap Coverage

- Pupil-teacher ratio
- Supply/agency staff percentage
- Teachers with 3+ years experience
- Teacher turnover
- QTS percentage
- Staff qualifications and leadership details where available

## Source Strategy

- New external sources required for workforce metrics (DfE School Workforce publications/API).
- Existing source extension for leadership where available in GIAS/Ofsted metadata.
- Mandatory endpoint/file schema inspection before normalization contract design.

## Bronze -> Silver -> Gold Plan

1. Bronze:
   - add workforce source download and manifest with release metadata.
2. Silver:
   - normalize yearly workforce rows and leadership attributes.
3. Gold:
   - add `school_workforce_yearly` keyed by `(urn, academic_year)`;
   - add/update leadership snapshot table if required for non-yearly fields.

## API Plan

1. Extend profile with workforce latest values and leadership snapshot.
2. Extend trends endpoint with workforce series where available.
3. Add completeness sections for workforce and leadership.

## Frontend Plan

1. Add staffing cards and trend indicators to the profile page.
2. Add leadership metadata block with explicit source freshness.
3. Ensure unavailable source conditions render deterministic copy.

## Validation and Gates

- Schema-contract tests and representative normalization fixtures.
- Profile/trends integration coverage for workforce metrics.
- Performance checks for added joins and payload size.

## Source Validation Evidence

- Workforce publication and release page schema inspected directly:
  - `https://explore-education-statistics.service.gov.uk/find-statistics/school-workforce-in-england/<release-slug>`
  - Parsed `__NEXT_DATA__` release payload keys used by implementation:
    - `props.pageProps.releaseVersion.id`
    - `props.pageProps.releaseVersion.downloadFiles[]`
- School-level workforce CSV row normalization contract implemented and tested for:
  - URN validation
  - academic-year normalization
  - suppression token handling
  - metric-level numeric validation/rejection
- 2026-03-05 closeout source check:
  - 2022 release includes school-level size and PTR files; supply/QTS can be derived from school-level headcount columns.
  - 2023 release includes school-level size and PTR files; supply/QTS can be derived from school-level headcount columns.
  - 2024 release school-level size file currently returns empty payload; pipeline falls back to school-level PTR file.
  - Teacher turnover school-level file in 2024 currently returns empty payload.
  - Teacher qualifications / teacher characteristics files in current releases are not consistently school-level for the required metrics.

## Implementation Notes

1. Gold schema extended via migration `20260305_17_phase_m4_workforce_leadership.py`:
   - Added `school_workforce_yearly` keyed by `(urn, academic_year)`.
   - Added `school_leadership_snapshot` keyed by `urn`.
2. Added new source pipeline and contract:
   - `dfe_workforce` with contract `dfe_workforce.v1`.
3. Extended profile payload:
   - `workforce_latest`
   - `leadership_snapshot`
   - completeness sections for workforce/leadership.
4. Extended trends payload:
   - workforce series (`pupil_teacher_ratio`, `supply_staff_pct`, `teachers_with_3plus_years_pct`, `teacher_turnover_pct`, `qts_pct`, `staff_with_relevant_qualification_pct`)
   - section completeness for workforce.
5. Extended data-quality coverage:
   - Added workforce and leadership sections in operations models/repository mapping.
6. Extended settings/pipeline wiring:
   - Added publication/release/lookback/strict-mode config
   - Added source-specific reject-ratio and freshness-SLA config for `dfe_workforce`.
7. 2026-03-05 QA regression fix:
   - Updated default workforce release slugs to live year-format values (`2022,2023,2024`).
   - Relaxed release-slug validation to support year and term slugs.
8. 2026-03-05 closeout fixes:
   - Added release-file selection fallback to prefer school-level size file and fall back to school-level PTR file when needed.
   - Added derived `supply_staff_pct` and `qts_pct` from published school-level counts.
   - Preserved non-null metric values when multiple release assets contribute overlapping academic years.

## Validation Evidence

- Command:
  - `uv run --project apps/backend pytest apps/backend/tests/unit/test_dfe_workforce_contract.py apps/backend/tests/integration/test_dfe_workforce_pipeline.py apps/backend/tests/unit/test_pipeline_contract_metadata.py apps/backend/tests/unit/test_pipeline_cli.py apps/backend/tests/unit/test_settings.py apps/backend/tests/unit/test_get_school_profile_use_case.py apps/backend/tests/unit/test_cached_school_profile_repository.py apps/backend/tests/unit/test_api_contract_checks.py apps/backend/tests/unit/test_get_school_trends_use_case.py apps/backend/tests/integration/test_school_profile_repository.py apps/backend/tests/integration/test_school_profile_api.py apps/backend/tests/integration/test_school_trends_repository.py apps/backend/tests/integration/test_school_trends_api.py apps/backend/tests/integration/test_data_quality_repository.py -q`
- Result:
  - `68 passed`

## Post-M6 Validation Evidence

- Command:
  - `uv run --project apps/backend pytest apps/backend/tests/unit/test_demographics_spc_contract.py apps/backend/tests/unit/test_demographics_sen_contract.py apps/backend/tests/unit/test_dfe_attendance_contract.py apps/backend/tests/unit/test_dfe_behaviour_contract.py apps/backend/tests/unit/test_dfe_workforce_contract.py apps/backend/tests/unit/test_uk_house_prices_contract.py apps/backend/tests/unit/test_ons_imd_transforms.py apps/backend/tests/unit/test_pipeline_cli.py apps/backend/tests/unit/test_pipeline_contract_metadata.py apps/backend/tests/unit/test_settings.py apps/backend/tests/integration/test_demographics_release_files_pipeline.py apps/backend/tests/integration/test_dfe_characteristics_pipeline.py apps/backend/tests/integration/test_dfe_attendance_pipeline.py apps/backend/tests/integration/test_dfe_behaviour_pipeline.py apps/backend/tests/integration/test_dfe_workforce_pipeline.py apps/backend/tests/integration/test_ons_imd_pipeline.py apps/backend/tests/integration/test_uk_house_prices_pipeline.py apps/backend/tests/integration/test_data_quality_repository.py apps/backend/tests/integration/test_school_profile_repository.py apps/backend/tests/integration/test_school_profile_api.py apps/backend/tests/unit/test_get_school_profile_use_case.py apps/backend/tests/unit/test_cached_school_profile_repository.py apps/backend/tests/integration/test_school_trends_repository.py apps/backend/tests/integration/test_school_trends_api.py apps/backend/tests/unit/test_get_school_trends_use_case.py apps/backend/tests/unit/test_api_contract_checks.py -q`
- Result:
  - `129 passed`
