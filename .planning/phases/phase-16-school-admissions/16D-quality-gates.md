# Phase 16 / 16D Design - Quality Gates

## Document Control

- Status: Implemented (2026-03-11)
- Last updated: 2026-03-11

## Required Commands

- `uv run --project apps/backend pytest apps/backend/tests/unit/test_gias_contract.py apps/backend/tests/integration/test_gias_pipeline.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/unit/test_school_admissions_contract.py apps/backend/tests/integration/test_school_admissions_pipeline.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/integration/test_school_profile_repository.py apps/backend/tests/integration/test_school_profile_api.py apps/backend/tests/integration/test_school_trends_repository.py apps/backend/tests/integration/test_school_trends_api.py -q`
- `make lint`
- `make test`

## Data Quality Gates

1. Bronze manifest captures the exact release version id and file id.
2. Join-key mismatch rate is reported and must remain below an agreed threshold before release.
3. Derived ratios are validated against source-published ratio columns on a representative sample.
4. API completeness semantics distinguish no-row, suppressed-value, and unsupported-year conditions.

## Exit Criteria

- One admissions sample school can be traced Bronze -> Silver -> Gold -> profile/trends.
- GIAS join-key persistence is live and regression-tested.
- Benchmark materialization can run with admissions metrics without schema conflicts.
