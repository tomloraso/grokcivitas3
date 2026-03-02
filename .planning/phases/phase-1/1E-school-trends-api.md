# Phase 1E Design - School Trends API

## Document Control

- Status: Draft
- Last updated: 2026-03-02
- Depends on:
  - `.planning/phases/phase-1/1A-source-contract-gate.md`
  - `.planning/phases/phase-1/1B-dfe-characteristics-pipeline.md`
  - `docs/architecture/backend-conventions.md`

## Objective

Expose yearly metric series for a school with deterministic delta and direction behavior, including explicit handling for partial history.

## Scope

### In scope

- `GET /api/v1/schools/{urn}/trends` route and schema.
- Yearly series from `school_demographics_yearly`.
- Delta and direction computation when prior year exists.
- History-quality metadata in response.

### Out of scope

- Ofsted timeline (Phase 2).
- Cross-school comparison trends (Phase 3).

## Contract

### Request

`GET /api/v1/schools/{urn}/trends`

### Response (shape)

```json
{
  "urn": "123456",
  "years_available": ["2024/25"],
  "history_quality": {
    "is_partial_history": true,
    "min_years_for_delta": 2,
    "years_count": 1
  },
  "series": {
    "disadvantaged_pct": [
      {
        "academic_year": "2024/25",
        "value": 17.2,
        "delta": null,
        "direction": null
      }
    ],
    "sen_pct": [
      {
        "academic_year": "2024/25",
        "value": 13.0,
        "delta": null,
        "direction": null
      }
    ],
    "ehcp_pct": [
      {
        "academic_year": "2024/25",
        "value": 2.1,
        "delta": null,
        "direction": null
      }
    ],
    "eal_pct": [
      {
        "academic_year": "2024/25",
        "value": 8.4,
        "delta": null,
        "direction": null
      }
    ]
  }
}
```

### Errors

- `404`: school URN not found.

## Decisions

1. Trend endpoint never fabricates missing years.
2. `delta` and `direction` are computed only when prior year exists.
3. Direction thresholds:
   - `up` when `delta > 0`
   - `down` when `delta < 0`
   - `flat` when `delta == 0`
4. When fewer than 2 years exist, `delta` and `direction` are `null`.
5. Response always includes `history_quality` so UI can render sparse-history states intentionally.

## Trend Depth Gate (From 1A)

Before shipping sparkline/trend claims:

1. Verify years available per metric from validated source.
2. If <3 years for most schools:
   - keep endpoint enabled,
   - mark `is_partial_history=true`,
   - avoid UI copy implying multi-year depth.

## Application And Infrastructure Design

### Ports

- `SchoolTrendsRepository`
  - `get_demographics_series(urn: str) -> list[DemographicsYearlyRow]`

### Use case

- `GetSchoolTrendsUseCase`
  - fetch yearly rows ordered by year ascending,
  - compute per-metric series,
  - compute deltas and direction where possible,
  - return response DTO with history quality metadata.

### Infrastructure

- Postgres repository query:
  - select all rows from `school_demographics_yearly` by `urn`,
  - order by parsed academic year.

## File-Oriented Implementation Plan

1. `apps/backend/src/civitas/domain/school_trends/models.py` (new)
2. `apps/backend/src/civitas/application/school_trends/ports/school_trends_repository.py` (new)
3. `apps/backend/src/civitas/application/school_trends/dto.py` (new)
4. `apps/backend/src/civitas/application/school_trends/use_cases.py` (new)
5. `apps/backend/src/civitas/infrastructure/persistence/postgres_school_trends_repository.py` (new)
6. `apps/backend/src/civitas/api/schemas/school_trends.py` (new)
7. `apps/backend/src/civitas/api/routes.py`
   - add `GET /api/v1/schools/{urn}/trends`.
8. `apps/backend/src/civitas/api/dependencies.py`
   - provide trends use case dependency.
9. `apps/backend/src/civitas/bootstrap/container.py`
   - wire trends repository and use case.

## Testing And Quality Gates

### Required tests

- `apps/backend/tests/unit/test_get_school_trends_use_case.py`
  - delta and direction behavior,
  - partial history behavior.
- `apps/backend/tests/integration/test_school_trends_api.py`
  - response contract and 404 behavior.
- contract tests for deterministic year ordering.

### Contract sync

After endpoint implementation:

1. `uv run --project apps/backend python tools/scripts/export_openapi.py`
2. `cd apps/web && npm run generate:types`

### Required gates

- `make lint`
- `make test`

## Acceptance Criteria

1. `GET /api/v1/schools/{urn}/trends` returns deterministic yearly series for supported metrics.
2. Delta/direction behavior is deterministic and null-safe for sparse history.
3. Response includes explicit history-quality metadata.
4. Endpoint remains correct with 1-year, 2-year, and 3+ year data availability.

## Risks And Mitigations

- Risk: insufficient source history limits trend value in Phase 1.
  - Mitigation: explicit partial-history semantics and truthful UI rendering.
- Risk: inconsistent academic year ordering from source strings.
  - Mitigation: normalized year parsing in pipeline and repository ordering tests.
