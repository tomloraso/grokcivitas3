# M2 - Demographics and Support Depth

## Status

- Implementation completed on 2026-03-05.
- Source-limited metrics explicitly marked and exposed via coverage/completeness metadata.
- Backend unit/integration quality gate passed.
- Post-M6 full pipeline/API end-to-end validation completed on 2026-03-05.
- Milestone handover state: ready for frontend testing.

## Goal

Complete the remaining demographics/support metrics not yet exposed from current school-level datasets.

## Gap Coverage

- FSM6
- SEND primary need categories
- Gender breakdown (% male / % female)
- Pupil mobility / turnover
- Top 5 home languages (if school-level published)

## Source Strategy

1. Existing ingested source extension first:
   - evaluate SPC/SEN school-level files already downloaded via `dfe_characteristics` for required columns.
2. If unavailable, add a new DfE source slice and document school-level publication limits.

## Bronze -> Silver -> Gold Plan

1. Bronze:
   - keep current release-file discovery for SPC/SEN;
   - if required, add a new publication slug/file-discovery path for missing fields.
2. Silver:
   - extend normalization contracts for supported columns and suppression tokens.
3. Gold:
   - extend `school_demographics_yearly` with typed columns for supported metrics;
   - if high-cardinality primary needs/languages require multiple rows, add dedicated yearly child tables keyed by `(urn, academic_year, category)`.

## API Plan

1. Extend profile response demographics payload with newly supported fields.
2. Add completeness reason codes for unpublishable school-level fields.
3. Keep unsupported list aligned with actual source publication behavior.

## Frontend Plan

1. Add new demographic cards and ranked lists for categories.
2. Reuse existing coverage notice pattern for unsupported/not-published fields.
3. Add trend visual support where multi-year values are present.

## Validation and Gates

- Source-contract tests for each new mapped column.
- Integration tests for demographics/profile payload parity.
- Explicit documentation for any metric still unavailable due source policy.

## Source Validation Evidence

- Release-file headers confirmed from staged SPC/SEN CSV payloads:
  - SPC:
    - `% of pupils known to be eligible for free school meals (Performance Tables)` (FSM6 proxy)
    - `headcount total male` / `headcount total female` (gender derivation available for recent releases)
    - `Number of pupils (used for FSM calculation in Performance Tables)` (gender denominator for derivation)
    - `number of pupils whose first language is known or believed to be English/other than English/unclassified`
    - Note: detailed per-language school-level columns for top-5 language ranking are not published in current SPC releases.
    - Note: school-level pupil-mobility percentage columns are not published in current SPC releases.
  - SEN:
    - `number of pupils with <need> as primary need`
    - `% of pupils with <need> as primary need`

## Implementation Notes

1. Gold schema extended via migration `20260305_15_phase_m2_demographics_support_depth.py`:
   - Added `fsm6_pct`, `male_pct`, `female_pct`, `pupil_mobility_pct` to `school_demographics_yearly`.
   - Added support flags:
     - `has_fsm6_data`
     - `has_gender_data`
     - `has_mobility_data`
     - `has_send_primary_need_data`
   - Added child tables:
     - `school_send_primary_need_yearly`
     - `school_home_language_yearly`
2. Silver normalization contracts extended:
   - `contracts/demographics_spc.py` now maps FSM6, derives gender percentage where published headcount+denominator columns exist, and keeps unsupported mobility/top-language coverage flags explicit.
   - `contracts/demographics_sen.py` now maps SEND primary-need categories.
3. Release-files pipeline extended end-to-end:
   - Stages and promotes new scalar metrics and support flags.
   - Upserts send-primary-need and home-language child rows.
   - Cleans stale category rows during promote.
4. API/domain/application extensions completed:
   - School profile demographics include new metrics, support flags, and category lists.
   - School trends include new demographic series (`fsm6`, `male`, `female`, `mobility`).
5. Cleanup fix delivered:
   - Suppressed home-language rows are now filtered out of ranked outputs.
6. 2026-03-05 closeout fix:
   - Added gender derivation from published SPC headcount columns (`headcount total male/female`) using published total-pupil denominator.

## Validation Evidence

- Command:
  - `uv run --project apps/backend pytest apps/backend/tests/unit/test_demographics_spc_contract.py apps/backend/tests/unit/test_demographics_sen_contract.py apps/backend/tests/unit/test_get_school_trends_use_case.py apps/backend/tests/integration/test_demographics_release_files_pipeline.py apps/backend/tests/integration/test_dfe_characteristics_pipeline.py apps/backend/tests/integration/test_data_quality_repository.py apps/backend/tests/integration/test_school_profile_repository.py apps/backend/tests/integration/test_school_profile_api.py apps/backend/tests/integration/test_school_trends_repository.py apps/backend/tests/integration/test_school_trends_api.py -q`
- Result:
  - `36 passed`

## Post-M6 Validation Evidence

- Command:
  - `uv run --project apps/backend pytest apps/backend/tests/unit/test_demographics_spc_contract.py apps/backend/tests/unit/test_demographics_sen_contract.py apps/backend/tests/unit/test_dfe_attendance_contract.py apps/backend/tests/unit/test_dfe_behaviour_contract.py apps/backend/tests/unit/test_dfe_workforce_contract.py apps/backend/tests/unit/test_uk_house_prices_contract.py apps/backend/tests/unit/test_ons_imd_transforms.py apps/backend/tests/unit/test_pipeline_cli.py apps/backend/tests/unit/test_pipeline_contract_metadata.py apps/backend/tests/unit/test_settings.py apps/backend/tests/integration/test_demographics_release_files_pipeline.py apps/backend/tests/integration/test_dfe_characteristics_pipeline.py apps/backend/tests/integration/test_dfe_attendance_pipeline.py apps/backend/tests/integration/test_dfe_behaviour_pipeline.py apps/backend/tests/integration/test_dfe_workforce_pipeline.py apps/backend/tests/integration/test_ons_imd_pipeline.py apps/backend/tests/integration/test_uk_house_prices_pipeline.py apps/backend/tests/integration/test_data_quality_repository.py apps/backend/tests/integration/test_school_profile_repository.py apps/backend/tests/integration/test_school_profile_api.py apps/backend/tests/unit/test_get_school_profile_use_case.py apps/backend/tests/unit/test_cached_school_profile_repository.py apps/backend/tests/integration/test_school_trends_repository.py apps/backend/tests/integration/test_school_trends_api.py apps/backend/tests/unit/test_get_school_trends_use_case.py apps/backend/tests/unit/test_api_contract_checks.py -q`
- Result:
  - `129 passed`
