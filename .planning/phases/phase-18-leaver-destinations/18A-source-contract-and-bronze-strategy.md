# Phase 18 / 18A Design - Source Contract And Bronze Strategy

## Document Control

- Status: Implemented (2026-03-11)
- Last updated: 2026-03-11
- Depends on:
  - `.planning/project-brief.md`
  - `docs/runbooks/pipelines.md`

## Objective

Freeze the exact live school-level destination source contract, prove the Bronze download path against the current public route, and remove stale assumptions before implementation starts.

## Local Bronze Proof

Proved locally on 2026-03-11 under the canonical Bronze root:

- `data/bronze/leaver_destinations/2026-03-11/ks4/2022-23/`
  - file: `ees_ks4_inst_202223.csv`
  - rows: `43,994`
  - headers: `33`
  - sha256: `e989c757b054224f60509b0f6e53da76274666d878d6083ee9c3a6e51b3c02cb`
- `data/bronze/leaver_destinations/2026-03-11/16_to_18/2022-23/`
  - file: `ees_ks5_inst_202223.csv`
  - rows: `75,658`
  - headers: `34`
  - sha256: `ff9d15bc5fdae0cd80960663e2894ff06dc3f2b51cba21c1d8f2859301969d2e`

Manifest evidence is stored beside each file in `manifest.json`.

## Verified Live Source Pages

KS4 destinations:

- release page:
  - `https://explore-education-statistics.service.gov.uk/find-statistics/key-stage-4-destination-measures/2023-24`
- data-catalogue page:
  - `https://explore-education-statistics.service.gov.uk/data-catalogue/data-set/7be58881-d49f-4e3b-b2b6-0877a1a0fe6e`
- public CSV route:
  - `https://explore-education-statistics.service.gov.uk/data-catalogue/data-set/7be58881-d49f-4e3b-b2b6-0877a1a0fe6e/csv`
- observed file name from `Content-Disposition`:
  - `ees_ks4_inst_202223.csv`
- observed middleware rewrite header:
  - `https://content.explore-education-statistics.service.gov.uk/api/data-set-files/7be58881-d49f-4e3b-b2b6-0877a1a0fe6e/download`

16-18 destinations:

- release page:
  - `https://explore-education-statistics.service.gov.uk/find-statistics/16-18-destination-measures/2023-24`
- data-catalogue page:
  - `https://explore-education-statistics.service.gov.uk/data-catalogue/data-set/bbee3278-589b-436f-a031-adeb0368e49f`
- public CSV route:
  - `https://explore-education-statistics.service.gov.uk/data-catalogue/data-set/bbee3278-589b-436f-a031-adeb0368e49f/csv`
- observed file name from `Content-Disposition`:
  - `ees_ks5_inst_202223.csv`
- observed middleware rewrite header:
  - `https://content.explore-education-statistics.service.gov.uk/api/data-set-files/bbee3278-589b-436f-a031-adeb0368e49f/download`

## Contract Corrections From The Earlier Draft

1. The previously documented data-catalogue ids (`78d96e14-...` and `948a4774-...`) are stale and should not be used.
2. The live 2023/24 release pages currently publish destination-year `2022/23` CSV assets (`time_period=202223`).
3. The public `.../data-catalogue/data-set/<id>/csv` route is the stable Bronze contract.
4. The `x-middleware-rewrite` header is observable, but the rewritten content API URL should not be treated as the public contract. Direct probes of that rewritten URL returned `404` from this environment.
5. The raw files are not already flattened into one-row-per-school percentage columns. They contain mixed count and percentage rows segmented by breakdown dimensions.

## Observed HTTP Contract

For both public CSV routes on 2026-03-11:

- HTTP status: `200 OK`
- `Content-Type`: `text/csv`
- `Content-Disposition`: attachment with the expected CSV file name
- `x-middleware-rewrite`: points at a `content.explore-education-statistics.../api/data-set-files/<id>/download` URL

Best practice:

1. Download from the public CSV route.
2. Record the observed rewrite target in the manifest for diagnostics.
3. Do not build the Bronze downloader around the rewritten content URL unless it is separately re-proved as a supported public dependency.

