# Phase S2 Design - Release File Discovery And Bronze Ingest

## Document Control

- Status: Complete
- Last updated: 2026-03-04
- Depends on:
  - `.planning/phases/phase-source-stabilization/S1-source-contract-and-catalog-freeze.md`
  - `docs/architecture/backend-conventions.md`
  - `.agents/pipelines.md`

## Objective

Implement deterministic release discovery and Bronze ingestion for multi-year school-level files from approved source families.

## In scope

- Discover release metadata from supported release pages.
- Resolve release version id and school-level file ids for configured lookback.
- Download files into Bronze with immutable manifests and checksums.
- Keep Bronze idempotent and rerunnable.

## Out of scope

- Row normalization and Gold upsert (handled in `S3`).

## Discovery contract

1. Release discovery source: release page JSON (`__NEXT_DATA__`) for each configured publication/release slug.
2. Content download endpoint:
   - `https://content.explore-education-statistics.service.gov.uk/api/releases/{releaseVersionId}/files/{fileId}`
3. File selection rule:
   - `name` contains `School level underlying data`,
   - exclude class-size variants,
   - take deterministic first match after stable sort by file id.

## Explicit source inputs

1. Publication slugs:
   - `school-pupils-and-their-characteristics`
   - `special-educational-needs-in-england`
2. Release slugs:
   - non-legacy release pages from `2019-20` through current configured lookback.
3. Content endpoint:
   - `https://content.explore-education-statistics.service.gov.uk/api/releases/{releaseVersionId}/files/{fileId}`

## No-shim rule for discovery

1. Do not implement fallback to previous DfE v1 dataset IDs for demographics history recovery.
2. If release discovery fails, fail fast and surface error; do not silently route to legacy ingest.

## Bronze manifest requirements

For each downloaded asset, record:

- publication slug
- release slug
- release version id
- file id
- file name
- downloaded timestamp (UTC)
- sha256
- row count

## File-oriented implementation plan

1. `apps/backend/src/civitas/infrastructure/pipelines/demographics_release_files.py` (new)
   - discovery + Bronze download stage.
2. `apps/backend/src/civitas/infrastructure/config/settings.py`
   - settings for lookback years, strict mode, and publication slugs.
3. `apps/backend/src/civitas/infrastructure/pipelines/base.py`
   - add pipeline source enum(s) if separate source IDs are used.
4. `apps/backend/src/civitas/infrastructure/pipelines/__init__.py`
   - wire new pipeline source(s).
5. `apps/backend/tests/integration/test_demographics_release_files_download.py` (new)
   - manifest and idempotency coverage.
6. `apps/backend/tests/unit/test_demographics_release_discovery.py` (new)
   - discovery parser and filtering behavior.

## Codex execution checklist

1. Start with unit tests for release parsing and file selection.
2. Add download stage with manifest write.
3. Add integration tests for rerun/idempotency.
4. Keep all metadata ASCII and stable-sort deterministic.

## Required commands

- `uv run --project apps/backend pytest apps/backend/tests/unit/test_demographics_release_discovery.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/integration/test_demographics_release_files_download.py -q`

## Acceptance criteria

1. Configured lookback releases are discoverable and downloadable from approved publications.
2. Bronze manifests are complete, deterministic, and rerunnable.
3. Failures are explicit when expected assets are missing.

## Implementation tracking (2026-03-04)

- [x] Added `apps/backend/src/civitas/infrastructure/pipelines/demographics_release_files.py` discovery + Bronze manifest download logic.
- [x] Added unit discovery coverage in `apps/backend/tests/unit/test_demographics_release_discovery.py`.
- [x] Added Bronze idempotency integration coverage in `apps/backend/tests/integration/test_demographics_release_files_download.py`.
- [x] Wired pipeline registry to use release-files demographics ingestion for `dfe_characteristics`.
