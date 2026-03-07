# 9E - Compare Quality Gates

## Goal

Close Phase 9 with a single repo state that proves compare is stable across backend, web, and data-contract boundaries.

## Required Checks

- backend unit and integration tests for compare feature
- API contract export and frontend type generation (`cd apps/web && npm run generate:types`)
- frontend lint, typecheck, unit tests, and build
- compare end-to-end journey coverage
- repository `make lint`
- repository `make test`

## Acceptance Evidence

- compare endpoint returns deterministic row order
- compare page works from search and profile entry points
- missing-data states are user-readable and match API semantics
- no contract drift remains between backend schemas and frontend generated types

## Sign-Off Condition

Phase 9 is complete only when backend, web, and generated-contract evidence all pass in one repository state.