## Source Header Contracts

KS4 headers proved from the downloaded Bronze file:

- `time_period`
- `time_identifier`
- `geographic_level`
- `country_code`
- `country_name`
- `region_code`
- `region_name`
- `old_la_code`
- `new_la_code`
- `la_name`
- `local_authority_selection_status`
- `school_laestab`
- `school_urn`
- `school_name`
- `admission_policy`
- `entry_gender`
- `institution_group`
- `institution_type`
- `breakdown_topic`
- `breakdown`
- `data_type`
- `version`
- `cohort`
- `overall`
- `education`
- `fe`
- `ssf`
- `sfc`
- `other_edu`
- `appren`
- `all_work`
- `all_notsust`
- `all_unknown`

16-18 headers proved from the downloaded Bronze file:

- `time_period`
- `time_identifier`
- `geographic_level`
- `country_code`
- `country_name`
- `region_code`
- `region_name`
- `old_la_code`
- `new_la_code`
- `la_name`
- `local_authority_selection_status`
- `school_laestab`
- `school_urn`
- `school_name`
- `admission_policy`
- `entry_gender`
- `institution_group`
- `institution_type`
- `cohort_level_group`
- `cohort_level`
- `breakdown_topic`
- `breakdown`
- `data_type`
- `version`
- `cohort`
- `overall`
- `education`
- `he`
- `fe`
- `other_edu`
- `appren`
- `all_work`
- `all_notsust`
- `all_unknown`

## Observed Data Semantics

1. `cohort` is a numeric cohort count, not a cohort label.
2. `data_type` distinguishes `Number of students` rows from `Percentage` rows.
3. `breakdown_topic` and `breakdown` create multiple rows per school-year-stage.
4. 16-18 adds qualification dimensions via `cohort_level_group` and `cohort_level`.
5. KS4 publishes education subcomponents via `fe`, `ssf`, `sfc`, and `other_edu`.
6. 16-18 publishes education subcomponents via `he`, `fe`, and `other_edu`.
7. Published suppression tokens such as `c` appear in measure columns and must remain raw in Bronze.
8. The published `overall` field already represents the combined sustained destination measure. It should be treated as the source of truth rather than re-derived from subcolumns.

## Bronze Rules

1. Store raw CSV assets under:
   - `data/bronze/leaver_destinations/<run-date>/ks4/<destination-year>/`
   - `data/bronze/leaver_destinations/<run-date>/16_to_18/<destination-year>/`
2. The canonical downloader target is the public CSV route, not the rewritten content URL.
3. Bronze manifests must capture:
   - release page URL
   - data-catalogue page URL
   - public CSV route URL
   - observed HTTP status
   - observed `Content-Type`
   - observed `Content-Disposition`
   - observed middleware rewrite target
   - downloaded timestamp
   - checksum
   - row count
   - header count
   - full header list
4. Destination year must be derived from the downloaded asset (`time_period` and file name), not inferred from the release slug.
5. Bronze must preserve the exact raw CSV values, including suppression tokens and duplicated count/percentage rows.
6. Contract validation must fail fast on:
   - non-200 response
   - non-CSV response
   - header drift
   - empty payload
7. If the public CSV route stops working, stop and re-prove the live source contract before Gold work continues.

## Repository File Plan

Add:

- `apps/backend/src/civitas/infrastructure/pipelines/leaver_destinations.py`
- `apps/backend/src/civitas/infrastructure/pipelines/contracts/leaver_destinations.py`
- settings extensions in `apps/backend/src/civitas/infrastructure/config/settings.py`
- source registration in pipeline registry and CLI

Tests:

- `apps/backend/tests/unit/test_leaver_destinations_contract.py`
- `apps/backend/tests/integration/test_leaver_destinations_pipeline.py`

## Acceptance Criteria

1. Both datasets can be downloaded reproducibly into Bronze through the public CSV route.
2. Contract tests lock the proved live headers above.
3. Bronze manifests record both the public CSV route and the observed rewrite target.
4. The Bronze strategy does not depend on the stale dataset ids or direct content-API calls.
