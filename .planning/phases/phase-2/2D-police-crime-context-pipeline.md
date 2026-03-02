# Phase 2D Design - Police UK Crime Context Bronze To Gold Pipeline

## Document Control

- Status: Draft
- Last updated: 2026-03-02
- Depends on:
  - `.planning/phases/phase-2/2A-source-contract-gate.md`
  - `.planning/phases/phase-0/0A-data-platform-baseline.md`
  - `.planning/phases/phase-0/0E-configuration-foundation.md`
  - `.planning/data-architecture.md`
  - `docs/architecture/backend-conventions.md`

## Objective

Implement monthly police crime context ingest and spatial aggregation into Gold `area_crime_context` for school-local area summaries.

## Scope

### In scope

- Archive-month discovery and download for Police UK data.
- Bronze storage of monthly archive assets.
- Staging load for crime street-level records needed by aggregation.
- Gold spatial aggregation by school, month, and crime category.
- Deterministic rerun behavior.

### Out of scope

- Outcome-history ingestion and stop/search ingestion (not required for Phase 2 profile context).
- API/web rendering behavior (owned by `2E`/`2F`).

## Source Contract

### Primary endpoint family (archive-first)

- Archive index:
  - `GET https://data.police.uk/data/archive/`
- Monthly archive pattern:
  - `GET https://data.police.uk/data/archive/{yyyy-mm}.zip`
- CSV schema reference:
  - `GET https://data.police.uk/about/#columns`

### Supporting API endpoint family

- Freshness:
  - `GET https://data.police.uk/api/crime-last-updated`
- Available months:
  - `GET https://data.police.uk/api/crimes-street-dates`
- Category list:
  - `GET https://data.police.uk/api/crime-categories?date={yyyy-mm}`
- Targeted sample/fallback:
  - `GET https://data.police.uk/api/crimes-street/all-crime?lat={lat}&lng={lng}&date={yyyy-mm}`

### Verified source snapshot (2026-03-02)

- Archive index callable (`200`) and lists links through `/data/archive/2026-01.zip`.
- `2026-01.zip` callable (`302` -> `200`) with:
  - `Content-Type: application/zip`
  - `Content-Length: 1746908436`
- About-page columns document includes:
  - `Longitude`, `Latitude`,
  - `LSOA code`, `LSOA name`,
  - `Crime type`,
  - `Last outcome category`.
- API endpoints callable (`200`) and return expected payload structures.
- API limit contract documented:
  - `15 requests per second with a burst of 30`,
  - `429` on exceed.

### Fallback path

- `CIVITAS_POLICE_CRIME_SOURCE_ARCHIVE_URL` override for explicit monthly archive URL.
- `CIVITAS_POLICE_CRIME_SOURCE_MODE` selector:
  - `archive` (default),
  - `api` (controlled fallback for targeted month/area recovery only).

## Decisions

1. Primary ingest path is monthly archive ZIP for reproducible Bronze artifacts.
2. Only crime street records are ingested for Phase 2 context (no stop/search, no outcomes-history tables).
3. Canonical required fields for aggregation:
   - `Month`
   - `Longitude`
   - `Latitude`
   - `Crime type`
4. Rows missing `Month`, `Longitude`, or `Latitude` are rejected.
5. Aggregation radius default is `1 mile` (`1609.344` meters), configurable through settings.
6. Gold stores category-level counts to support API summary rollups without reprocessing raw points.

## Data Flow

### Bronze

- Path format:
  - `data/bronze/police_crime/{yyyy-mm}/archive.zip`
- Metadata sidecar:
  - `archive.metadata.json`
  - includes source URL, checksum, extracted file count, and targeted month.

### Staging

- Per-run staging tables:
  - `staging.police_crime_raw__{run_id}`
  - `staging.police_crime_points__{run_id}`
- Stage responsibilities:
  - extract ZIP,
  - ingest street-crime CSV rows,
  - map required columns to canonical names,
  - convert month string to date month-start,
  - construct PostGIS point from `Longitude`/`Latitude`,
  - reject invalid coordinates/required-field gaps.

### Gold

Target table: `area_crime_context`

Minimum columns:

- `urn`
- `month`
- `crime_category`
- `incident_count`
- `radius_meters`
- `source_month`
- `updated_at`

Primary key:

- `(urn, month, crime_category, radius_meters)`

Aggregation rule:

- spatial join where `ST_DWithin(schools.location, crime_point::geography, radius_meters)`.
- `incident_count = count(*)` per `(urn, month, category, radius)`.

Indexes:

- PK composite index
- B-tree on `(urn, month)`
- B-tree on `(month, crime_category)`

## File-Oriented Implementation Plan

1. `apps/backend/src/civitas/infrastructure/config/settings.py`
   - add police-crime source/radius configuration settings.
2. `apps/backend/src/civitas/infrastructure/pipelines/police_crime_context.py` (new)
   - implement download, stage, promote pipeline.
3. `apps/backend/src/civitas/infrastructure/pipelines/__init__.py`
   - register `police_crime_context` pipeline source.
4. `apps/backend/alembic/versions/*_phase2_area_crime_context.py` (new)
   - create Gold table + indexes.
5. `apps/backend/tests/fixtures/police_crime_context/` (new)
   - add fixture ZIP/CSV samples with valid and invalid rows.
6. `apps/backend/tests/unit/test_police_crime_context_transforms.py` (new)
   - parsing and coordinate-validation coverage.
7. `apps/backend/tests/integration/test_police_crime_context_pipeline.py` (new)
   - stage/promote aggregation and idempotency coverage.

## Testing And Quality Gates

### Required tests

- archive URL and month resolution behavior is deterministic.
- required-field and coordinate validation rejects bad rows.
- spatial aggregation results are deterministic for fixture geometries.
- reruns on unchanged input are idempotent.

### Required gates

- `uv run --project apps/backend pytest apps/backend/tests/unit/test_police_crime_context_transforms.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/integration/test_police_crime_context_pipeline.py -q`
- `make lint`
- `make test`

## Acceptance Criteria

1. `civitas pipeline run --source police_crime_context` completes Bronze -> Staging -> Gold.
2. `area_crime_context` contains month/category counts per school for configured radius.
3. Pipeline handles large monthly archives predictably and reruns idempotently.
4. API-fallback mode is explicit and rate-limit aware.

## Risks And Mitigations

- Risk: monthly archive sizes increase processing cost.
  - Mitigation: archive-month bounded processing and staged extraction strategy.
- Risk: API fallback exceeds rate limits.
  - Mitigation: archive-first design, rate-limit aware fallback with bounded use.
- Risk: anonymized police coordinates introduce spatial uncertainty.
  - Mitigation: present results as context aggregates, not exact local incident counts.
