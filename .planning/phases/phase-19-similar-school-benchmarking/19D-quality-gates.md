# Phase 19 / 19D Design - Quality Gates

## Document Control

- Status: Completed
- Last updated: 2026-03-12

## Required Commands

- `uv run --project apps/backend pytest apps/backend/tests/integration/test_school_trends_repository.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/integration/test_school_profile_repository.py apps/backend/tests/integration/test_school_profile_api.py apps/backend/tests/integration/test_school_trends_api.py -q`
- `make lint`
- `make test`

## Data Quality Gates

1. Cohort membership is deterministic for a fixed academic year and source state.
2. Percentile distributions are monotonic and internally consistent.
3. Similar-school cohorts below minimum size are either widened deterministically or omitted with explicit completeness semantics.
4. Benchmark computation remains off the request path.

## Exit Criteria

- One metric can be traced through cohort build, distribution materialization, percentile rank, and API response.
- Legacy average scopes remain available during rollout.
- Similar-school percentile context is available without request-time SQL explosion.

## Validation Run Log

- 2026-03-12: `uv run --project apps/backend pytest apps/backend/tests/integration/test_school_trends_repository.py -q`
  - Result: `8 skipped` in this environment.
- 2026-03-12: `uv run --project apps/backend pytest apps/backend/tests/integration/test_school_compare_api.py apps/backend/tests/integration/test_school_trends_api.py -q`
  - Result: `10 passed`.
- 2026-03-12: `uv run --project apps/backend pytest apps/backend/tests/unit/test_materialize_school_benchmarks_use_case.py apps/backend/tests/unit/test_pipeline_cli.py -q`
  - Result: `34 passed`.
- 2026-03-12: `npm test -- --runInBand src/features/school-profile/mappers/profileMapper.test.ts src/features/school-profile/school-profile.test.tsx`
  - Result: `21 passed`.
- 2026-03-12: `make lint`
  - Result: passed.
- 2026-03-12: `make test`
  - Result: backend `478 passed, 57 skipped`; web `243 passed`.

## Sign-Off Assessment

- Exit criteria satisfied for the shipped Phase 19 scope.
- The skipped repository/infrastructure integration tests remain environment-dependent rather than product regressions; the API, unit, and repo-wide gates that were runnable all passed.
- Phase 19 is signed off on 2026-03-12.

## Follow-Up Work

- Add compare-page rendering for additive benchmark contexts if the compare experience needs to expose similar-school context directly.
- Revisit incremental URN-scoped benchmark materialization only if cache-wide rebuild cost becomes an operational problem.
