# Phase 2A Design - Source Contract Gate (Non-Negotiable)

## Document Control

- Status: Implemented
- Last updated: 2026-03-02
- Depends on:
  - `.planning/phases/phase-2/README.md`
  - `.planning/project-brief.md`
  - `.planning/data-architecture.md`
  - `docs/architecture.md`

## Objective

Enforce a hard pre-implementation gate so every Phase 2 source-dependent deliverable is grounded in real, callable endpoints with verified field coverage.

No implementation work for `2B`, `2C`, `2D`, or `2E` may start until this gate passes.

## Scope

### In scope

- Define mandatory source verification checks for Phase 2 sources.
- Lock endpoint contracts (method, URL pattern, required fields, fallback).
- Record dated verification evidence from live responses.
- Define coverage policy where required product fields do not exist as exact source fields.

### Out of scope

- Pipeline transformation implementation details (owned by `2B`, `2C`, `2D`).
- API and web implementation details (owned by `2E`, `2F`).

## Gate Rules (Blocking)

1. Every source-dependent design doc must include:
   - exact endpoint URL pattern(s),
   - HTTP method,
   - expected success status code,
   - required source fields,
   - verification date and evidence.
2. Every source family must define a fallback path:
   - alternate callable endpoint,
   - or explicit environment override for source URL/file input.
3. Every required Phase 2 metric must map to a verified source field or be explicitly marked as a proxy/unsupported.
4. Missing fields must not be fabricated or inferred from unrelated fields.
5. Join keys must be verified from callable source structures before implementation:
   - school key: `URN`,
   - deprivation key: `LSOA code`,
   - crime geospatial key: `Latitude`/`Longitude`.
6. Timeline and area-context responses must include explicit coverage metadata when history depth or geography linkage is partial.

## Phase 2 Source Contract Matrix

### Ofsted timeline source family

- Landing page:
  - `GET https://www.gov.uk/government/statistical-data-sets/monthly-management-information-ofsteds-school-inspections-outcomes`
- Timeline assets:
  - latest monthly YTD pattern:
    - `https://assets.publishing.service.gov.uk/media/.../Management_information_-_state-funded_schools_-_all_inspections_-_year_to_date_published_by_*.csv`
  - historical baseline asset:
    - `https://assets.publishing.service.gov.uk/media/.../Management_information_-_state-funded_schools_1_September_2015_to_31_August_2019.csv`
- Supporting latest-only asset (already used by Phase 1):
  - `...latest_inspections...csv` (used as fallback for latest headline, not full timeline history).

### ONS IMD source family

- Primary release page:
  - `GET https://www.gov.uk/government/statistics/english-indices-of-deprivation-2025`
- Primary data asset:
  - `GET https://assets.publishing.service.gov.uk/media/691ded56d140bbbaa59a2a7d/File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv`
- Fallback release page:
  - `GET https://www.gov.uk/government/statistics/english-indices-of-deprivation-2019`
- Fallback data asset:
  - `GET https://assets.publishing.service.gov.uk/media/5dc407b440f0b6379a7acc8d/File_7_-_All_IoD2019_Scores__Ranks__Deciles_and_Population_Denominators_3.csv`

### Police UK source family

- Archive index page:
  - `GET https://data.police.uk/data/archive/`
- Monthly archive pattern:
  - `GET https://data.police.uk/data/archive/{yyyy-mm}.zip`
- CSV schema reference page:
  - `GET https://data.police.uk/about/#columns`
- Supporting API endpoints:
  - `GET https://data.police.uk/api/crime-last-updated`
  - `GET https://data.police.uk/api/crimes-street-dates`
  - `GET https://data.police.uk/api/crime-categories?date={yyyy-mm}`
  - `GET https://data.police.uk/api/crimes-street/all-crime?lat={lat}&lng={lng}&date={yyyy-mm}`

### Supporting postcode geography contract

- Postcode lookup with LSOA code:
  - `GET https://api.postcodes.io/postcodes/{postcode}`
- Required fields:
  - `result.codes.lsoa`
  - `result.lsoa`
  - `result.latitude`
  - `result.longitude`

## Verification Snapshot (Executed 2026-03-02)

### Ofsted checks

- Landing page returned `200`.
- Latest `all_inspections` asset returned `200`.
- Latest `latest_inspections` asset returned `200`.
- Historical 2015-2019 asset returned `200`.
- Verified timeline fields across real files:
  - `URN`
  - `Inspection number`
  - `Inspection start date`
  - `Publication date`
  - `Inspection type`
- Verified schema nuance:
  - 2015-2019 file includes a metadata preamble row before the CSV header.

### ONS IMD checks

- IoD2025 landing page returned `200`.
- IoD2025 File 7 CSV returned `200`.
- Verified required fields:
  - `LSOA code (2021)`
  - `Index of Multiple Deprivation (IMD) Decile (where 1 is most deprived 10% of LSOAs)`
  - `Income Deprivation Affecting Children Index (IDACI) Score (rate)`
  - `Income Deprivation Affecting Children Index (IDACI) Decile (where 1 is most deprived 10% of LSOAs)`
- IoD2019 fallback File 7 CSV returned `200` with corresponding legacy-column equivalents.

### Police UK checks

