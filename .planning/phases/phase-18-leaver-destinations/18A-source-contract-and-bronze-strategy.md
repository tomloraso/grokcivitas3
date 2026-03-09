# Phase 18 / 18A Design - Source Contract And Bronze Strategy

## Document Control

- Status: Planned
- Last updated: 2026-03-09
- Depends on:
  - `.planning/project-brief.md`
  - `docs/runbooks/pipelines.md`

## Objective

Freeze the exact school-level destination source contract and define the Bronze strategy.

## Verified Source Pages

KS4 destinations:

- release page:
  - `https://explore-education-statistics.service.gov.uk/find-statistics/key-stage-4-destination-measures/2023-24`
- data-catalogue page:
  - `https://explore-education-statistics.service.gov.uk/data-catalogue/data-set/78d96e14-1ebb-43cf-af12-ef2523a6e78a`
- human CSV route:
  - `https://explore-education-statistics.service.gov.uk/data-catalogue/data-set/78d96e14-1ebb-43cf-af12-ef2523a6e78a/csv`
- browser rewrite target observed from HTTP headers:
  - `https://content.explore-education-statistics.service.gov.uk/api/data-set-files/78d96e14-1ebb-43cf-af12-ef2523a6e78a/download`

16-18 destinations:

- release page:
  - `https://explore-education-statistics.service.gov.uk/find-statistics/16-18-destination-measures/2023-24`
- data-catalogue page:
  - `https://explore-education-statistics.service.gov.uk/data-catalogue/data-set/948a4774-f40a-43c8-bc18-be9f143367a2`
- human CSV route:
  - `https://explore-education-statistics.service.gov.uk/data-catalogue/data-set/948a4774-f40a-43c8-bc18-be9f143367a2/csv`
- browser rewrite target observed from HTTP headers:
  - `https://content.explore-education-statistics.service.gov.uk/api/data-set-files/948a4774-f40a-43c8-bc18-be9f143367a2/download`

## Source Header Contracts

KS4 source columns verified from the data-catalogue page preview after opening the live dataset page:

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
- `school_urn`
- `school_name`
- `school_type`
- `destination_measure`
- `cohort`
- `sustained_education_destination`
- `apprenticeship_destination`
- `employment_destination`
- `not_sustained_destination`
- `destination_not_captured`

16-18 source columns verified from the data-catalogue page preview after opening the live dataset page:

- `time_period`
- `time_identifier`
- `geographic_level`
- `country_code`
- `country_name`
- `region_code`
- `region_name`
- `new_la_code`
- `old_la_code`
- `la_name`
- `school_urn`
- `school_name`
- `school_type`
- `cohort`
- `destination_measure`
- `sustained_education_destination`
- `apprenticeship_destination`
- `employment_destination`
- `education_employment_training_destination`
- `destination_not_captured`

## Bronze Rules

1. Store raw CSV assets under:
   - `data/bronze/leaver_destinations/ks4/<academic_year>/`
   - `data/bronze/leaver_destinations/16_to_18/<academic_year>/`
2. Manifest metadata must capture:
   - source page URL
   - CSV route URL
   - downloaded timestamp
   - checksum
   - row count
3. Do not use the empty release-file endpoints for Bronze.
4. First implementation slice must prove the downloader against the browser-visible route and the rewrite target above before Gold work begins.
5. Use a browser-style User-Agent for download requests and fail fast on 4xx or schema drift.
6. If the browser route and rewrite target still do not yield a downloadable payload in implementation, stop and record the new source contract before proceeding.

## Repository File Plan

Add:

- `apps/backend/src/civitas/infrastructure/pipelines/leaver_destinations.py`
- `apps/backend/src/civitas/infrastructure/pipelines/contracts/leaver_destinations.py`
- `apps/backend/src/civitas/infrastructure/config/settings.py`
- source registration in pipeline registry and CLI

Tests:

- `apps/backend/tests/unit/test_leaver_destinations_contract.py`
- `apps/backend/tests/integration/test_leaver_destinations_pipeline.py`

## Acceptance Criteria

1. Both datasets can be downloaded reproducibly into Bronze.
2. Contract tests lock the source columns used by the pipeline.
3. The Bronze strategy is independent of the empty release-file path.
