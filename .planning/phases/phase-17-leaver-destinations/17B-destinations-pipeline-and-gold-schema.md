# Phase 17 / 17B Design - Destinations Pipeline And Gold Schema

## Document Control

- Status: Implemented (2026-03-11)
- Last updated: 2026-03-11
- Depends on:
  - `.planning/phases/phase-18-leaver-destinations/18A-source-contract-and-bronze-strategy.md`

## Objective

Normalize the proved KS4 and 16-18 raw CSV shape into a unified Gold model that preserves the published row semantics while still supporting profile and trends reads without request-time pivot logic.

## Design Correction From The Earlier Draft

The raw files do not publish one destination measure per row with already-flattened percentage columns.

They publish:

1. multiple measure columns on each row (`overall`, `education`, `appren`, `all_work`, and stage-specific education subcomponents)
2. mixed `Number of students` and `Percentage` rows, distinguished by `data_type`
3. breakdown dimensions (`breakdown_topic`, `breakdown`)
4. 16-18 qualification dimensions (`cohort_level_group`, `cohort_level`)

Because of that, the earlier `(urn, academic_year, destination_stage, cohort, destination_measure)` model is not faithful to the proved source contract and should not be implemented.

## Gold Schema

Create `school_leaver_destinations_yearly` keyed by:

- `(urn, academic_year, destination_stage, qualification_group, qualification_level, breakdown_topic, breakdown)`

Columns:

- `urn bigint not null`
- `academic_year text not null`
- `destination_stage text not null`
- `qualification_group text not null`
- `qualification_level text not null`
- `breakdown_topic text not null`
- `breakdown text not null`
- `school_name text not null`
- `school_laestab text null`
- `admission_policy text null`
- `entry_gender text null`
- `institution_group text null`
- `institution_type text null`
- `cohort_count integer null`
- `overall_count integer null`
- `overall_pct numeric(7,4) null`
- `education_count integer null`
- `education_pct numeric(7,4) null`
- `apprenticeship_count integer null`
- `apprenticeship_pct numeric(7,4) null`
- `employment_count integer null`
- `employment_pct numeric(7,4) null`
- `not_sustained_count integer null`
- `not_sustained_pct numeric(7,4) null`
- `activity_unknown_count integer null`
- `activity_unknown_pct numeric(7,4) null`
- `fe_count integer null`
- `fe_pct numeric(7,4) null`
- `other_education_count integer null`
- `other_education_pct numeric(7,4) null`
- `school_sixth_form_count integer null`
- `school_sixth_form_pct numeric(7,4) null`
- `sixth_form_college_count integer null`
- `sixth_form_college_pct numeric(7,4) null`
- `higher_education_count integer null`
- `higher_education_pct numeric(7,4) null`
- `source_file_url text not null`
- `source_updated_at_utc timestamptz not null`

Stage rules:

- `destination_stage = 'ks4'` for the KS4 dataset
- `destination_stage = '16_to_18'` for the 16-18 study-leaver dataset
- KS4 normalizes `qualification_group` and `qualification_level` to blank strings in Gold so the composite primary key remains stable; the serving layer maps those blanks back to `null`

## Derivation Rules

1. Parse `academic_year` from `time_period`:
   - `202223 -> 2022/23`
2. Treat `cohort` as a published cohort count:
   - persist as `cohort_count`
3. Pivot `data_type`:
   - `Number of students` -> `*_count`
   - `Percentage` -> `*_pct`
4. Use published `overall_*` as the source of truth for the combined sustained destination measure.
5. Do not derive `overall_pct` or `overall_count` from subcolumns except for optional validation checks with tolerance.
6. Map source fields as follows:
   - `appren -> apprenticeship_*`
   - `all_work -> employment_*`
   - `all_notsust -> not_sustained_*`
   - `all_unknown -> activity_unknown_*`
   - `other_edu -> other_education_*`
7. Stage-specific education subcomponents:
   - KS4:
     - `ssf -> school_sixth_form_*`
     - `sfc -> sixth_form_college_*`
   - 16-18:
     - `he -> higher_education_*`
8. Preserve all breakdown rows in Gold. Initial profile/trends slices can filter to published totals without re-pivoting raw Bronze data at request time.

## Pipeline Design

1. Bronze:
   - one raw CSV asset per stage and destination year under the run-date directory
2. Silver:
   - `school_ks4_destinations_stage`
   - `school_16_to_18_destinations_stage`
   - each stage table keeps normalized row dimensions:
     - school identifiers
     - `academic_year`
     - `qualification_group`
     - `qualification_level`
     - `breakdown_topic`
     - `breakdown`
     - `data_type`
     - raw measure values after null-token handling
3. Gold:
   - pivot count and percentage rows into `school_leaver_destinations_yearly`
   - preserve stage-specific nullable columns instead of flattening KS4 and 16-18 into fake common measure names

## Serving Slice Guidance

Initial serving slices should read the most comparable published rows:

1. `breakdown_topic = 'Total'`
2. `breakdown = 'Total'`
3. For 16-18, prefer:
   - `qualification_group = 'Total'`
   - `qualification_level = 'Total'`

This keeps the first product slice simple without discarding the richer raw shape that may be needed later.

## Repository File Plan

Add or edit:

- `apps/backend/src/civitas/infrastructure/pipelines/leaver_destinations.py`
- `apps/backend/alembic/versions/<new>_phase_18_school_leaver_destinations.py`
- `apps/backend/src/civitas/infrastructure/pipelines/base.py`
- `apps/backend/src/civitas/infrastructure/pipelines/__init__.py`
- `apps/backend/src/civitas/infrastructure/config/settings.py`
- `apps/backend/src/civitas/cli/main.py`

## Vertical Slice Sequence

1. Slice 18B.1:
   - KS4 Bronze -> Silver -> Gold using the proved public CSV route and total rows
2. Slice 18B.2:
   - 16-18 Bronze -> Silver -> Gold with qualification dimensions preserved
3. Slice 18B.3:
   - shared Gold reader logic and completeness wiring for serving

## Acceptance Criteria

1. Gold rows are keyed by the published row dimensions, not by invented measure semantics.
2. Count and percentage rows are preserved without lossy coercion.
3. Published `overall` is stored directly rather than re-derived.
4. No request-time transformation is required to combine count/percentage rows for the initial profile and trends reads.
