# Phase 8 / AI-1 Design - GIAS Pipeline Enrichment

## Document Control

- Status: Implemented
- Last updated: 2026-03-06
- Depends on:
  - `.planning/phases/phase-8-ai-overview/README.md`
  - `apps/backend/src/civitas/infrastructure/pipelines/contracts/gias.py`
  - `apps/backend/src/civitas/infrastructure/pipelines/gias.py`
  - `apps/backend/src/civitas/domain/school_profiles/models.py`
  - `docs/architecture/backend-conventions.md`

## Tracking Update (2026-03-06)

- `gias.v2` is implemented with widened header validation, normalized website/telephone/age/governance fields, and soft-fail coercion for optional enrichment values.
- The `schools` Gold table was widened via Alembic and profile-serving layers were updated through domain, DTO, repository, API schema, OpenAPI, and web mapping/components.
- Aggregated normalization warnings are persisted to `pipeline_normalization_warnings` and covered in pipeline integration tests.
- The web school profile now renders the additional contact, address, characteristics, and governance fields introduced by this phase.

## Objective

Widen the GIAS pipeline from 12 extracted fields to ~30 by promoting columns already present in the Bronze CSV (`edubasealldata.csv`, 135 columns). This provides core school identity fields (website, contact, head teacher, address, age range, admissions, trust/MAT, religious character, SEN provisions) without any new external data sources.

## Scope

### In scope

- Bump GIAS normalization contract from `gias.v1` to `gias.v2`.
- Extend `REQUIRED_HEADERS`, `NormalizedGiasRow`, and `GiasStagedRow` with new fields.
- Add Alembic migration to widen the `schools` Gold table.
- Extend `SchoolProfileSchool` domain model, `SchoolProfileSchoolDto` application DTO, and API response schema.
- Extend frontend `SchoolProfileSchool` type and profile display.

### Out of scope

- AI-generated summaries (owned by `AI-2`).
- New external data sources.
- Any field not present in the existing GIAS Bronze CSV.

## Fields To Promote

### Contact and identity

| GIAS CSV column | Gold column | Type | Notes |
|---|---|---|---|
| `SchoolWebsite` | `website` | `text NULL` | Normalize URL (ensure scheme) |
| `TelephoneNum` | `telephone` | `text NULL` | Strip whitespace |
| `HeadTitle (name)` | `head_title` | `text NULL` | e.g. "Mr", "Mrs", "Dr" |
| `HeadFirstName` | `head_first_name` | `text NULL` | |
| `HeadLastName` | `head_last_name` | `text NULL` | |
| `HeadPreferredJobTitle` | `head_job_title` | `text NULL` | e.g. "Executive Headteacher" |

### Address

| GIAS CSV column | Gold column | Type | Notes |
|---|---|---|---|
| `Street` | `address_street` | `text NULL` | |
| `Locality` | `address_locality` | `text NULL` | |
| `Address3` | `address_line3` | `text NULL` | |
| `Town` | `address_town` | `text NULL` | |
| `County (name)` | `address_county` | `text NULL` | |

### Characteristics

| GIAS CSV column | Gold column | Type | Notes |
|---|---|---|---|
| `StatutoryLowAge` | `statutory_low_age` | `integer NULL` | |
| `StatutoryHighAge` | `statutory_high_age` | `integer NULL` | |
| `Gender (name)` | `gender` | `text NULL` | "Mixed", "Boys", "Girls" |
| `ReligiousCharacter (name)` | `religious_character` | `text NULL` | "Church of England", "Roman Catholic", etc. |
| `Diocese (name)` | `diocese` | `text NULL` | |
| `AdmissionsPolicy (name)` | `admissions_policy` | `text NULL` | "Selective", "Non-selective", "Not applicable" |
| `OfficialSixthForm (name)` | `sixth_form` | `text NULL` | "Has a sixth form", "Does not have a sixth form" |
| `NurseryProvision (name)` | `nursery_provision` | `text NULL` | |
| `Boarders (name)` | `boarders` | `text NULL` | |
| `PercentageFSM` | `fsm_pct_gias` | `real NULL` | GIAS-reported FSM (cross-reference with DfE) |

### Governance

| GIAS CSV column | Gold column | Type | Notes |
|---|---|---|---|
| `Trusts (name)` | `trust_name` | `text NULL` | Multi-academy trust name |
| `TrustSchoolFlag (name)` | `trust_flag` | `text NULL` | |
| `Federations (name)` | `federation_name` | `text NULL` | |
| `FederationFlag (name)` | `federation_flag` | `text NULL` | |
| `LA (name)` | `la_name` | `text NULL` | Local authority name |
| `LA (code)` | `la_code` | `text NULL` | Local authority code |

