# Phase 0B Design - GIAS Bronze To Gold Pipeline

## Document Control

- Status: Draft
- Last updated: 2026-02-27
- Depends on:
  - `.planning/phases/phase-0/0A-data-platform-baseline.md`
  - `.planning/data-architecture.md`
  - `.planning/project-brief.md`
  - `.planning/deployment-strategy.md`

## Objective

Implement the first real production-style data pipeline using GIAS as the canonical school source and load queryable school location records into Gold.

## Scope

### In scope

- Bronze download/archive for GIAS files.
- Staging load, type normalization, validation, and rejection logging.
- Gold `schools` upsert with PostGIS geography.
- Idempotent re-run behavior for repeated source loads.

### Out of scope

- API endpoint exposure (0C).
- Frontend search/map rendering (0D).
- DfE/Ofsted/area context metrics (Phase 1+).

## Decisions

1. **Primary school key**: use `urn` as Gold `schools` primary key.
2. **Search dataset policy**: include only open schools in search responses; keep status fields in Gold for future filtering.
3. **Geometry source**: derive geometry from GIAS easting/northing when available and valid.
4. **Bronze immutability**: every downloaded file is written to a date-stamped folder and never mutated.
5. **Coordinate transform**: convert GIAS easting/northing from EPSG:27700 (BNG) to EPSG:4326 for `location` geography.

## Source Contract

- Source: GIAS bulk download (`edubasealldata` payload).
- Download flow endpoints:
  - `GET https://get-information-schools.service.gov.uk/Downloads`
  - `POST https://get-information-schools.service.gov.uk/Downloads/Collate`
  - `GET https://get-information-schools.service.gov.uk/Downloads/GenerateAjax/{id}`
  - `GET https://ea-edubase-api-prod.azurewebsites.net/edubase/downloads/File.xhtml?id={id}` (zip payload)
- Expected CSV file name pattern: `edubasealldataYYYYMMDD.csv`
- Required CSV headers (locked to exact names):
  - URN
  - EstablishmentName
  - TypeOfEstablishment (name)
  - PhaseOfEducation (name)
  - EstablishmentStatus (name)
  - Postcode
  - Easting
  - Northing
  - OpenDate
  - CloseDate
  - NumberOfPupils
  - SchoolCapacity

### Source-To-Gold Mapping (Phase 0)

- `URN` -> `schools.urn`
- `EstablishmentName` -> `schools.name`
- `TypeOfEstablishment (name)` -> `schools.type`
- `PhaseOfEducation (name)` -> `schools.phase`
- `EstablishmentStatus (name)` -> `schools.status`
- `Postcode` -> `schools.postcode`
- `Easting` -> `schools.easting`
- `Northing` -> `schools.northing`
- `OpenDate` -> `schools.open_date`
- `CloseDate` -> `schools.close_date`
- `NumberOfPupils` -> `schools.pupil_count`
- `SchoolCapacity` -> `schools.capacity`

If source fields change, pipeline fails fast with explicit schema mismatch logging.

### Verification Snapshot

- Verified against live extract generated on 2026-02-27:
  - zip file: `extract.zip`
  - csv inside zip: `edubasealldata20260227.csv`

## Data Flow

### Bronze

- Path format: `data/bronze/gias/{yyyy-mm-dd}/edubasealldata.csv`
- Store source checksum and download timestamp in run metadata.

### Staging

- Create per-run staging table in `staging` schema (for example: `staging.gias_schools__{run_id}`).
- Load via `COPY`.
- Normalize:
  - trim text fields
  - normalize postcode case/spacing
  - cast numeric/date fields
  - convert known source sentinel placeholders to `NULL`
- Validate:
  - reject rows without URN
  - reject rows without usable coordinates
  - reject rows with out-of-range BNG coordinates
  - reject rows with invalid type conversions
- Persist rejected rows to `pipeline_rejections` with reason code.

### Gold

- Target table: `schools`
- Minimum columns:
  - `urn` (PK)
  - `name`
  - `phase`
  - `type`
  - `status`
  - `postcode`
  - `easting`
  - `northing`
  - `location` (`geography(Point,4326)`)
  - `capacity`
  - `pupil_count`
  - `open_date`
  - `close_date`
  - `updated_at`
- Upsert behavior:
  - `INSERT ... ON CONFLICT (urn) DO UPDATE`
  - update changed fields and `updated_at`
  - keep operation idempotent for same input data
- Geometry build:
  - create geometry from BNG columns:
    - `ST_SetSRID(ST_MakePoint(easting, northing), 27700)`
  - transform to WGS84:
    - `ST_Transform(<bng_geometry>, 4326)::geography(Point,4326)`
- Indexes:
  - PK on `urn`
  - GIST on `location`
  - optional B-tree on `status` for open-school filters

## File-Oriented Implementation Plan

1. `apps/backend/src/civitas/infrastructure/pipelines/gias.py`
   - implement download, stage, promote pipeline methods.
2. `apps/backend/src/civitas/infrastructure/pipelines/__init__.py`
   - register GIAS pipeline entry in source registry.
3. `apps/backend/alembic/versions/*_phase0_gias_schools.py`
   - create Gold `schools` table + indexes.
4. `apps/backend/src/civitas/infrastructure/persistence/` (new postgres module files as needed)
   - shared SQL execution helpers for pipeline promote/upsert.
5. `apps/backend/tests/fixtures/gias/`
   - sample GIAS CSV fixtures for valid + invalid rows.
6. `apps/backend/tests/integration/test_gias_pipeline.py`
   - end-to-end pipeline test against test DB.
7. `apps/backend/tests/unit/test_gias_transforms.py`
   - normalization and validation rule tests.

## Observability

For each run record:

- total rows downloaded
- staged rows
- promoted rows
- rejected rows
- duration per stage
- failure reason (if failed)

This data must persist in `pipeline_runs` even when run fails.

## Testing And Quality Gates

### Required tests

- Golden fixture load produces expected `schools` records.
- Duplicate runs with unchanged fixture are idempotent.
- Invalid rows are rejected and logged, not silently dropped.
- Geometry query smoke test confirms loaded points are spatially valid.
- Coordinate transform test confirms known BNG sample maps to expected UK lat/lng range.

### Required gates

- `make lint`
- `make test`

## Acceptance Criteria

1. `civitas pipeline run --source gias` ingests GIAS from Bronze to Gold successfully.
2. Gold `schools` table contains queryable PostGIS points for valid rows.
3. Re-running the same input does not duplicate schools.
4. Validation rejects malformed rows and records rejection reasons.

## Risks And Mitigations

- **Risk**: source format drift from GIAS updates.
  - **Mitigation**: explicit schema contract checks and fail-fast logging.
- **Risk**: poor coordinate quality in source rows.
  - **Mitigation**: strict coordinate validation and rejection reporting.
