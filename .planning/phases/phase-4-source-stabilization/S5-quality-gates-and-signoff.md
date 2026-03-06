# Phase 4 / S5 Design - Quality Gates And Sign-Off

## Document Control

- Status: Complete
- Last updated: 2026-03-04
- Depends on:
 - `.planning/phases/phase-4-source-stabilization/S1-source-contract-and-catalog-freeze.md`
 - `.planning/phases/phase-4-source-stabilization/S2-release-file-discovery-and-bronze-ingest.md`
 - `.planning/phases/phase-4-source-stabilization/S3-multi-source-normalization-and-gold-upsert.md`
 - `.planning/phases/phase-4-source-stabilization/S4-completeness-contract-and-parent-facing-copy.md`
  - `.agents/tooling.md`
  - `.agents/testing.md`

## Objective

Define mandatory gates so this blocking phase only closes when source reliability, trend depth, and completeness transparency are all proven.

## Gate 0 - Source contract gate

Required commands:

- `uv run --project apps/backend python tools/scripts/verify_phase_s_sources.py`
- `uv run --project apps/backend pytest apps/backend/tests/unit/test_verify_phase_s_sources.py -q`

## Gate 1 - Discovery and Bronze ingest

Required commands:

- `uv run --project apps/backend pytest apps/backend/tests/unit/test_demographics_release_discovery.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/integration/test_demographics_release_files_download.py -q`

## Gate 2 - Normalization and Gold promote

Required commands:

- `uv run --project apps/backend pytest apps/backend/tests/unit/test_demographics_spc_contract.py apps/backend/tests/unit/test_demographics_sen_contract.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/integration/test_demographics_release_files_pipeline.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/integration/test_school_trends_repository.py -q`

## Gate 3 - API and UI completeness contract

Required commands:

1. `uv run --project apps/backend python tools/scripts/export_openapi.py`
2. `cd apps/web && npm run generate:types`
3. `uv run --project apps/backend pytest apps/backend/tests/integration/test_school_profile_api.py apps/backend/tests/integration/test_school_trends_api.py -q`
4. `cd apps/web && npm run test -- school-profile`
5. `cd apps/web && npm run lint`
6. `cd apps/web && npm run typecheck`

## Gate 4 - Coverage and trend-depth checks

Required commands:

- `uv run --project apps/backend python tools/scripts/check_demographics_trend_coverage.py --strict`

Required thresholds (open schools):

1. Primary `>=2` years: `>=90%`
2. Secondary `>=2` years: `>=90%`
3. Primary `>=3` years: `>=85%`
4. Secondary `>=3` years: `>=85%`

## Gate 5 - Repository golden path

Required commands:

- `make lint`
- `make test`

## Gate 6 - Legacy path removal check

Required checks:

1. No active pipeline configuration points demographics ingestion back to the old single-dataset history path.
2. No TODO-marked compatibility shim remains in demographics pipeline modules.
3. Phase sign-off lists removed legacy codepaths explicitly.

## Sign-off artifact

Create:

 - `.planning/phases/phase-4-source-stabilization/signoff-YYYY-MM-DD.md`

Artifact must include:

1. command evidence for all gates,
2. coverage/depth metrics by phase,
3. unresolved risks and approved follow-ups.

## Exit criteria

1. All gates pass in one repository state.
2. Trend-history behavior is explained by source coverage, not hidden ingestion limitations.
3. `Phase 4` is marked complete in `.planning/phased-delivery.md`.

## Implementation tracking (2026-03-04)

- [x] Added trend coverage gate script: `tools/scripts/check_demographics_trend_coverage.py`.
- [x] Updated local runbooks and `.env.example` for release-files demographics source controls.
- [x] Executed Gate 0 through Gate 6 command set and recorded evidence in:
 - `.planning/phases/phase-4-source-stabilization/signoff-2026-03-04.md`
- [x] Marked `Phase 4` complete in `.planning/phased-delivery.md`.
