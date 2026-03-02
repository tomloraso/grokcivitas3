# Phase 1B Design - DfE Characteristics Bronze To Gold Pipeline

## Document Control

- Status: Draft
- Last updated: 2026-03-02
- Depends on:
  - `.planning/phases/phase-1/1A-source-contract-gate.md`
  - `.planning/phases/phase-0/0A-data-platform-baseline.md`
  - `.planning/phases/phase-0/0E-configuration-foundation.md`
  - `.planning/data-architecture.md`
  - `docs/architecture/backend-conventions.md`

## Objective

Implement the first Phase 1 DfE demographics pipeline using verified callable endpoints and promote typed yearly school demographics into Gold.

## Scope

### In scope

- DfE dataset discovery and download from validated API endpoints.
- Bronze archive with source metadata.
- Staging normalization, validation, and rejection logging.
- Gold upsert into `school_demographics_yearly` with typed columns.
- Idempotent rerun behavior.

### Out of scope

- Ofsted latest ingest (`1C`).
- School profile API (`1D`) and trends API (`1E`) implementation.
- Any unverified metric not present in callable source contracts.

## Source Contract

### Primary endpoint family (required)

- Base: `https://api.education.gov.uk/statistics/v1`
- Required calls:
  - `GET /publications?page=1&pageSize=20`
  - `GET /publications/{publicationId}/data-sets?page=1&pageSize=20`
  - `GET /data-sets/{dataSetId}`
  - `GET /data-sets/{dataSetId}/meta`
  - `GET /data-sets/{dataSetId}/csv`

### Current validated dataset candidate (2026-03-02)

- publication: `Key stage 2 attainment`
- dataset: `Key stage 2 institution level - Schools (School information)`
- `dataSetId=019afee4-ba17-73cb-85e0-f88c101bb734`
- verified CSV header includes:
  - `school_urn`
  - `time_period`
  - `ptfsm6cla1a`
  - `psenelek`
  - `psenelk`
  - `psenele`
  - `ptealgrp2`
  - `ptealgrp1`
  - `ptealgrp3`

### Fallback path

- `CIVITAS_DFE_CHARACTERISTICS_SOURCE_CSV` override for direct file/URL input when API download is unavailable.
- `CIVITAS_DFE_CHARACTERISTICS_DATASET_ID` override for controlled dataset switching.

## Scope Guardrails From Source Coverage

Supported from validated callable source:

- disadvantaged percentage (school-level)
- SEN percentage
- EHCP percentage
- EAL percentage
- first-language percentage breakdown (English vs unclassified)

Not currently supported from validated school-level source (2026-03-02):

- school-level ethnicity breakdown
- top non-English language breakdown
- direct FSM percentage field (source provides disadvantaged metric)

## Decisions

1. Primary key is `(urn, academic_year)`.
2. Use `school_urn` from source CSV as canonical school join key.
3. Normalize `time_period` to `academic_year` format (`YYYY/YY`) for Gold.
4. Use typed columns only in Gold; no metric-key EAV table.
5. Store source dataset id and source version for auditability.
6. Represent unavailable metrics as nullable typed columns with coverage flags; do not synthesize values.

## Data Flow

### Bronze

- Path format:
  - `data/bronze/dfe-characteristics/{yyyy-mm-dd}/school_characteristics.csv`
- Metadata sidecar:
  - `school_characteristics.metadata.json`
  - includes endpoint URL, dataset id, published version, checksum, row count.

### Staging

- Create per-run staging table in `staging` schema:
  - `staging.dfe_characteristics__{run_id}`
- Normalize and validate:
  - trim fields,
  - parse numeric/suppressed values,
  - parse `academic_year`,
  - reject rows without `school_urn` or year.
- Log rejects to `pipeline_rejections`.

### Gold

Target table: `school_demographics_yearly`

Minimum columns:

- `urn` (FK to `schools.urn`)
- `academic_year`
- `disadvantaged_pct`
- `fsm_pct` (nullable; unpopulated until verified source supports direct FSM)
- `sen_pct`
- `sen_support_pct`
- `ehcp_pct`
- `eal_pct`
- `first_language_english_pct`
- `first_language_unclassified_pct`
- `total_pupils`
- `has_ethnicity_data` (boolean)
- `has_top_languages_data` (boolean)
- `source_dataset_id`
- `source_dataset_version`
- `updated_at`

Upsert behavior:

- `INSERT ... ON CONFLICT (urn, academic_year) DO UPDATE`
- deterministic reruns on unchanged source input.

Indexes:

- PK `(urn, academic_year)`
- B-tree on `academic_year`
- B-tree on `urn`

## File-Oriented Implementation Plan

1. `apps/backend/src/civitas/infrastructure/config/settings.py`
   - add DfE dataset id/source override settings.
2. `apps/backend/src/civitas/infrastructure/pipelines/dfe_characteristics.py` (new)
   - implement `download`, `stage`, `promote`.
3. `apps/backend/src/civitas/infrastructure/pipelines/__init__.py`
   - register DfE pipeline source in registry.
4. `apps/backend/alembic/versions/*_phase1_school_demographics_yearly.py`
   - create Gold table and indexes.
5. `apps/backend/tests/fixtures/dfe_characteristics/`
   - add valid and mixed-validity CSV fixtures.
6. `apps/backend/tests/unit/test_dfe_characteristics_transforms.py` (new)
   - normalization, suppression handling, required field validation.
7. `apps/backend/tests/integration/test_dfe_characteristics_pipeline.py` (new)
   - stage/promote idempotency and schema assertions.
8. `.env.example`
   - add optional DfE source settings.

## Testing And Quality Gates

### Required tests

- Source schema mismatch fails fast with explicit error.
- Missing `school_urn` rows are rejected and logged.
- Suppressed values are normalized deterministically.
- Gold upsert is idempotent for identical source input.

### Required gates

- `uv run --project apps/backend pytest apps/backend/tests/unit/test_dfe_characteristics_transforms.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/integration/test_dfe_characteristics_pipeline.py -q`
- `make lint`
- `make test`

## Acceptance Criteria

1. `civitas pipeline run --source dfe_characteristics` completes Bronze -> Staging -> Gold.
2. `school_demographics_yearly` is populated with typed yearly rows keyed by `(urn, academic_year)`.
3. Unsupported metrics are explicit in schema and coverage flags, not implied.
4. Pipeline reruns are idempotent and rejection logging is preserved.

## Risks And Mitigations

- Risk: source dataset id changes over time.
  - Mitigation: dataset id is configurable and verified by `1A` gate.
- Risk: current source does not satisfy full product metric set.
  - Mitigation: explicit coverage flags and decision records; no silent approximation.
- Risk: limited historical years reduce trend utility.
  - Mitigation: `1E` trend-depth policy and partial-history response semantics.
