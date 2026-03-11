# Phase 18 / 18D Design - Quality Gates

## Document Control

- Status: Implemented (2026-03-11)
- Last updated: 2026-03-11

## Required Commands

- `uv run --project apps/backend pytest apps/backend/tests/unit/test_leaver_destinations_contract.py apps/backend/tests/integration/test_leaver_destinations_pipeline.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/integration/test_school_profile_repository.py apps/backend/tests/integration/test_school_profile_api.py apps/backend/tests/integration/test_school_trends_repository.py apps/backend/tests/integration/test_school_trends_api.py -q`
- `make lint`
- `make test`

## Data Quality Gates

1. Bronze manifests record the public data-catalogue CSV route used.
2. Bronze manifests also record the observed middleware rewrite target for diagnostics.
3. Contract tests lock the proved live headers for both datasets.
4. The pipeline fails explicitly if the data-catalogue schema changes.
5. Count and percentage rows are pivoted separately and regression-tested.
6. Published `overall` values are consumed as source-of-truth fields and are not replaced by arithmetic re-derivations.
7. Suppression tokens and other raw null-like markers are handled explicitly in normalization tests.
8. Destination year (`2022/23`) is derived from the asset content, not inferred from the release slug (`2023-24`).

## Exit Criteria

- One KS4 school and one 16-18 institution can be traced Bronze -> Silver -> Gold.
- API payloads expose stage-aware destination metrics from published total rows.
- Scope caveat for 16-18 remains explicit in planning and completeness docs.
- Completeness distinguishes `unsupported_stage` from source absence.
