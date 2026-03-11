# Phase 19 / 19C Design - API Contract And Web Adoption

## Document Control

- Status: Planned
- Last updated: 2026-03-09
- Depends on:
  - `.planning/phases/phase-20-similar-school-benchmarking/20B-materialization-and-backfill.md`

## Objective

Expose percentile-aware benchmark data through the profile and trends contracts.

## API Additions

For each benchmarked metric, add support for:

- `benchmark_scope`
- `benchmark_value`
- `benchmark_percentile_rank`
- `benchmark_school_count`
- `benchmark_label`

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

1. API payloads can expose both average benchmark values and percentile context.
2. Similar-school scope is clearly labeled in the contract.
3. Existing clients can be migrated without breaking current benchmark use.
