# Phase 16 / 16B Design - Admissions Pipeline And Gold Schema

## Document Control

- Status: Implemented (2026-03-11)
- Last updated: 2026-03-11
- Depends on:
  - `.planning/phases/phase-17-school-admissions/17A-join-key-foundation-and-source-contract.md`

## Objective

Implement the Bronze -> Silver -> Gold admissions ingest and derived metrics.

## Bronze -> Silver -> Gold Flow

1. Bronze:
   - download the verified school-level CSV into `data/bronze/school_admissions/<academic_year>/`
   - capture release version id, file id, checksum, and row count in manifest
2. Silver:
   - normalize one row per source row into `school_admissions_stage`
   - parse numeric preference and offer counts
   - preserve published source ratio columns for auditability and cross-checking
   - preserve source descriptor fields for cohorting and completeness
3. Gold:
   - upsert yearly rows into `school_admissions_yearly`
   - calculate derived oversubscription and offer-rate metrics into persisted Gold columns

## Gold Schema

Create `school_admissions_yearly` keyed by `(urn, academic_year)` with:

- `urn bigint not null`
- `academic_year text not null`
- `entry_year text null`
- `school_laestab text null`
- `school_phase text null`
- `school_name text not null`
- `places_offered_total integer null`
- `preferred_offers_total integer null`
- `first_preference_offers integer null`
- `second_preference_offers integer null`
- `third_preference_offers integer null`
- `applications_any_preference integer null`
- `applications_first_preference integer null`
- `applications_second_preference integer null`
- `applications_third_preference integer null`
- `first_preference_application_to_offer_ratio numeric(9,4) null`
- `first_preference_application_to_total_places_ratio numeric(9,4) null`
- `cross_la_applications integer null`
- `cross_la_offers integer null`
- `admissions_policy text null`
- `establishment_type text null`
- `denomination text null`
- `fsm_eligible_pct numeric(7,4) null`
- `urban_rural text null`
- `allthrough_school boolean null`
- `oversubscription_ratio numeric(9,4) null`
- `first_preference_offer_rate numeric(9,4) null`
- `any_preference_offer_rate numeric(9,4) null`

## Derivation Rules

1. `oversubscription_ratio = applications_any_preference / places_offered_total`
2. `first_preference_offer_rate = first_preference_offers / applications_first_preference`
3. `any_preference_offer_rate = preferred_offers_total / applications_any_preference`
4. Preserve source ratios where published and store them alongside derived ratios for cross-checking.
5. Published source ratio columns are staged in Silver and copied to Gold without recomputation.

## Repository File Plan

Add or edit:

- `apps/backend/src/civitas/infrastructure/pipelines/school_admissions.py`
- `apps/backend/src/civitas/infrastructure/pipelines/contracts/school_admissions.py`
- `apps/backend/src/civitas/infrastructure/config/settings.py`
- `apps/backend/src/civitas/infrastructure/pipelines/base.py`
- `apps/backend/src/civitas/infrastructure/pipelines/__init__.py`
- `apps/backend/src/civitas/cli/main.py`
- `apps/backend/alembic/versions/<new>_phase_17_school_admissions_yearly.py`

Tests to add:

- `apps/backend/tests/unit/test_school_admissions_contract.py`
- `apps/backend/tests/integration/test_school_admissions_pipeline.py`

## Vertical Slice Sequence

1. Slice 17B.1:
   - GIAS join-key persistence
   - Bronze CSV ingest and manifest
2. Slice 17B.2:
   - Silver normalization
   - Gold table upsert
3. Slice 17B.3:
   - derived ratios
   - data-quality thresholds

## Acceptance Criteria

1. Admissions rows upsert deterministically by school and academic year.
2. Derived metrics are null-safe and traceable back to source counts.
3. Source descriptors needed for future similar-school cohorting are retained in Gold.