- Archive index page returned `200`.
- Example monthly archive `2026-01.zip` resolved (`302` -> `200`) and returned:
  - `Content-Type: application/zip`
  - `Content-Length: 1746908436`
- CSV schema reference page returned `200` and documents archive URL pattern plus field definitions.
- API endpoints returned `200`:
  - `crime-last-updated` -> `{"date":"2026-01-01"}`
  - `crimes-street-dates` -> includes `2026-01`
  - `crime-categories?date=2026-01` -> category list
  - `crimes-street/all-crime` sample query -> real JSON records including geospatial and category fields.
- API limits page documents:
  - `15 requests per second with a burst of 30`
  - `429` on limit exceed.

### Supporting postcode checks

- `GET https://api.postcodes.io/postcodes/SW1A2AA` returned `200`.
- Verified presence of:
  - `result.codes.lsoa` (code-form join key),
  - `result.lsoa` (label),
  - `result.latitude`,
  - `result.longitude`.

## Implementation Progress (2026-03-02)

- Completed: added executable Phase 2 source gate script:
  - `tools/scripts/verify_phase2_sources.py`
- Completed: implemented contract checks for:
  - Ofsted landing + `all_inspections` + `latest_inspections` + 2015-2019 baseline assets.
  - ONS IoD2025 and IoD2019 landing/file endpoints with required header verification.
  - Police archive index + latest monthly archive resolution + schema reference + API endpoints + limits page checks.
  - Postcodes.io lookup fields required for LSOA joins.
- Completed: added unit coverage for extractor/parser logic and gate pass/fail behavior:
  - `apps/backend/tests/unit/test_verify_phase2_sources.py`
- Completed: optimized police archive verification path to avoid downloading full multi-GB archives by validating status with bounded read.
- Completed: executed gate command against live endpoints:
  - `uv run --project apps/backend python tools/scripts/verify_phase2_sources.py`
  - result: `PASS: Phase 2 source contracts verified`

## Required Metric Coverage Policy

Required Phase 2 profile additions:

- Ofsted timeline events
  - source mapping: Ofsted `all_inspections` assets (`Inspection number`, `Inspection start date`, `Inspection type`, outcome fields).
- Area deprivation
  - source mapping: IMD decile from IoD File 7.
- Child-poverty context
  - source mapping: IDACI score/decile from IoD File 7 (explicit proxy for child-poverty context).
- Area crime summary
  - source mapping: Police archive/API `Crime type`, `Month`, `Latitude`, `Longitude`.

Coverage policy:

1. If required metric maps directly to verified source fields:
   - mark as `supported`.
2. If required metric is served by a verified proxy field:
   - mark as `supported_via_proxy` and document proxy semantics.
3. If required metric is unavailable:
   - mark as `unsupported_in_source`,
   - return `null` plus `coverage` metadata in API responses,
   - record decision in affected deliverable docs.

Known Phase 2 mapping caveat on 2026-03-02:

- "child poverty context" is represented by verified IDACI fields, not a distinct standalone "child poverty index" column.

## Timeline And Area Coverage Policy

1. Ofsted timeline history is considered "full-history ready" only when:
   - historical baseline asset (2015-2019) is included, and
   - all available `all_inspections` assets from 2019 onward are backfilled.
2. If timeline ingest is partial, API must expose explicit timeline coverage metadata.
3. Area deprivation is available only when the school can be mapped to an LSOA code.
4. Area crime context is available only when:
   - school coordinates exist, and
   - crime month aggregate exists for the requested/latest month window.

## File-Oriented Implementation Plan

1. `tools/scripts/verify_phase2_sources.py` (new)
   - run HTTP checks for all Phase 2 source contracts,
   - verify required fields from sampled source payloads/headers,
   - fail non-zero on missing endpoint or required field.
2. `apps/backend/tests/unit/test_verify_phase2_sources.py` (new)
   - parser and gate pass/fail coverage.
3. `.planning/phases/phase-2/source-verification-2026-03-02.md` (new)
   - store endpoint status and field evidence snapshot.
4. `.planning/phases/phase-2/2B-ofsted-timeline-pipeline.md`
   - consume gate and lock timeline source assets and schema-version handling.
5. `.planning/phases/phase-2/2C-ons-imd-pipeline.md`
   - consume gate and lock IMD/IDACI source field mappings.
6. `.planning/phases/phase-2/2D-police-crime-context-pipeline.md`
   - consume gate and lock archive/API contracts and rate-limit constraints.

## Acceptance Criteria

1. Source contract checks are executable and reproducible from repo root.
2. Every Phase 2 source-dependent deliverable references this gate and its pass criteria.
3. Proxy mappings and unsupported fields are explicit and testable.
4. Phase 2 implementation is blocked when source checks fail.

## Risks And Mitigations

- Risk: Ofsted asset patterns drift and break extraction.
  - Mitigation: contract gate plus environment override for explicit asset URLs.
- Risk: IMD release changes structure or column names.
  - Mitigation: strict required-field checks with IoD2019 fallback.
- Risk: Police data volume and API limits cause ingest instability.
  - Mitigation: archive-first ingest design, API used only for freshness checks and controlled fallback.
- Risk: missing LSOA code linkage prevents deprivation joins.
  - Mitigation: supporting postcode contract verification and explicit coverage metadata for unmapped schools.
