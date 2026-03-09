# Phase 17 / 17C Design - Serving Contract And Benchmark Integration

## Document Control

- Status: Planned
- Last updated: 2026-03-09
- Depends on:
  - `.planning/phases/phase-17-school-admissions/17B-admissions-pipeline-and-gold-schema.md`

## Objective

Expose admissions demand and offer signals through the existing Civitas serving layer.

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

## Repository File Plan

Expected backend files:

- `apps/backend/src/civitas/infrastructure/persistence/postgres_school_profile_repository.py`
- `apps/backend/src/civitas/infrastructure/persistence/cached_school_profile_repository.py`
- `apps/backend/src/civitas/infrastructure/persistence/postgres_school_trends_repository.py`
- `apps/backend/src/civitas/application/school_profiles/`
- `apps/backend/src/civitas/application/school_trends/`

## Completeness Rules

1. Admissions coverage must be phase-aware because primary and secondary publication shapes can differ over time.
2. If a school has no matching admissions row for a year, surface explicit completeness rather than zero counts.
3. Do not derive subjective "hard to get into" labels; expose only raw and benchmarked metrics.

## Acceptance Criteria

1. Admissions metrics appear in profile and trends for matched schools.
2. Benchmark materialization includes admissions metrics using current cache behavior.
3. Missing-year admissions data is handled explicitly and consistently across API payloads.