### Geography and context

| GIAS CSV column | Gold column | Type | Notes |
|---|---|---|---|
| `UrbanRural (name)` | `urban_rural` | `text NULL` | |
| `NumberOfBoys` | `number_of_boys` | `integer NULL` | |
| `NumberOfGirls` | `number_of_girls` | `integer NULL` | |
| `LSOA (code)` | `lsoa_code` | `text NULL` | Cross-references area_deprivation |
| `LSOA (name)` | `lsoa_name` | `text NULL` | |

### Change tracking

| GIAS CSV column | Gold column | Type | Notes |
|---|---|---|---|
| `LastChangedDate` | `last_changed_date` | `date NULL` | GIAS record last-changed |

## Normalization Rules

1. `SchoolWebsite`: trim whitespace; if non-empty and missing scheme, prepend `https://`. If basic validation fails, set to `None` and emit a normalization warning (do not reject the row).
2. `TelephoneNum`: strip all whitespace, keep digits and leading `+` only. If no valid number remains, set to `None` and emit a normalization warning.
3. Age fields: parse as integer; if outside `[0, 25]`, set to `None` and emit a normalization warning.
4. `PercentageFSM`: parse as float; if outside `[0, 100]`, set to `None` and emit a normalization warning.
5. `NumberOfBoys`, `NumberOfGirls`: parse as integer using existing `_parse_optional_integer`; invalid parse becomes `None` with normalization warning.
6. `LastChangedDate`: parse using existing date parser; invalid parse becomes `None` with normalization warning.
7. All text fields: strip whitespace, convert empty to `None`.
8. Hard row rejection remains limited to core identity/geometry contract failures (missing URN, missing/invalid coordinates, invalid coordinate range, unrecoverable required-field parse errors).

## Normalization Warning Telemetry

Optional-field coercions are observable through two explicit channels:

1. Structured logs emitted during stage:
   - Event name: `pipeline_normalization_warning`
   - Fields: `run_id`, `source`, `urn`, `field_name`, `reason_code`, `raw_value`
2. Aggregated persistence in Postgres:
   - Table: `pipeline_normalization_warnings`
   - Columns: `run_id`, `source`, `field_name`, `reason_code`, `warning_count`, `created_at`
   - One row per `(run_id, source, field_name, reason_code)` aggregate

Warnings are operational signals only and are not counted as `rejected_rows`.

## Decisions

1. Contract bump is `gias.v1` -> `gias.v2`. The old contract version is not maintained.
2. All new fields are nullable. Existing rows receive `NULL` for new columns via migration default.
3. Website normalization adds `https://` scheme if missing but does not validate reachability.
4. `fsm_pct_gias` is stored alongside DfE-derived FSM to allow cross-referencing; it is not the primary FSM metric.
5. LSOA code from GIAS can be used as a fallback join key for area context (currently derived from postcode).
6. Invalid optional enrichment fields must not remove the school from Gold; they are coerced to `NULL` and recorded as normalization warnings.

## File-Oriented Implementation Plan

1. `apps/backend/src/civitas/infrastructure/pipelines/contracts/gias.py`
   - Bump `CONTRACT_VERSION` to `gias.v2`.
   - Extend `REQUIRED_HEADERS` with new column names.
   - Extend `NormalizedGiasRow` TypedDict with new fields.
   - Add normalization helpers for website, telephone, age range.
   - Update `normalize_row` to extract and validate new fields with soft-fail coercion for optional fields.

2. `apps/backend/src/civitas/infrastructure/pipelines/gias.py`
   - Extend `GiasStagedRow` dataclass with new fields.
   - Update `normalize_gias_row` mapping.
   - Add normalization warning event logging and aggregate writes to `pipeline_normalization_warnings`.
   - Update staging table DDL in `stage()` to include new columns.
   - Update staging INSERT statement.
   - Update promote UPSERT to include new columns in INSERT and ON CONFLICT UPDATE.

3. `apps/backend/alembic/versions/YYYYMMDD_NN_phase_ai1_gias_enrichment.py` (new)
   - `ALTER TABLE schools ADD COLUMN` for each new field.
   - All columns nullable, no default required.
   - No index additions in this migration (indexed fields already covered by existing indices).
   - Create `pipeline_normalization_warnings` table for aggregated warning telemetry.

