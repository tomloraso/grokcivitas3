# Phase 19 / 19D Design - Serving Contract And Quality Gates

## Document Control

- Status: Planned
- Last updated: 2026-03-11

## Serving Summary Model

Create a serving-facing summary table or materialized Gold table:

- `school_subject_summary_yearly`

Key:

- `(urn, academic_year, key_stage, qualification_family, exam_cohort, subject)`

Columns:

- `urn bigint not null`
- `academic_year text not null`
- `key_stage text not null`
- `qualification_family text not null`
- `exam_cohort text null`
- `subject text not null`
- `source_version text not null`
- `entries_count_total integer not null`
- `high_grade_count integer null`
- `high_grade_share_pct numeric(7,4) null`
- `pass_grade_count integer null`
- `pass_grade_share_pct numeric(7,4) null`
- `ranking_eligible boolean not null`

## Summary Rules

1. Build the summary from detailed Gold rows after selecting one canonical `source_version` per business grain.
2. Canonical source-version precedence is:
   - `final`
   - `revised`
   - `provisional`
   - `unknown`
3. If multiple rows tie after precedence, break ties deterministically by latest persisted `source_downloaded_at_utc`, then lexical `source_version`.
4. Exclude `All subjects` from strongest or weakest subject rankings.
5. Set `ranking_eligible = false` when `entries_count_total < 5`.
6. Grade-band mapping:
   - KS4 `9 to 1`: high grades `7, 8, 9`; pass grades `4, 5, 6, 7, 8, 9`
   - KS4 letter grades: high grades `A*, A`; pass grades `A*, A, B, C`
   - 16-18 A level style: high grades `A*, A`; pass grades `A*, A, B, C, D, E`
7. If a qualification uses a different grade structure, the mapping must be explicitly tested before it is ranked.
8. If a qualification family or exam cohort is not explicitly approved for ranking, persist the summary row with `ranking_eligible = false` rather than collapsing or omitting it.

## Serving Additions

Profile latest:

- strongest subjects list
- weakest subjects list
- subject breakdown by stage, qualification family, and exam cohort

Release sequencing rule:

- profile/API exposure for KS4 may ship as part of the 4-16 MVP
- 16-18 summary rows may be materialized in Gold earlier, but public serving remains gated behind an explicit product decision or brief update

Trend additions:

- subject summaries by academic year, stage, qualification family, and exam cohort

Required tests to add or extend:

- version-selection tests for provisional/revised/final precedence
- grade-band mapping tests per supported `grade_structure`
- ranking-eligibility tests for low-entry and unsupported qualification/cohort cases
- repository/API integration coverage for latest profile and trends reads

## Required Commands

- `uv run --project apps/backend pytest apps/backend/tests/unit/test_ks4_subject_performance_contract.py apps/backend/tests/integration/test_ks4_subject_performance_pipeline.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/unit/test_16_to_18_subject_performance_contract.py apps/backend/tests/integration/test_16_to_18_subject_performance_pipeline.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/integration/test_school_subject_summary_materialization.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/integration/test_school_profile_repository.py apps/backend/tests/integration/test_school_profile_api.py apps/backend/tests/integration/test_school_trends_repository.py apps/backend/tests/integration/test_school_trends_api.py -q`
- `make lint`
- `make test`

## Exit Criteria

- Subject summaries can be served without reading raw CSVs at request time.
- Ranking rules are explicit and tested.
- No school-level subject value-added claims appear in the API or UI.
