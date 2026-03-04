# Phase 2C Design - ONS IMD Bronze To Gold Pipeline

## Document Control

- Status: Implemented
- Last updated: 2026-03-02
- Depends on:
  - `.planning/phases/phase-2/2A-source-contract-gate.md`
  - `.planning/phases/phase-0/0A-data-platform-baseline.md`
  - `.planning/phases/phase-0/0E-configuration-foundation.md`
  - `.planning/data-architecture.md`
  - `docs/architecture/backend-conventions.md`

## Objective

Ingest ONS Indices of Deprivation data into Gold `area_deprivation`, providing verified IMD and IDACI fields for school area-context enrichment.

## Scope

### In scope

- Download IMD release data from verified GOV.UK assets.
- Bronze archive with source metadata.
- Staging normalization and validation of deprivation fields.
- Gold upsert to `area_deprivation` keyed by LSOA code.
- Explicit handling of release fallback (IoD2025 primary, IoD2019 fallback).

### Out of scope

- Crime-area aggregation (owned by `2D`).
- API contract and web rendering behavior (owned by `2E`/`2F`).

## Source Contract

### Primary endpoint family (required)

- Release page:
  - `GET https://www.gov.uk/government/statistics/english-indices-of-deprivation-2025`
- Primary file:
  - `GET https://assets.publishing.service.gov.uk/media/691ded56d140bbbaa59a2a7d/File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv`

### Fallback endpoint family

- Release page:
  - `GET https://www.gov.uk/government/statistics/english-indices-of-deprivation-2019`
- Fallback file:
  - `GET https://assets.publishing.service.gov.uk/media/5dc407b440f0b6379a7acc8d/File_7_-_All_IoD2019_Scores__Ranks__Deciles_and_Population_Denominators_3.csv`

### Supporting postcode geography contract

- `GET https://api.postcodes.io/postcodes/{postcode}` with required field:
  - `result.codes.lsoa`

### Verified source snapshot (2026-03-02)

- IoD2025 release page: `200`
- IoD2025 File 7 CSV: `200`
- IoD2019 fallback File 7 CSV: `200`
- IoD2025 File 7 verified required fields:
  - `LSOA code (2021)`
  - `LSOA name (2021)`
  - `Index of Multiple Deprivation (IMD) Decile (where 1 is most deprived 10% of LSOAs)`
  - `Income Deprivation Affecting Children Index (IDACI) Score (rate)`
  - `Income Deprivation Affecting Children Index (IDACI) Decile (where 1 is most deprived 10% of LSOAs)`
- IoD2025 File 7 observed rows:
  - `33755`

### Fallback path

- `CIVITAS_IMD_SOURCE_CSV` override for explicit file/URL.
- `CIVITAS_IMD_RELEASE` selector (`iod2025` default, `iod2019` fallback).

## Decisions

1. Use File 7 as the single canonical ingest asset for both IMD and IDACI context.
2. Canonical join key is LSOA code, not LSOA label.
3. Child-poverty context is represented explicitly via IDACI fields:
   - `idaci_score`,
   - `idaci_decile`.
4. Preserve source release metadata (`source_release`, `lsoa_vintage`) in Gold.
5. If school -> LSOA code mapping is unavailable, API returns `null` deprivation context with explicit coverage metadata.

## Implementation Progress (2026-03-02)

- Completed: added `OnsImdPipeline` with Bronze download, staging validation/rejection logging, and Gold promote upsert:
  - `apps/backend/src/civitas/infrastructure/pipelines/ons_imd.py`
- Completed: added pipeline source registration and settings wiring for:
  - `PipelineSource.ONS_IMD`
  - `CIVITAS_IMD_SOURCE_CSV`
  - `CIVITAS_IMD_RELEASE`
- Completed: added Gold migration:
  - `apps/backend/alembic/versions/20260302_07_phase2_area_deprivation.py`
- Completed: added fixtures and tests:
  - `apps/backend/tests/fixtures/ons_imd/*`
  - `apps/backend/tests/unit/test_ons_imd_transforms.py`
  - `apps/backend/tests/integration/test_ons_imd_pipeline.py`
