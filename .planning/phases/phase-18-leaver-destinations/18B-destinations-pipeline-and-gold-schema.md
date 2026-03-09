# Phase 18 / 18B Design - Destinations Pipeline And Gold Schema

## Document Control

- Status: Planned
- Last updated: 2026-03-09
- Depends on:
  - `.planning/phases/phase-18-leaver-destinations/18A-source-contract-and-bronze-strategy.md`

## Objective

Normalize KS4 and 16-18 destination datasets into a unified school destination Gold table.

## Gold Schema

Create `school_leaver_destinations_yearly` keyed by `(urn, academic_year, destination_stage, cohort, destination_measure)`:

- `urn bigint not null`
- `academic_year text not null`
- `destination_stage text not null`
- `cohort text not null`
- `destination_measure text not null`
- `school_name text not null`
- `school_type text null`
- `sustained_education_pct numeric(7,4) null`
- `apprenticeship_pct numeric(7,4) null`
- `employment_pct numeric(7,4) null`
- `not_sustained_pct numeric(7,4) null`
- `education_employment_training_pct numeric(7,4) null`
- `destination_not_captured_pct numeric(7,4) null`
- `positive_destination_pct numeric(7,4) null`

Stage rules:

- `destination_stage = 'ks4'` for the KS4 dataset
- `destination_stage = '16_to_18'` for the study-leaver dataset

## Derivation Rules

1. For KS4:
   - `positive_destination_pct = sustained_education_pct + apprenticeship_pct + employment_pct`
2. For 16-18:
   - if `education_employment_training_pct` is present, persist it as published
   - otherwise derive `positive_destination_pct` from education + apprenticeship + employment
3. Preserve `not_sustained_pct` only where published.

## Pipeline Design

1. Bronze:
   - one raw CSV asset per dataset and academic year
2. Silver:
   - stage tables:
     - `school_ks4_destinations_stage`
     - `school_16_to_18_destinations_stage`
3. Gold:
   - normalize both into `school_leaver_destinations_yearly`
   - use a strict unioned mapper so stage-specific columns become nullable Gold fields rather than bespoke API logic

## Repository File Plan

Add or edit:

- `apps/backend/src/civitas/infrastructure/pipelines/leaver_destinations.py`
- `apps/backend/alembic/versions/<new>_phase_18_school_leaver_destinations.py`
- `apps/backend/src/civitas/infrastructure/pipelines/base.py`
- `apps/backend/src/civitas/infrastructure/pipelines/__init__.py`
- `apps/backend/src/civitas/cli/main.py`

## Vertical Slice Sequence

1. Slice 18B.1:
   - KS4 Bronze and Gold path
2. Slice 18B.2:
   - 16-18 Bronze and Gold path
3. Slice 18B.3:
   - unified Gold table and completeness wiring

## Acceptance Criteria

1. School destination rows are keyed consistently by school, year, stage, and cohort.
2. Stage-specific fields are preserved without lossy coercion.
3. No request-time transformation is required to combine KS4 and 16-18 data.
