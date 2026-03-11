# Phase 17 / 17C Design - Serving Contract And Benchmark Integration

## Document Control

- Status: Implemented (2026-03-11)
- Last updated: 2026-03-11
- Depends on:
  - `.planning/phases/phase-17-school-admissions/17B-admissions-pipeline-and-gold-schema.md`

## Objective

Expose admissions demand and offer signals through the existing Civitas serving layer.

Because the current profile and trends APIs use stable response shapes, admissions should be added as explicit nullable contract fields plus admissions completeness metadata. Admissions availability must not depend on returning a different response shape for schools or years without matched admissions rows.

## Serving Additions

Profile latest additions:

- `admissions_latest.places_offered_total`
- `admissions_latest.applications_any_preference`
- `admissions_latest.applications_first_preference`
- `admissions_latest.oversubscription_ratio`
- `admissions_latest.first_preference_offer_rate`
- `admissions_latest.any_preference_offer_rate`
- `admissions_latest.admissions_policy`

Trend additions:

- `admissions.oversubscription_ratio`
- `admissions.first_preference_offer_rate`
- `admissions.any_preference_offer_rate`
- `admissions.cross_la_applications`
- `admissions.cross_la_offers`

Benchmark registration:

- `admissions_oversubscription_ratio`
- `admissions_first_preference_offer_rate`
- `admissions_any_preference_offer_rate`
- `admissions_cross_la_applications`

These metrics should flow through the existing `metric_benchmarks_yearly` materialization and benchmark cache path. This phase does not add admissions rows to the compare API or compare UI.

## Repository File Plan

Expected backend files:

- `apps/backend/src/civitas/domain/school_profiles/models.py`
- `apps/backend/src/civitas/domain/school_trends/models.py`
- `apps/backend/src/civitas/infrastructure/persistence/postgres_school_profile_repository.py`
- `apps/backend/src/civitas/infrastructure/persistence/cached_school_profile_repository.py`
- `apps/backend/src/civitas/infrastructure/persistence/postgres_school_trends_repository.py`
- `apps/backend/src/civitas/application/school_profiles/`
- `apps/backend/src/civitas/application/school_trends/`
- `apps/backend/src/civitas/api/schemas/school_profiles.py`
- `apps/backend/src/civitas/api/schemas/school_trends.py`
- `apps/backend/src/civitas/api/school_profile_presenter.py`
- `apps/backend/src/civitas/api/routes.py`
- `apps/backend/src/civitas/infrastructure/persistence/postgres_data_quality_repository.py`

Expected web files if admissions metrics are rendered in the existing profile and trends experience during this phase:

- `apps/web/src/api/types.ts`
- `apps/web/src/features/school-profile/metricCatalog.ts`
- `apps/web/src/features/school-profile/SchoolProfileFeature.tsx`
- `apps/web/src/features/school-profile/components/`

## Completeness Rules

1. Admissions coverage must be phase-aware because primary and secondary publication shapes can differ over time.
2. If a school has no matching admissions row for a year, surface explicit completeness rather than zero counts.
3. Do not derive subjective "hard to get into" labels; expose only raw and benchmarked metrics.
4. Profile and trends API shapes remain stable whether admissions data is present, absent, or unsupported for a year.

## Acceptance Criteria

1. Admissions metrics appear in profile and trends for matched schools.
2. Benchmark materialization includes admissions metrics using current cache behavior.
3. Missing-year admissions data is handled explicitly and consistently across API payloads.
4. Profile and trends API schemas remain shape-stable across schools and years with different admissions coverage.
