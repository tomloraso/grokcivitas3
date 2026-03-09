# Phase 19 / 19D Design - Serving Contract And Quality Gates

## Document Control

- Status: Planned
- Last updated: 2026-03-09

## Serving Summary Model

Create a serving-facing summary table or materialized Gold table:

- `school_subject_summary_yearly`

Key:

- `(urn, academic_year, key_stage, subject)`

Columns:

- `urn bigint not null`
- `academic_year text not null`
- `key_stage text not null`
- `subject text not null`
- `entries_count_total integer not null`
- `high_grade_count integer null`
- `high_grade_share_pct numeric(7,4) null`
- `pass_grade_count integer null`
- `pass_grade_share_pct numeric(7,4) null`
- `ranking_eligible boolean not null`

## Summary Rules

1. Exclude `All subjects` from strongest or weakest subject rankings.
2. Set `ranking_eligible = false` when `entries_count_total < 5`.
3. Grade-band mapping:
   - KS4 `9 to 1`: high grades `7, 8, 9`; pass grades `4, 5, 6, 7, 8, 9`
   - KS4 letter grades: high grades `A*, A`; pass grades `A*, A, B, C`
   - 16-18 A level style: high grades `A*, A`; pass grades `A*, A, B, C, D, E`
4. If a qualification uses a different grade structure, the mapping must be explicitly tested before it is ranked.

## Serving Additions

Profile latest:

- strongest subjects list
- weakest subjects list
- subject breakdown by stage

Trend additions:

- subject summaries by academic year and stage

## Required Commands

- `uv run --project apps/backend pytest apps/backend/tests/unit/test_ks4_subject_performance_contract.py apps/backend/tests/integration/test_ks4_subject_performance_pipeline.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/unit/test_16_to_18_subject_performance_contract.py apps/backend/tests/integration/test_16_to_18_subject_performance_pipeline.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/integration/test_school_profile_repository.py apps/backend/tests/integration/test_school_profile_api.py apps/backend/tests/integration/test_school_trends_repository.py apps/backend/tests/integration/test_school_trends_api.py -q`
- `make lint`
- `make test`

## Exit Criteria

- Subject summaries can be served without reading raw CSVs at request time.
- Ranking rules are explicit and tested.
- No school-level subject value-added claims appear in the API or UI.