- Completed: updated local configuration/runbook coverage:
  - `.env.example`
  - `docs/runbooks/local-development.md`
  - `apps/backend/tests/unit/test_settings.py`
  - `apps/backend/tests/unit/test_pipeline_cli.py`
- Verification commands executed:
  - `uv run --project apps/backend ruff check apps/backend`
  - `uv run --project apps/backend pytest apps/backend/tests/unit/test_ons_imd_transforms.py apps/backend/tests/integration/test_ons_imd_pipeline.py apps/backend/tests/unit/test_settings.py apps/backend/tests/unit/test_pipeline_cli.py -q`
  - `make lint`
  - `make test`

## Data Flow

### Bronze

- Path format:
  - `data/bronze/ons_imd/{yyyy-mm-dd}/file_7.csv`
- Metadata sidecar:
  - `file_7.metadata.json`
  - includes source URL, release tag, checksum, row count.

### Staging

- Per-run staging table:
  - `staging.ons_imd__{run_id}`
- Normalization responsibilities:
  - field rename to canonical snake_case,
  - numeric/decile type casting,
  - LSOA-code validation,
  - reject logging for rows missing required deprivation fields.

### Gold

Target table: `area_deprivation`

Minimum columns:

- `lsoa_code` (PK)
- `lsoa_name`
- `local_authority_district_code`
- `local_authority_district_name`
- `imd_score`
- `imd_rank`
- `imd_decile`
- `idaci_score`
- `idaci_rank`
- `idaci_decile`
- `source_release`
- `lsoa_vintage`
- `source_file_url`
- `updated_at`

Upsert behavior:

- `INSERT ... ON CONFLICT (lsoa_code) DO UPDATE`
- deterministic rerun semantics.

Indexes:

- PK on `lsoa_code`
- B-tree on `imd_decile`
- B-tree on `idaci_decile`

## File-Oriented Implementation Plan

1. `apps/backend/src/civitas/infrastructure/config/settings.py`
   - add IMD source/release override settings.
2. `apps/backend/src/civitas/infrastructure/pipelines/ons_imd.py` (new)
   - implement download, stage, promote pipeline.
3. `apps/backend/src/civitas/infrastructure/pipelines/__init__.py`
   - register `ons_imd` pipeline source.
4. `apps/backend/alembic/versions/*_phase2_area_deprivation.py` (new)
   - create `area_deprivation` Gold table + indexes.
5. `apps/backend/tests/fixtures/ons_imd/` (new)
   - add valid and mixed-validity fixture CSV.
6. `apps/backend/tests/unit/test_ons_imd_transforms.py` (new)
   - field mapping and type-cast behavior coverage.
7. `apps/backend/tests/integration/test_ons_imd_pipeline.py` (new)
   - stage/promote idempotency and schema assertions.

## Testing And Quality Gates

### Required tests

- Required columns are validated and missing schema fails fast.
- IMD/IDACI values cast deterministically.
- Invalid/missing LSOA code rows are rejected and logged.
- Gold upsert remains idempotent on unchanged input.

### Required gates

- `uv run --project apps/backend pytest apps/backend/tests/unit/test_ons_imd_transforms.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/integration/test_ons_imd_pipeline.py -q`
- `make lint`
- `make test`

## Acceptance Criteria

1. `civitas pipeline run --source ons_imd` completes Bronze -> Staging -> Gold.
2. `area_deprivation` contains validated IMD and IDACI context by LSOA code.
3. Release fallback behavior is explicit and deterministic.
4. Reruns are idempotent with preserved rejection logging.

## Risks And Mitigations

- Risk: release assets change column names or formats.
  - Mitigation: strict source gate checks and transform tests.
- Risk: area joins degrade due missing school LSOA codes.
  - Mitigation: postcode geography contract verification and API coverage flags.
- Risk: "child poverty context" interpreted as a distinct index not present in source.
  - Mitigation: explicit product mapping to IDACI fields.
