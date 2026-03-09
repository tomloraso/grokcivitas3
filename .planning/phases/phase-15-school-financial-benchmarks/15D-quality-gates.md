# Phase 15 / 15D Design - Quality Gates

## Document Control

- Status: Planned
- Last updated: 2026-03-09

## Required Test Commands

- `uv run --project apps/backend pytest apps/backend/tests/unit/test_school_financial_benchmarks_contract.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/integration/test_school_financial_benchmarks_pipeline.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/integration/test_school_profile_repository.py apps/backend/tests/integration/test_school_profile_api.py apps/backend/tests/integration/test_school_trends_repository.py apps/backend/tests/integration/test_school_trends_api.py apps/backend/tests/integration/test_data_quality_repository.py -q`
- `make lint`
- `make test`

## Data Quality Gates

1. Bronze manifest captures workbook URL, checksum, sheet list, and row counts.
2. Silver rejects rows with invalid URNs or non-numeric core money fields where numeric values are required.
3. Gold derived metrics do not divide by zero.
4. Finance row counts and populated-metric ratios are captured in operational validation.

## Implementation Sign-Off Checklist

1. Verified workbook URL is committed to settings defaults or documented operator config.
2. Gold schema migration is reversible and uses consistent naming with existing yearly tables.
3. Profile and trends API contracts are updated in the same PR as persistence changes.
4. Benchmark materialization is rerun manually after promote and validated against sample schools.

## Exit Criteria

- One academy with known AAR data can be traced Bronze -> Silver -> Gold -> profile/trends payload.
- Finance metrics benchmark successfully in the existing benchmark cache path.
- Docs remain explicit that maintained-school finance parity is not part of this phase.
