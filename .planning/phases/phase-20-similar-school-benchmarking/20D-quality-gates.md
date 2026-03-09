# Phase 20 / 20D Design - Quality Gates

## Document Control

- Status: Planned
- Last updated: 2026-03-09

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
