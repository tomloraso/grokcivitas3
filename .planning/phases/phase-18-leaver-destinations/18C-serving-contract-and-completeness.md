# Phase 18 / 18C Design - Serving Contract And Completeness

## Document Control

- Status: Planned
- Last updated: 2026-03-09
- Depends on:
  - `.planning/phases/phase-18-leaver-destinations/18B-destinations-pipeline-and-gold-schema.md`

## Objective

Expose destination outcomes in profile and trends while preserving stage and scope boundaries.

## Serving Additions

Profile latest:

- `destinations_latest.ks4`
- `destinations_latest.study_16_18`

Each stage block should expose:

- `cohort`
- `destination_measure`
- `sustained_education_pct`
- `apprenticeship_pct`
- `employment_pct`
- `positive_destination_pct`
- `not_sustained_pct`
- `education_employment_training_pct`
- `destination_not_captured_pct`

Trend additions:

- destination series by stage and cohort

## Completeness Rules

1. KS4 destination coverage is in-scope for the current brief.
2. 16-18 destination coverage should be feature-flagged or release-sequenced if the brief remains 4-16.
3. Missing stage data must not remove the other stage from the payload.
4. If only one cohort is published for a school-year, preserve it and expose the cohort label.

## Repository File Plan

Expected backend files:

- `apps/backend/src/civitas/infrastructure/persistence/postgres_school_profile_repository.py`
- `apps/backend/src/civitas/infrastructure/persistence/postgres_school_trends_repository.py`
- `apps/backend/src/civitas/application/school_profiles/`
- `apps/backend/src/civitas/application/school_trends/`

## Acceptance Criteria

1. Destination metrics are returned with clear stage labeling.
2. The API can omit 16-18 without breaking the KS4 surface if the product scope remains 4-16.
3. Completeness metadata distinguishes unsupported stage from missing source row.
