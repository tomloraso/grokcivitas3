# Phase 18 / 18D Design - Quality Gates

## Document Control

- Status: Planned
- Last updated: 2026-03-09

## Required Commands

- `uv run --project apps/backend pytest apps/backend/tests/unit/test_leaver_destinations_contract.py apps/backend/tests/integration/test_leaver_destinations_pipeline.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/integration/test_school_profile_repository.py apps/backend/tests/integration/test_school_profile_api.py apps/backend/tests/integration/test_school_trends_repository.py apps/backend/tests/integration/test_school_trends_api.py -q`
- `make lint`
- `make test`

## Data Quality Gates

1. Bronze manifests record the data-catalogue CSV route used.
2. Destination percentages remain in their published percentage scale.
3. Stage-specific null handling is regression-tested.
4. The pipeline fails explicitly if the data-catalogue schema changes.

## Exit Criteria

- One KS4 school and one 16-18 institution can be traced Bronze -> Silver -> Gold.
- API payloads expose stage-aware destination metrics.
- Scope caveat for 16-18 remains explicit in planning and completeness docs.
