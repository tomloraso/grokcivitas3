# Phase 2B Design - Ofsted Timeline Bronze To Gold Pipeline

## Document Control

- Status: Implemented
- Last updated: 2026-03-02
- Depends on:
  - `.planning/phases/phase-2/2A-source-contract-gate.md`
  - `.planning/phases/phase-1/1C-ofsted-latest-pipeline.md`
  - `.planning/phases/phase-0/0A-data-platform-baseline.md`
  - `.planning/phases/phase-0/0E-configuration-foundation.md`
  - `.planning/data-architecture.md`
  - `docs/architecture/backend-conventions.md`

## Objective

Implement full Ofsted inspection timeline ingest using verified `all_inspections` assets, and promote canonical timeline events into Gold `ofsted_inspections`.

## Scope

### In scope

- Resolve callable Ofsted timeline assets from the landing page.
- Bronze archive for timeline assets (rolling academic-year window + optional historical baseline).
- Staging normalization across schema variants.
- Gold upsert into `ofsted_inspections` with deterministic deduplication.
- Idempotent rerun behavior.

### Out of scope

- Latest-headline-only ingest (already delivered in Phase 1C).
- API/web rendering behavior (owned by `2E`/`2F`).

## Source Contract

### Primary endpoint family (required)

- Landing page:
  - `GET https://www.gov.uk/government/statistical-data-sets/monthly-management-information-ofsteds-school-inspections-outcomes`
- Timeline asset patterns:
  - `...all_inspections_-_year_to_date_published_by_*.csv`
  - `...state-funded_schools_1_September_2015_to_31_August_2019.csv`

### Verified source snapshot (2026-03-02)

- Latest YTD timeline asset:
  - `https://assets.publishing.service.gov.uk/media/698b20be235b57593bc1be33/Management_information_-_state-funded_schools_-_all_inspections_-_year_to_date_published_by_31_Jan_2026.csv`
- Historical baseline asset:
  - `https://assets.publishing.service.gov.uk/media/5f6b4b76d3bf7f72337b6ef7/Management_information_-_state-funded_schools_1_September_2015_to_31_August_2019.csv`
- Verified YTD header fields:
  - `URN`
  - `Inspection number`
  - `Inspection type`
  - `Inspection start date`
  - `Publication date`
  - `Category of concern`
  - `Leadership and governance`
- Verified historical baseline header (line 2 after preamble):
  - `Academic year`
  - `URN`
  - `Inspection number`
  - `Inspection start date`
  - `Publication date`
  - `Overall effectiveness`

### Fallback path

- `CIVITAS_OFSTED_TIMELINE_SOURCE_INDEX_URL` override for landing page/index source.
- `CIVITAS_OFSTED_TIMELINE_SOURCE_ASSETS` override for explicit timeline CSV asset list.
- `CIVITAS_OFSTED_TIMELINE_YEARS` rolling academic-year window size (default 10).
- `CIVITAS_OFSTED_TIMELINE_INCLUDE_HISTORICAL_BASELINE` toggle for controlled backfill behavior.

## Decisions

1. Timeline ingest is asset-list-driven, not single-file-driven.
2. Parser supports two source schema versions:
   - `all_inspections_ytd` (post-2019 monthly assets),
   - `all_inspections_historical_2015_2019` (with preamble row).
3. Canonical timeline key is `inspection_number`; rows without `inspection_number` are rejected.
4. Preserve both:
   - normalized outcome fields (`overall_effectiveness_label` where available),
   - raw headline outcome text (`headline_outcome_text`) for schema-variant compatibility.
5. Keep `school_ofsted_latest` (Phase 1) as existing latest-headline source while timeline path hardens; parity checks can merge behavior later.
6. Do not infer a graded Ofsted code when the source only provides textual/section outcomes.

## Implementation Progress (2026-03-02)

- Completed: added `OfstedTimelinePipeline`:
  - `apps/backend/src/civitas/infrastructure/pipelines/ofsted_timeline.py`
  - supports asset-list ingestion, schema-variant handling, staging dedupe, and Gold upsert.
- Completed: extended pipeline registration and source enum wiring:
  - `apps/backend/src/civitas/infrastructure/pipelines/{base.py,__init__.py}`
- Completed: added settings support for timeline source controls:
  - `CIVITAS_OFSTED_TIMELINE_SOURCE_INDEX_URL`
  - `CIVITAS_OFSTED_TIMELINE_SOURCE_ASSETS`
  - `CIVITAS_OFSTED_TIMELINE_INCLUDE_HISTORICAL_BASELINE`
- Completed: added migration for Gold timeline table:
  - `apps/backend/alembic/versions/20260302_06_phase2_ofsted_inspections.py`