4. `apps/backend/src/civitas/domain/school_profiles/models.py`
   - Extend `SchoolProfileSchool` with new fields (all `| None`).

5. `apps/backend/src/civitas/application/school_profiles/dto.py`
   - Extend `SchoolProfileSchoolDto` with matching new fields.

6. `apps/backend/src/civitas/application/school_profiles/use_cases.py`
   - Update domain-to-DTO mapping for new fields.

7. `apps/backend/src/civitas/infrastructure/persistence/postgres_school_profile_repository.py`
   - Extend profile query SQL to SELECT new columns from `schools`.
   - Update `SchoolProfileSchool` construction with new fields.

8. `apps/backend/src/civitas/api/routes.py`
   - Extend `SchoolProfileSchoolResponse` Pydantic model with new fields.
   - Update domain-to-response mapping.

9. `apps/backend/src/civitas/api/schemas/` (if separate schema file exists)
   - Extend school response schema.

10. `apps/web/src/api/generated-types.ts`
    - Regenerate from OpenAPI after backend changes.

11. `apps/web/src/features/school-profile/` (profile display components)
    - Add contact details section (website, phone, head teacher).
    - Add address display.
    - Add characteristics display (age range, gender, religious character, admissions, sixth form).
    - Add governance section (trust/MAT, federation, LA).

12. `apps/backend/tests/unit/test_gias_transforms.py`
   - Extend header validation tests for new required headers.
   - Add normalization tests for website, telephone, age fields.
   - Add coercion tests for invalid website, out-of-range age, out-of-range FSM (`NULL` + warning path).

13. `apps/backend/tests/integration/test_gias_pipeline.py`
   - Verify new columns flow through stage -> promote -> Gold.
   - Verify invalid optional fields do not cause row rejection.
   - Verify warning aggregates are written to `pipeline_normalization_warnings`.

14. `apps/backend/tests/integration/test_school_profile_api.py`
   - Extend profile response assertions for new fields.

## Codex Execution Checklist

1. Add contract tests for new fields and normalization rules first.
2. Bump contract version and extend `NormalizedGiasRow` and normalization logic.
3. Extend `GiasStagedRow` and pipeline stage/promote SQL.
4. Add Alembic migration for schools table widening.
5. Extend domain model, DTO, repository query, and API schema.
6. Run unit and integration tests.
7. Regenerate OpenAPI types and extend frontend display.
8. Run full `make lint` and `make test`.

## Required Commands

- `uv run --project apps/backend pytest apps/backend/tests/unit/test_gias_transforms.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/integration/test_gias_pipeline.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/integration/test_school_profile_api.py -q`
- `make lint`
- `make test`

## Testing And Quality Gates

### Required tests

- Contract validates all 30+ required headers.
- Website normalization adds `https://` scheme when missing.
- Telephone normalization strips non-digit characters.
- Age validation coerces values outside `[0, 25]` to `NULL` with warning telemetry.
- FSM percentage coerces values outside `[0, 100]` to `NULL` with warning telemetry.
- Warning aggregates are persisted to `pipeline_normalization_warnings`.
- Full pipeline stage -> promote includes all new columns.
- Profile API response includes new fields.

### Required gates

- All existing tests pass (zero regressions).
- `make lint` clean.
- `make test` clean.

## Acceptance Criteria

1. GIAS contract version is `gias.v2` with 30+ required headers.
2. `schools` Gold table contains all new columns.
3. Profile API exposes new fields (website, telephone, head teacher, address, characteristics, governance).
4. Frontend displays contact, address, characteristic, and governance sections on school profile.
5. All new fields are nullable; existing schools receive `NULL` until next pipeline run.
6. Invalid optional enrichment values are coerced to `NULL` and logged as normalization warnings; core identity/geometry failures still write to `pipeline_rejections`.
7. Normalization warnings are emitted in structured logs and persisted as aggregates in `pipeline_normalization_warnings`.

## Risks And Mitigations

- Risk: Some GIAS CSV extracts may not include all target columns (schema drift).
  - Mitigation: `validate_headers` fails fast on missing headers; can downgrade to optional headers if specific columns prove unreliable across extracts.
- Risk: Website URLs in GIAS may be stale or broken.
  - Mitigation: Store as-is with scheme normalization; do not validate reachability. UI can indicate "school-reported website".
- Risk: Head teacher names change frequently.
  - Mitigation: Updated on each pipeline run; `LastChangedDate` provides staleness signal.
