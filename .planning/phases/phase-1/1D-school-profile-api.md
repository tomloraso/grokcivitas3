# Phase 1D Design - School Profile API

## Document Control

- Status: Implemented
- Last updated: 2026-03-02
- Depends on:
  - `.planning/phases/phase-1/1B-dfe-characteristics-pipeline.md`
  - `.planning/phases/phase-1/1C-ofsted-latest-pipeline.md`
  - `docs/architecture/backend-conventions.md`
  - `docs/architecture/boundaries.md`

## Objective

Expose a school profile endpoint that returns core school details plus latest demographics snapshot and latest Ofsted headline.

## Scope

### In scope

- `GET /api/v1/schools/{urn}` route and schema.
- Application use case and ports for profile composition.
- Infrastructure repository adapter(s) to read from Gold tables.
- Explicit source coverage flags for metrics unavailable from validated source.

### Out of scope

- Trends endpoint (`1E`).
- Compare features (Phase 3).
- Paywall behavior (Phase 4).

## Contract

### Request

`GET /api/v1/schools/{urn}`

Path params:

- `urn` (required; school URN)

### Response (shape)

```json
{
  "school": {
    "urn": "123456",
    "name": "Example School",
    "phase": "Primary",
    "type": "Academy",
    "status": "Open",
    "postcode": "SW1A 1AA",
    "lat": 51.5010,
    "lng": -0.1416
  },
  "demographics_latest": {
    "academic_year": "2024/25",
    "disadvantaged_pct": 17.2,
    "fsm_pct": null,
    "sen_pct": 13.0,
    "ehcp_pct": 2.1,
    "eal_pct": 8.4,
    "first_language_english_pct": 90.6,
    "first_language_unclassified_pct": 1.0,
    "coverage": {
      "fsm_supported": false,
      "ethnicity_supported": false,
      "top_languages_supported": false
    }
  },
  "ofsted_latest": {
    "overall_effectiveness_code": "2",
    "overall_effectiveness_label": "Good",
    "inspection_start_date": "2025-10-10",
    "publication_date": "2025-11-15",
    "is_graded": true,
    "ungraded_outcome": null
  }
}
```

### Errors

- `404`: school URN not found.
- `503`: dependent data store/service unavailable.

## Application And Infrastructure Design

### Ports (application layer)

- `SchoolProfileRepository`
  - `get_school_profile(urn: str) -> SchoolProfile | None`

### Use case

- `GetSchoolProfileUseCase`
  - validate URN format,
  - fetch school core row,
  - fetch latest demographics row,
  - fetch latest Ofsted row,
  - build response DTO with coverage flags.

### Infrastructure adapters

- Postgres profile repository joining:
  - `schools`
  - latest row from `school_demographics_yearly`
  - `school_ofsted_latest`

## Decisions

1. API returns `null` for unsupported metrics and exposes `coverage` flags.
2. No UI-facing metric is synthesized from unavailable source fields.
3. Endpoint remains stable even when demographics or Ofsted is partially missing:
   - school core remains primary,
   - child sections may be `null`.
4. Mapping ownership follows backend conventions:
   - infrastructure -> domain/application types,
   - API layer -> wire schema.

## Implementation Progress (2026-03-02)

- Completed: added school profile domain/application layers:
  - `apps/backend/src/civitas/domain/school_profiles/models.py`
  - `apps/backend/src/civitas/application/school_profiles/{dto.py,use_cases.py,errors.py}`
  - `apps/backend/src/civitas/application/school_profiles/ports/school_profile_repository.py`
- Completed: added Postgres repository adapter:
  - `apps/backend/src/civitas/infrastructure/persistence/postgres_school_profile_repository.py`
  - joins `schools` + latest `school_demographics_yearly` row + `school_ofsted_latest`.
- Completed: added API schema + route + dependency wiring for `GET /api/v1/schools/{urn}`:
  - `apps/backend/src/civitas/api/schemas/school_profiles.py`
  - `apps/backend/src/civitas/api/{dependencies.py,routes.py}`
  - `apps/backend/src/civitas/bootstrap/container.py`
- Completed: added test coverage:
  - unit: `apps/backend/tests/unit/test_get_school_profile_use_case.py`
  - API contract: `apps/backend/tests/integration/test_school_profile_api.py`
  - repository integration: `apps/backend/tests/integration/test_school_profile_repository.py`

## File-Oriented Implementation Plan

1. `apps/backend/src/civitas/domain/school_profiles/models.py` (new)
   - profile aggregate/value objects.
2. `apps/backend/src/civitas/application/school_profiles/ports/school_profile_repository.py` (new)
3. `apps/backend/src/civitas/application/school_profiles/dto.py` (new)
4. `apps/backend/src/civitas/application/school_profiles/use_cases.py` (new)
5. `apps/backend/src/civitas/infrastructure/persistence/postgres_school_profile_repository.py` (new)
6. `apps/backend/src/civitas/api/schemas/school_profiles.py` (new)
7. `apps/backend/src/civitas/api/routes.py`
   - add `GET /api/v1/schools/{urn}` route.
8. `apps/backend/src/civitas/api/dependencies.py`
   - provide profile use case dependency.
9. `apps/backend/src/civitas/bootstrap/container.py`
   - wire profile repository and use case.

## Testing And Quality Gates

### Required tests

- `apps/backend/tests/unit/test_get_school_profile_use_case.py`
  - found/not-found behavior,
  - coverage flag behavior,
  - null subsection behavior.
- `apps/backend/tests/integration/test_school_profile_api.py`
  - contract response for success and 404.
- boundary tests remain green (`test_import_boundaries.py`).

### Contract sync

After endpoint implementation:

1. `uv run --project apps/backend python tools/scripts/export_openapi.py`
2. `cd apps/web && npm run generate:types`

### Required gates

- `make lint`
- `make test`

## Acceptance Criteria

1. `GET /api/v1/schools/{urn}` returns school core data plus latest demographics and Ofsted headline.
2. Unsupported metrics are explicit via `null` plus `coverage` flags.
3. Route, use case, and repository follow architecture boundary rules.
4. OpenAPI reflects the new profile contract.

## Risks And Mitigations

- Risk: contract instability while source coverage evolves.
  - Mitigation: stable wire shape with explicit coverage metadata.
- Risk: accidental transport leakage into application/domain layers.
  - Mitigation: strict port/DTO boundaries and import tests.