- Completed: added fixtures and tests:
  - `apps/backend/tests/fixtures/ofsted_timeline/*`
  - `apps/backend/tests/unit/test_ofsted_timeline_transforms.py`
  - `apps/backend/tests/integration/test_ofsted_timeline_pipeline.py`
- Completed: updated local configuration/runbook + CLI source coverage:
  - `.env.example`
  - `docs/runbooks/local-development.md`
  - `apps/backend/tests/unit/test_pipeline_cli.py`
  - `apps/backend/tests/unit/test_settings.py`
- Verification commands executed:
  - `uv run --project apps/backend ruff check apps/backend`
  - `uv run --project apps/backend pytest apps/backend/tests/unit/test_ofsted_timeline_transforms.py apps/backend/tests/integration/test_ofsted_timeline_pipeline.py apps/backend/tests/unit/test_pipeline_cli.py apps/backend/tests/unit/test_settings.py -q`
  - `uv run --project apps/backend python tools/scripts/verify_phase2_sources.py`

## Data Flow

### Bronze

- Path format:
  - `data/bronze/ofsted_timeline/{yyyy-mm-dd}/`
- Stored assets:
  - landing-page snapshot (`index.html`),
  - selected timeline CSV files,
  - `assets.manifest.json` containing asset URL, checksum, schema variant, and row count.

### Staging

- Per-run staging tables:
  - `staging.ofsted_timeline_raw__{run_id}`
  - `staging.ofsted_timeline_normalized__{run_id}`
- Normalization responsibilities:
  - schema-variant detection,
  - optional preamble-row skip for 2015-2019 file,
  - date parsing,
  - outcome normalization,
  - required-field validation (`URN`, `Inspection number`, `Inspection start date`),
  - reject logging to `pipeline_rejections`.

### Gold

Target table: `ofsted_inspections`

Minimum columns:

- `inspection_number` (PK)
- `urn`
- `inspection_start_date`
- `inspection_end_date`
- `publication_date`
- `inspection_type`
- `inspection_type_grouping`
- `event_type_grouping`
- `overall_effectiveness_code` (nullable)
- `overall_effectiveness_label` (nullable)
- `headline_outcome_text` (nullable)
- `category_of_concern` (nullable)
- `source_schema_version`
- `source_asset_url`
- `source_asset_month`
- `updated_at`

Upsert behavior:

- `INSERT ... ON CONFLICT (inspection_number) DO UPDATE`
- deterministic reruns from unchanged Bronze input.

Indexes:

- PK on `inspection_number`
- B-tree on `(urn, inspection_start_date DESC)`
- B-tree on `publication_date`

## File-Oriented Implementation Plan

1. `apps/backend/src/civitas/infrastructure/config/settings.py`
   - add Ofsted timeline source settings and overrides.
2. `apps/backend/src/civitas/infrastructure/pipelines/ofsted_timeline.py` (new)
   - implement download, stage, promote for timeline assets.
3. `apps/backend/src/civitas/infrastructure/pipelines/__init__.py`
   - register `ofsted_timeline` pipeline source.
4. `apps/backend/alembic/versions/*_phase2_ofsted_inspections.py` (new)
   - create Gold timeline table + indexes.
5. `apps/backend/tests/fixtures/ofsted_timeline/` (new)
   - add fixtures for:
     - YTD schema,
     - 2015-2019 schema with preamble.
6. `apps/backend/tests/unit/test_ofsted_timeline_transforms.py` (new)
   - schema-version parsing and normalization coverage.
7. `apps/backend/tests/integration/test_ofsted_timeline_pipeline.py` (new)
   - Bronze -> Silver -> Gold idempotency and dedupe coverage.

## Testing And Quality Gates

### Required tests

- YTD schema rows parse correctly to canonical fields.
- Historical preamble-row file parses correctly.
- Missing required fields are rejected and logged.
- Duplicate inspections across multiple YTD assets upsert deterministically.

### Required gates

- `uv run --project apps/backend pytest apps/backend/tests/unit/test_ofsted_timeline_transforms.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/integration/test_ofsted_timeline_pipeline.py -q`
- `make lint`
- `make test`

## Acceptance Criteria

1. `civitas pipeline run --source ofsted_timeline` completes Bronze -> Silver -> Gold.
2. `ofsted_inspections` contains canonical timeline events with deterministic keys.
3. Pipeline supports both verified schema variants without manual intervention.
4. Reruns are idempotent and rejection logging is preserved.

## Risks And Mitigations

- Risk: Ofsted asset naming or HTML structure changes.
  - Mitigation: link-extraction tests and explicit asset override support.
- Risk: schema drift between timeline assets causes silent mapping issues.
  - Mitigation: schema-variant detection with strict required-field assertions.
- Risk: latest YTD files alone provide incomplete history.
  - Mitigation: explicit historical baseline backfill requirement in pipeline design.
