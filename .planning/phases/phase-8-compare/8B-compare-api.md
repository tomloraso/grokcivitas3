# 8B - Compare API

## Goal

Implement a backend compare endpoint that returns aligned rows for up to four schools using the existing Gold serving model.

## Endpoint

- `GET /api/v1/schools/compare?urns=<urn1>,<urn2>,...`

## Backend Shape

- Add a dedicated compare feature module in backend domain, application, infrastructure, and API layers.
- Reuse existing profile and trends repositories where practical, but keep compare-specific row assembly in a dedicated use case.
- Enforce a maximum of four URNs and reject duplicates or invalid inputs clearly.

## Response Requirements

- Return schools in request order.
- Return compare sections and rows in a deterministic order.
- Include school identity block plus aligned metric rows.
- Include per-cell availability metadata and year labels.
- Include benchmark context where the underlying serving layer already provides it.

## Testing Requirements

- unit tests for compare row assembly and missing-data rules
- integration tests for repository queries
- API tests for request validation and response shape
- contract sync for generated frontend types

## Acceptance Criteria

- Compare endpoint is implemented and typed in OpenAPI.
- Row ordering and missing-data behavior are deterministic.
- API rejects invalid compare requests with clear validation errors.
