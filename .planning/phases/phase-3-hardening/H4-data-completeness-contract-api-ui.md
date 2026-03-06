# Phase 3 / H4 Design - Data Completeness Contract Across API And UI

## Document Control

- Status: Implemented
- Last updated: 2026-03-03
- Depends on:
 - `.planning/phases/phase-3-hardening/H3-historical-demographics-backfill-lookback.md`
  - `.planning/phases/phase-2/2E-school-profile-api-extensions.md`
  - `.planning/phases/phase-2/2F-web-profile-area-context-enhancements.md`
  - `docs/architecture/backend-conventions.md`
  - `docs/architecture/frontend-conventions.md`

## Objective

Expose section-level completeness explicitly in API and UI so parents can understand whether data is missing at source, unavailable by design, or temporarily incomplete.

## Tracking Update (2026-03-03, implementation checkpoint)

- Implemented section-level completeness contracts for profile and trends APIs with status, reason code, last-updated timestamp, and optional years-available metadata.
- Implemented repository-level completeness derivation in:
  - `apps/backend/src/civitas/infrastructure/persistence/postgres_school_profile_repository.py`
  - `apps/backend/src/civitas/infrastructure/persistence/postgres_school_trends_repository.py`
- Wired completeness DTO/schema flow through:
  - `apps/backend/src/civitas/application/school_profiles/*`
  - `apps/backend/src/civitas/application/school_trends/*`
  - `apps/backend/src/civitas/api/schemas/*`
  - `apps/backend/src/civitas/api/routes.py`
- Implemented school-profile UI completeness rendering with section shells and top-level summary via:
  - `apps/web/src/features/school-profile/mappers/profileMapper.ts`
  - `apps/web/src/features/school-profile/components/SectionCompletenessNotice.tsx`
  - `apps/web/src/features/school-profile/SchoolProfileFeature.tsx`
- Regenerated web API types from backend OpenAPI and validated required quality gates.

## Scope

### In scope

- Extend profile and trends responses with machine-readable completeness metadata.
- Add reason codes and freshness fields per section.
- Render clear user-friendly section states in web profile UI.
- Ensure core sections render even when data is unavailable.

### Out of scope

- New premium gating behavior.
- New data-source acquisition.

## Completeness Contract

Per section (`demographics`, `trends`, `ofsted_latest`, `ofsted_timeline`, `area_deprivation`, `area_crime`):

- `status`: `available | partial | unavailable`
- `reason_code`:
  - `source_missing`
  - `source_not_provided`
  - `rejected_by_validation`
  - `not_joined_yet`
  - `pipeline_failed_recently`
  - `not_applicable`
- `last_updated_at`: ISO timestamp or null
- `years_available`: optional for trend-capable sections

## UI Messaging Policy

1. No pipeline jargon in user-facing copy.
2. Message hierarchy:
   - what is available now,
   - what is missing,
   - why it is missing (plain language),
   - when data was last refreshed.
3. Do not hide major sections when unavailable; show section shell with explicit state.

## File-Oriented Implementation Plan

1. `apps/backend/src/civitas/application/school_profiles/dto.py`
   - add completeness DTOs.
2. `apps/backend/src/civitas/application/school_trends/dto.py`
   - add trends completeness metadata.
3. `apps/backend/src/civitas/api/schemas/school_profiles.py`
   - extend OpenAPI contract with completeness block.
4. `apps/backend/src/civitas/api/schemas/school_trends.py`
   - extend trends response schema.
5. `apps/backend/src/civitas/infrastructure/persistence/postgres_school_profile_repository.py`
   - compute per-section completeness status/reason from serving data and run telemetry.
6. `apps/backend/src/civitas/infrastructure/persistence/postgres_school_trends_repository.py`
   - return trend completeness context.
7. `apps/web/src/features/school-profile/types.ts`
   - add completeness VM types.
8. `apps/web/src/features/school-profile/mappers/profileMapper.ts`
   - map reason codes to parent-facing copy keys.
9. `apps/web/src/features/school-profile/components/`:
   - add `SectionCompletenessNotice` component.
   - update existing cards to render unavailable/partial shells.
10. `apps/web/src/features/school-profile/SchoolProfileFeature.tsx`
    - add top-level completeness summary near page header.

## Testing And Quality Gates

### Required tests

- API contract includes completeness metadata for all sections.
- reason codes map correctly from backend to UI message keys.
- core section cards render in unavailable state instead of disappearing.
- trend warnings distinguish 0-year vs 1-year vs multi-year partial history.

### Required gates

- `uv run --project apps/backend pytest apps/backend/tests/integration/test_school_profile_api.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/integration/test_school_trends_api.py -q`
- `cd apps/web && npm run test -- school-profile`
- `cd apps/web && npm run lint`
- `cd apps/web && npm run typecheck`
- `make lint`
- `make test`

## Acceptance Criteria

1. API responses expose explicit section-level completeness metadata.
2. Profile page communicates missing data clearly and consistently for end users.
3. Sparse pages (for example schools with minimal data) are understandable without technical interpretation.
4. Existing profile functionality remains backward compatible for consumers of existing fields.

## Risks And Mitigations

- Risk: API payload bloat.
  - Mitigation: compact completeness schema and section-level only.
- Risk: copy becomes inconsistent across components.
  - Mitigation: centralized message mapping and shared UI component.
