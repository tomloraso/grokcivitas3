# Phase 1C Design - Ofsted Latest Bronze To Gold Pipeline

## Document Control

- Status: Implemented
- Last updated: 2026-03-02
- Depends on:
  - `.planning/phases/phase-1/1A-source-contract-gate.md`
  - `.planning/phases/phase-0/0A-data-platform-baseline.md`
  - `.planning/phases/phase-0/0E-configuration-foundation.md`
  - `.planning/data-architecture.md`
  - `docs/architecture/backend-conventions.md`

## Objective

Ingest the latest Ofsted inspection headline per school from a verified callable monthly source and upsert one latest snapshot row per URN into Gold.

## Scope

### In scope

- Resolve latest CSV asset URL from Ofsted landing page.
- Bronze archive of the resolved latest CSV with metadata.
- Staging normalization and validation.
- Gold upsert to `school_ofsted_latest` with one row per school URN.

### Out of scope

- Full Ofsted timeline ingest (Phase 2).
- School profile API wiring (`1D`).

## Source Contract

### Primary endpoint family

- Landing page:
  - `GET https://www.gov.uk/government/statistical-data-sets/monthly-management-information-ofsteds-school-inspections-outcomes`
- Latest CSV link extraction:
  - first valid link matching:
    - `assets.publishing.service.gov.uk/...latest_inspections...csv`

### Verified source snapshot (2026-03-02)

- Landing page returned `200`.
- Latest asset resolved to:
  - `https://assets.publishing.service.gov.uk/media/698b20be95285e721cd7127d/Management_information_-_state-funded_schools_-_latest_inspections_as_at_31_Jan_2026.csv`
- Asset returned `200`.
- Verified headers include:
  - `URN`
  - `Inspection start date`
  - `Publication date`
  - `Latest OEIF overall effectiveness`
  - `Ungraded inspection overall outcome`

### Fallback path

- `CIVITAS_OFSTED_LATEST_SOURCE_CSV` override for explicit asset URL or local file path.

## Decisions

1. Resolve latest CSV from landing page on each download run unless override is set, selecting the newest dated `latest_inspections` asset when multiple candidates are present.
2. Gold table keeps one latest row per current `urn`.
3. Use `Latest OEIF overall effectiveness` as primary headline when available.
4. Map numeric overall effectiveness codes to labels:
   - `1` -> `Outstanding`
   - `2` -> `Good`
   - `3` -> `Requires improvement`
   - `4` -> `Inadequate`
   - `Not judged` -> `Not judged`
5. If graded field is null, keep `ungraded inspection overall outcome` as secondary headline text.
6. Do not infer a graded label from ungraded outcome text.

## Implementation Progress (2026-03-02)

- Completed: added `OfstedLatestPipeline` at `apps/backend/src/civitas/infrastructure/pipelines/ofsted_latest.py` with:
  - landing page latest-asset URL resolution,
  - Bronze download + metadata sidecar,
  - staging normalization/validation/rejection logging,
  - Gold promote upsert behavior.
- Completed: added pipeline source registration and settings wiring for:
  - `PipelineSource.OFSTED_LATEST`,
  - `CIVITAS_OFSTED_LATEST_SOURCE_CSV`.
- Completed: added Gold migration `20260302_05_phase1_school_ofsted_latest.py`.
- Completed: added fixtures and tests:
  - `apps/backend/tests/fixtures/ofsted_latest/*`
  - `apps/backend/tests/unit/test_ofsted_latest_transforms.py`
  - `apps/backend/tests/integration/test_ofsted_latest_pipeline.py`
- Completed: updated CLI/settings coverage and local runbook wiring for the new source:
  - `apps/backend/tests/unit/test_pipeline_cli.py`
  - `apps/backend/tests/unit/test_settings.py`
  - `.env.example`
  - `docs/runbooks/local-development.md`

## Data Flow

### Bronze

- Path format:
  - `data/bronze/ofsted_latest/{yyyy-mm-dd}/latest_inspections.csv`
- Metadata sidecar:
  - `latest_inspections.metadata.json`
  - includes landing page URL, resolved asset URL, checksum, row count.

### Staging

- Per-run staging table:
  - `staging.ofsted_latest__{run_id}`
- Normalize and validate:
  - trim text,
  - parse date fields,
  - reject rows without `URN`.
- Log rejects to `pipeline_rejections`.

### Gold

Target table: `school_ofsted_latest`

Minimum columns:

- `urn` (PK/FK to `schools.urn`)
- `inspection_start_date`
- `publication_date`
- `overall_effectiveness_code`
- `overall_effectiveness_label`
- `is_graded`
- `ungraded_outcome`
- `source_asset_url`
- `source_asset_month`
- `updated_at`

Upsert behavior:

- `INSERT ... ON CONFLICT (urn) DO UPDATE`
- always update `updated_at` and source metadata fields.

Indexes:

- PK on `urn`
- B-tree on `overall_effectiveness_code`
- B-tree on `inspection_start_date`

## File-Oriented Implementation Plan

1. `apps/backend/src/civitas/infrastructure/config/settings.py`
   - add Ofsted latest source override setting.
2. `apps/backend/src/civitas/infrastructure/pipelines/ofsted_latest.py` (new)
   - implement download/stage/promote pipeline.
3. `apps/backend/src/civitas/infrastructure/pipelines/__init__.py`
   - register Ofsted latest pipeline source.
4. `apps/backend/alembic/versions/*_phase1_school_ofsted_latest.py`
   - create Gold table and indexes.
5. `apps/backend/tests/fixtures/ofsted_latest/`
   - add fixture(s) with graded and ungraded examples.
6. `apps/backend/tests/unit/test_ofsted_latest_transforms.py` (new)
   - code-to-label mapping and date parsing coverage.
7. `apps/backend/tests/integration/test_ofsted_latest_pipeline.py` (new)
   - stage/promote and one-row-per-URN behavior coverage.
8. `.env.example`
   - add optional Ofsted source override setting.

## Testing And Quality Gates

### Required tests

- Latest link extraction picks expected asset URL format.
- Missing URN rows are rejected and logged.
- Graded mapping is deterministic.
- Upsert behavior remains idempotent for unchanged source.

### Required gates

- `uv run --project apps/backend pytest apps/backend/tests/unit/test_ofsted_latest_transforms.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/integration/test_ofsted_latest_pipeline.py -q`
- `make lint`
- `make test`

## Acceptance Criteria

1. `civitas pipeline run --source ofsted_latest` completes Bronze -> Silver -> Gold.
2. `school_ofsted_latest` contains at most one current row per `urn`.
3. Ofsted headline rating/date fields are populated from verified source columns.
4. Pipeline reruns are idempotent and observable via run metadata/rejections.

## Risks And Mitigations

- Risk: Ofsted landing page structure changes and link extraction breaks.
  - Mitigation: extraction tests + environment override fallback.
- Risk: grading schema changes in source values.
  - Mitigation: strict mapping with explicit unknown-value handling and failure logging.
