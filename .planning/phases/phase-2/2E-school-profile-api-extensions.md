# Phase 2E Design - School Profile API Extensions (Timeline + Area Context)

## Document Control

- Status: Implemented
- Last updated: 2026-03-02
- Depends on:
  - `.planning/phases/phase-2/2B-ofsted-timeline-pipeline.md`
  - `.planning/phases/phase-2/2C-ons-imd-pipeline.md`
  - `.planning/phases/phase-2/2D-police-crime-context-pipeline.md`
  - `.planning/phases/phase-1/1D-school-profile-api.md`
  - `docs/architecture/backend-conventions.md`
  - `docs/architecture/boundaries.md`

## Objective

Extend the existing school profile endpoint to include:

1. Ofsted inspection timeline events.
2. Area deprivation context.
3. Area crime summary context.

## Scope

### In scope

- Extend `GET /api/v1/schools/{urn}` response contract.
- Application/use-case and port changes for timeline + area context composition.
- Infrastructure repository extensions to query new Phase 2 Gold tables.
- Explicit partial-data and coverage metadata behavior.

### Out of scope

- New standalone endpoints for timeline or area context.
- Compare API behavior (Phase 3).
- Entitlement/paywall behavior (Phase 4).

## Contract

### Request

`GET /api/v1/schools/{urn}`

### Response (shape extension)

```json
{
  "school": {},
  "demographics_latest": {},
  "ofsted_latest": {},
  "ofsted_timeline": {
    "events": [
      {
        "inspection_number": "10426709",
        "inspection_start_date": "2025-11-11",
        "publication_date": "2026-01-11",
        "inspection_type": "S5 Inspection",
        "overall_effectiveness_label": null,
        "headline_outcome_text": "Strong standard",
        "category_of_concern": null
      }
    ],
    "coverage": {
      "is_partial_history": false,
      "earliest_event_date": "2015-09-14",
      "latest_event_date": "2026-01-15",
      "events_count": 9
    }
  },
  "area_context": {
    "deprivation": {
      "lsoa_code": "E01004736",
      "imd_decile": 3,
      "idaci_score": 0.241,
      "idaci_decile": 2,
      "source_release": "IoD2025"
    },
    "crime": {
      "radius_miles": 1.0,
      "latest_month": "2026-01",
      "total_incidents": 486,
      "categories": [
        {
          "category": "violent-crime",
          "incident_count": 132
        }
      ]
    },
    "coverage": {
      "has_deprivation": true,
      "has_crime": true,
      "crime_months_available": 12
    }
  }
}
```

### Errors

- `404`: school URN not found.
- `503`: dependent datastore unavailable.

## Decisions

1. Extend existing profile endpoint instead of introducing additional profile sub-endpoints.
2. Keep Phase 1 response fields backward compatible; Phase 2 adds optional sections only.
3. Timeline events are sorted descending by `inspection_start_date`.
4. Area deprivation uses verified IDACI fields as child-poverty context proxy.
5. Missing context data is represented explicitly via `coverage` flags and nullable sections.
6. Crime summary defaults to latest available month while preserving category breakdown.
7. Timeline coverage is marked `is_partial_history=true` when no events exist or earliest event is after the verified historical baseline date (`2015-09-14`).
8. Current deprivation join path uses cached postcode LSOA name (`postcode_cache.lsoa`) matched to `area_deprivation.lsoa_name` because cached LSOA code storage is not yet available in Phase 2E.

## Implementation Progress (2026-03-02)

- Completed: extended school profile domain/application models for Phase 2 sections:
  - `apps/backend/src/civitas/domain/school_profiles/models.py`
  - `apps/backend/src/civitas/application/school_profiles/{dto.py,use_cases.py}`
- Completed: extended Postgres profile repository composition:
  - `apps/backend/src/civitas/infrastructure/persistence/postgres_school_profile_repository.py`
  - added timeline query (`ofsted_inspections`), deprivation lookup (`postcode_cache` -> `area_deprivation`), and latest-month crime summary (`area_crime_context`).
- Completed: extended API wire schemas and route mapping:
  - `apps/backend/src/civitas/api/schemas/school_profiles.py`
  - `apps/backend/src/civitas/api/routes.py`
- Completed: extended backend tests:
  - `apps/backend/tests/unit/test_get_school_profile_use_case.py`
  - `apps/backend/tests/integration/test_school_profile_repository.py`
  - `apps/backend/tests/integration/test_school_profile_api.py`
- Completed: synced contracts and regenerated frontend API types:
  - `uv run --project apps/backend python tools/scripts/export_openapi.py`
  - `cd apps/web && npm run generate:types`
- Completed: revalidated repository quality gates after 2E implementation:
  - `make lint`
  - `make test`

## Application And Infrastructure Design

### Ports (application layer)

- Extend profile data port surface to include:
  - timeline events by `urn`,
  - deprivation context by school LSOA,
  - crime context by school `urn`.

### Use case

- Extend `GetSchoolProfileUseCase` to orchestrate:
  - school core + Phase 1 profile data,
  - timeline query from `ofsted_inspections`,
  - deprivation query from `area_deprivation`,
  - crime summary query from `area_crime_context`,
  - unified coverage metadata assembly.

### Infrastructure adapters

- Extend Postgres profile repository adapter(s) to query:
  - `ofsted_inspections`,
  - `area_deprivation`,
  - `area_crime_context`.

## File-Oriented Implementation Plan

1. `apps/backend/src/civitas/domain/school_profiles/models.py`
   - add timeline and area-context value objects.
2. `apps/backend/src/civitas/application/school_profiles/dto.py`
   - extend response DTO with Phase 2 sections.
3. `apps/backend/src/civitas/application/school_profiles/use_cases.py`
   - compose timeline + area context.
4. `apps/backend/src/civitas/application/school_profiles/ports/school_profile_repository.py`
   - extend repository contract.
5. `apps/backend/src/civitas/infrastructure/persistence/postgres_school_profile_repository.py`
   - add Phase 2 Gold-table queries.
6. `apps/backend/src/civitas/api/schemas/school_profiles.py`
   - extend wire schema.
7. `apps/backend/tests/unit/test_get_school_profile_use_case.py`
   - add timeline + area context behavior coverage.
8. `apps/backend/tests/integration/test_school_profile_repository.py`
   - add Phase 2 repository query coverage.
9. `apps/backend/tests/integration/test_school_profile_api.py`
   - add contract assertions for new fields and partial-data scenarios.

## Testing And Quality Gates

### Required tests

- timeline event ordering and shape coverage.
- area deprivation mapping coverage (including null/missing mapping).
- crime summary aggregation contract coverage.
- explicit partial-history and partial-context response coverage.

### Contract sync

After endpoint schema extension:

1. `uv run --project apps/backend python tools/scripts/export_openapi.py`
2. `cd apps/web && npm run generate:types`

### Required gates

- `make lint`
- `make test`

## Acceptance Criteria

1. `GET /api/v1/schools/{urn}` includes Ofsted timeline and area context sections.
2. Existing Phase 1 contract fields remain stable.
3. Missing/partial context is explicit and deterministic.
4. OpenAPI reflects the extended profile contract and web types regenerate cleanly.

## Risks And Mitigations

- Risk: endpoint payload growth affects profile latency.
  - Mitigation: bounded query shapes, indexed access paths, and compact timeline fields.
- Risk: inconsistent joins cause null-heavy area context.
  - Mitigation: explicit join-key handling and coverage metadata.
- Risk: regression in existing Phase 1 profile consumers.
  - Mitigation: backward-compatible schema extension and contract tests.
