# Phase 17 / 17C Design - Serving Contract And Completeness

## Document Control

- Status: Implemented (2026-03-11)
- Last updated: 2026-03-11
- Depends on:
  - `.planning/phases/phase-18-leaver-destinations/18B-destinations-pipeline-and-gold-schema.md`

## Objective

Expose destination outcomes in profile and trends with clear stage labeling, without hiding the proved differences between KS4 and 16-18 row structure.

## Serving Additions

Profile latest:

- `destinations_latest.ks4`
- `destinations_latest.study_16_18`

Each stage block should expose:

- `academic_year`
- `cohort_count`
- `qualification_group`
- `qualification_level`
- `overall_pct`
- `education_pct`
- `apprenticeship_pct`
- `employment_pct`
- `not_sustained_pct`
- `activity_unknown_pct`
- `fe_pct`
- `other_education_pct`
- `school_sixth_form_pct`
- `sixth_form_college_pct`
- `higher_education_pct`

Serving rules:

1. KS4 returns `qualification_group = null` and `qualification_level = null` at the API boundary, even though Gold stores blank strings for those key columns.
2. KS4 uses `school_sixth_form_pct` and `sixth_form_college_pct`; `higher_education_pct` remains `null`.
3. 16-18 uses `higher_education_pct`; `school_sixth_form_pct` and `sixth_form_college_pct` remain `null`.
4. The initial profile slice should read the published total row:
   - `breakdown_topic = 'Total'`
   - `breakdown = 'Total'`
   - and for KS4:
     - `qualification_group = ''`
     - `qualification_level = ''`
   - and for 16-18:
     - `qualification_group = 'Total'`
     - `qualification_level = 'Total'`

## Trend Additions

Trend payloads should add stage-aware total-row series for:

- `ks4_overall_pct`
- `ks4_education_pct`
- `ks4_apprenticeship_pct`
- `ks4_employment_pct`
- `ks4_not_sustained_pct`
- `ks4_activity_unknown_pct`
- `study_16_18_overall_pct`
- `study_16_18_education_pct`
- `study_16_18_apprenticeship_pct`
- `study_16_18_employment_pct`
- `study_16_18_not_sustained_pct`
- `study_16_18_activity_unknown_pct`

Initial trend scope should stay on total rows only. Breakdown and qualification subgroup trends can remain a later enhancement.

## Completeness Rules

1. KS4 destination coverage is in-scope for the current brief.
2. 16-18 destination coverage should be feature-flagged or release-sequenced if the brief remains 4-16.
3. Missing stage data must not remove the other stage from the payload.
4. If only non-total rows are present for a school-year-stage, mark the section `partial`, not `unavailable`.
5. If 16-18 is intentionally withheld for scope reasons, completeness must report `unsupported_stage` rather than `source_missing`.
6. If the total row is missing but the school has other destination rows, completeness should distinguish that from an entirely missing school-year.

## Required Completeness Additions

Add `unsupported_stage` to the destination completeness reason set across:

- domain models
- application DTOs
- API schemas

This is required to meet the phase requirement that unsupported product scope be distinguishable from missing source data.

## Repository File Plan

Expected backend files:

- `apps/backend/src/civitas/infrastructure/persistence/postgres_school_profile_repository.py`
- `apps/backend/src/civitas/infrastructure/persistence/postgres_school_trends_repository.py`
- `apps/backend/src/civitas/application/school_profiles/`
- `apps/backend/src/civitas/application/school_trends/`
- `apps/backend/src/civitas/domain/school_profiles/models.py`
- `apps/backend/src/civitas/domain/school_trends/models.py`
- `apps/backend/src/civitas/api/schemas/school_profiles.py`
- `apps/backend/src/civitas/api/schemas/school_trends.py`

## Acceptance Criteria

1. Destination metrics are returned with explicit stage labeling and stage-specific nullable fields.
2. The API can omit 16-18 without breaking the KS4 surface if the product scope remains 4-16.
3. Completeness metadata distinguishes `unsupported_stage` from missing source rows.
4. Initial serving reads use the published total rows rather than derived or reconstructed pseudo-rows.
