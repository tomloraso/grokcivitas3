# Phase 16 / 16B Design - Teacher Characteristics Pipeline

## Document Control

- Status: Implemented (2026-03-11)
- Last updated: 2026-03-11
- Depends on:
  - `.planning/phases/phase-16-workforce-census-depth/16A-source-catalog-and-schema-freeze.md`

## Objective

Add teacher-characteristics history and leadership composition to the existing workforce pipeline.

## Bronze -> Silver -> Gold Flow

1. Bronze:
   - download and retain the raw teacher-characteristics ZIP
   - record ZIP checksum and internal entry list in manifest metadata
2. Silver:
   - parse each yearly `workforce_teacher_characteristics_school_<yyyyyy>.csv` entry
   - normalize suppression tokens such as `c` or `u`
   - stage one row per `(run_id, academic_year, urn, characteristic_group, characteristic)`
3. Gold:
   - persist granular teacher rows in `school_teacher_characteristics_yearly`
   - derive leadership totals and teacher totals into `school_workforce_yearly`

## Silver Schema

Create `school_teacher_characteristics_stage` with:

- `run_id uuid not null`
- `academic_year text not null`
- `urn bigint not null`
- `school_laestab text null`
- `school_name text not null`
- `school_type text null`
- `characteristic_group text not null`
- `characteristic text not null`
- `grade text null`
- `sex text null`
- `age_group text null`
- `working_pattern text null`
- `qts_status text null`
- `on_route text null`
- `ethnicity_major text null`
- `teacher_fte numeric(12,2) null`
- `teacher_headcount numeric(12,2) null`
- `teacher_fte_pct numeric(7,4) null`
- `teacher_headcount_pct numeric(7,4) null`

## Gold Schema

Create `school_teacher_characteristics_yearly` keyed by `(urn, academic_year, characteristic_group, characteristic)`:

- `urn bigint not null`
- `academic_year text not null`
- `characteristic_group text not null`
- `characteristic text not null`
- `grade text null`
- `sex text null`
- `age_group text null`
- `working_pattern text null`
- `qts_status text null`
- `on_route text null`
- `ethnicity_major text null`
- `teacher_fte numeric(12,2) null`
- `teacher_headcount numeric(12,2) null`
- `teacher_fte_pct numeric(7,4) null`
- `teacher_headcount_pct numeric(7,4) null`

Extend `school_workforce_yearly` with these derived fields:

- `teacher_headcount_total numeric(12,2) null`
- `teacher_fte_total numeric(12,2) null`
- `headteacher_headcount numeric(12,2) null`
- `deputy_headteacher_headcount numeric(12,2) null`
- `assistant_headteacher_headcount numeric(12,2) null`
- `classroom_teacher_headcount numeric(12,2) null`
- `leadership_headcount numeric(12,2) null`
- `leadership_share_of_teachers numeric(7,4) null`
- `teacher_female_pct numeric(7,4) null`
- `teacher_male_pct numeric(7,4) null`
- `teacher_qts_pct numeric(7,4) null`
- `teacher_unqualified_pct numeric(7,4) null`

## Derivation Rules

Use rows where `characteristic_group = 'Total'` to populate total teacher counts.

Use rows where `characteristic_group = 'Grade'` to derive:

- headteacher
- deputy headteacher
- assistant headteacher
- classroom teacher
- leadership total as head + deputy + assistant

Use rows where `characteristic_group = 'Sex'`, `QTS status`, `Age group`, and `Ethnicity Major` to populate granular trend surfaces.

## Repository File Plan

Add or edit:

- `apps/backend/src/civitas/infrastructure/pipelines/dfe_workforce.py`
- `apps/backend/src/civitas/infrastructure/pipelines/contracts/dfe_workforce.py`
- `apps/backend/alembic/versions/<new>_phase_16_teacher_characteristics.py`
- `apps/backend/tests/unit/test_dfe_workforce_contract.py`
- `apps/backend/tests/integration/test_dfe_workforce_pipeline.py`

## Vertical Slice Sequence

1. Slice 16B.1:
   - Bronze ZIP ingest
   - internal-entry parsing tests
   - stage table promotion
2. Slice 16B.2:
   - Gold granular table
   - teacher totals and leadership derivations
3. Slice 16B.3:
   - profile/trends mapping for teacher characteristics and leadership size

## Acceptance Criteria

1. Teacher-characteristics history is queryable by school and academic year.
2. Leadership size derives from published grade rows, not inferred from names or external metadata.
3. Suppressed values stay suppressed and do not become zero.
