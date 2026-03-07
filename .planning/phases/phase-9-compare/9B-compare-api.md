# 9B - Compare API

## Goal

Implement a backend compare endpoint that returns aligned rows for up to four schools using the existing Gold serving model.

## Endpoint

- `GET /api/v1/schools/compare?urns=<urn1>,<urn2>,...`

## Request Validation

- Accept one comma-separated `urns` query parameter.
- Trim whitespace around each URN before validation.
- Reject requests with fewer than two URNs or more than four URNs with `400 Bad Request`.
- Reject duplicate URNs with `400 Bad Request`.
- If any requested URN is unknown, fail the whole request with `404 Not Found` and identify the missing URN values in the error detail.
- If the compare serving layer cannot be read, return `503 Service Unavailable`.

## Backend Shape

- Add a dedicated compare feature module in backend domain, application, infrastructure, and API layers.
- Reuse existing profile and trends repositories where practical, but keep compare-specific row assembly in a dedicated use case.
- Keep compare-specific row assembly and missing-data mapping in the compare use case, not in `routes.py`.
- If compare becomes query-heavy, add a compare-specific infrastructure adapter behind an application port rather than pushing SQL into the API layer.

## Response Requirements

- Return schools in request order.
- Return sections in the order frozen by `9A`.
- Return rows in the exact metric order frozen by `9A`.
- Include one school header object per requested URN and one aligned cell per requested URN on every returned row.
- Include per-cell availability metadata, year labels, and benchmark context where the underlying serving layer already provides it.
- Do not include `distance_miles` in the backend compare response. That value belongs to client-side selection context from search routes.

## OpenAPI Shape

Define the compare response using dedicated transport schemas:

- `SchoolCompareResponse`
- `SchoolCompareSchoolResponse`
- `SchoolCompareSectionResponse`
- `SchoolCompareRowResponse`
- `SchoolCompareCellResponse`
- `SchoolCompareBenchmarkResponse`

The response should follow this shape:

```json
{
  "schools": [
    {
      "urn": "100001",
      "name": "Example School",
      "postcode": "SW1A 1AA",
      "phase": "Primary",
      "type": "Community school",
      "age_range_label": "Ages 4-11"
    }
  ],
  "sections": [
    {
      "key": "inspection",
      "label": "Inspection",
      "rows": [
        {
          "metric_key": "ofsted_overall_effectiveness",
          "label": "Latest Ofsted",
          "unit": "text",
          "cells": [
            {
              "urn": "100001",
              "value_text": "Good",
              "value_numeric": null,
              "year_label": null,
              "snapshot_date": "2025-10-10",
              "availability": "available",
              "completeness_status": "available",
              "completeness_reason_code": null,
              "benchmark": null
            }
          ]
        }
      ]
    }
  ]
}
```

## Field Rules

- `unit` must use one of: `text`, `date`, `days`, `years`, `percent`, `count`, `rate`, `ratio`, `score`, `currency`, `decile`.
- `value_text` is always the display-ready value shown by the web UI.
- `value_numeric` is populated only for numeric metrics and should remain `null` for text and date rows.
- `year_label` is used for academic-year metrics.
- `snapshot_date` is used for point-in-time rows such as inspections.
- `benchmark` is `null` when no existing Gold benchmark context is available for that metric.
- `benchmark` should expose the current metric year together with school, national, and local values plus delta metadata already used on profile and trends surfaces.

## Assembly Rules

- Each returned row must contain exactly one cell per requested school in request order.
- Mixed-phase compare sets should use the union of applicable performance rows from `9A`.
- If a visible row does not apply to a given selected school, mark that cell `unsupported`.
- Omit a row only when every requested school would be `unsupported`.
- Reuse existing profile and trends completeness semantics when populating `completeness_status` and `completeness_reason_code`.

## Testing Requirements

- unit tests for compare row assembly and missing-data rules
- integration tests for repository queries
- API tests for request validation and response shape
- contract sync for generated frontend types

## Acceptance Criteria

- Compare endpoint is implemented and typed in OpenAPI.
- Row ordering and missing-data behavior are deterministic.
- API rejects invalid compare requests with clear validation errors.
