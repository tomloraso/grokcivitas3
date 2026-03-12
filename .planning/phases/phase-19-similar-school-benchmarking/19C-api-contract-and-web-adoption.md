# Phase 19 / 19C Design - API Contract And Web Adoption

## Document Control

- Status: Completed
- Last updated: 2026-03-12
- Depends on:
  - `.planning/phases/phase-19-similar-school-benchmarking/19B-materialization-and-backfill.md`

## Objective

Expose percentile-aware benchmark data through the profile and trends contracts.

## API Additions

For each benchmarked metric, add support for:

- existing average benchmark values that preserve the current `national_*` plus local scope/value shape
- additive benchmark `contexts[]` entries carrying percentile-aware metadata per scope

Each benchmark context entry exposes:

- `scope`
- `label`
- `value`
- `percentile_rank`
- `school_count`

Required scopes:

- `national`
- `local_authority_district`
- `phase`
- `similar_school`

## Web Adoption Rules

1. Existing inline benchmark bars can continue to use average values during the transition.
2. Similar-school percentile context should be additive, not a replacement for raw metric values.
3. Do not introduce qualitative labels such as "good" or "bad" based solely on percentile rank.

## Repository File Plan

Backend:

- `apps/backend/src/civitas/infrastructure/persistence/postgres_school_profile_repository.py`
- `apps/backend/src/civitas/infrastructure/persistence/postgres_school_trends_repository.py`
- `apps/backend/src/civitas/application/school_profiles/`
- `apps/backend/src/civitas/application/school_trends/`

Frontend follow-on:

- profile stat-card benchmark surface
- trend dashboard benchmark drill-down
- compare page benchmark blocks where applicable

## Acceptance Criteria

1. API payloads can expose both average benchmark values and additive percentile contexts.
2. Similar-school scope is clearly labeled in the contract.
3. Existing clients can be migrated without breaking current benchmark use.

## Implemented State

- Backend contracts now expose additive benchmark `contexts[]` entries on:
  - school profile benchmark metrics
  - school trends benchmark points
  - school compare benchmark payloads
- The contract shape ships with:
  - `scope`
  - `label`
  - `value`
  - `percentile_rank`
  - `school_count`
  - optional `area_code`
- School profile benchmark cards now surface similar-school value, percentile rank, and cohort size alongside the existing local/national benchmark rows.
- Frontend mapper coverage now asserts that similar-school context is mapped from API responses into the school-profile view model.
- School profile UI coverage now asserts that similar-school label, formatted value, percentile copy, and cohort size render in the benchmark card surface.

## Deviations

- Compare web rendering still uses the existing benchmark-label presentation and does not yet render the additive `contexts[]` payload. The compare API contract is ready, but compare UI adoption remains follow-up work.
- The original file plan referenced `postgres_school_profile_repository.py`; the shipped profile contract wiring reuses benchmark rows from the school trends repository/use case instead.

## Validation

- `uv run --project apps/backend pytest apps/backend/tests/integration/test_school_compare_api.py apps/backend/tests/integration/test_school_trends_api.py -q`
  - Result: `10 passed`.
- `npm test -- --runInBand src/features/school-profile/mappers/profileMapper.test.ts src/features/school-profile/school-profile.test.tsx`
  - Result: `21 passed`.
- `make lint`
  - Result: passed.
- `make test`
  - Result: passed.

## Completion Note

- 19C is complete for the shipped profile/trends/contract adoption scope and is included in Phase 19 sign-off.
