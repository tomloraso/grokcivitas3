# Phase 1H Design - Phase 1 Quality Gates And Sign-Off

## Document Control

- Status: Draft
- Last updated: 2026-03-02
- Depends on:
  - `.planning/phases/phase-1/1A-source-contract-gate.md`
  - `.planning/phases/phase-1/1B-dfe-characteristics-pipeline.md`
  - `.planning/phases/phase-1/1C-ofsted-latest-pipeline.md`
  - `.planning/phases/phase-1/1D-school-profile-api.md`
  - `.planning/phases/phase-1/1E-school-trends-api.md`
  - `.planning/phases/phase-1/1F-web-routing-navigation-foundation.md`
  - `.planning/phases/phase-1/1F1-web-component-expansion-data-viz-baseline.md`
  - `.planning/phases/phase-1/1G-web-school-profile-page.md`
  - `.agents/tooling.md`
  - `.agents/testing.md`

## Objective

Define the mandatory verification gates and sign-off checklist for Phase 1 completion.

## Quality Gates (Mandatory)

## Gate 0 - Source Contract Gate

- Run source verification checks before source-dependent implementation.
- Must pass `1A` criteria (callable endpoints, required fields, fallback path).

Required command target:

- `uv run --project apps/backend python tools/scripts/verify_phase1_sources.py`

## Gate 1 - Backend Unit And Integration

Minimum required backend coverage:

- DfE characteristics transform + pipeline tests.
- Ofsted latest transform + pipeline tests.
- Profile and trends use-case tests.
- Profile and trends API contract tests.
- Import boundary tests.

Required commands:

- `uv run --project apps/backend pytest`
- `uv run --project apps/backend pytest apps/backend/tests/unit/test_import_boundaries.py -q`

## Gate 2 - Contract Sync

OpenAPI and frontend generated types must be in sync after backend API changes.

Required commands:

1. `uv run --project apps/backend python tools/scripts/export_openapi.py`
2. `cd apps/web && npm run generate:types`

## Gate 3 - Web Quality

Minimum required web coverage:

- route behavior tests (`/` and `/schools/:urn`),
- site chrome tests (header, footer, mobile nav, breadcrumbs, skip-to-content, 404),
- expanded UI primitive tests (Badge, Tabs, Tooltip, Toast),
- data component tests (StatCard, TrendIndicator, RatingBadge, Sparkline, MetricGrid, MetricUnavailable),
- profile loading/success/error/sparse-history states,
- search -> profile navigation e2e smoke.

Required commands:

- `cd apps/web && npm run lint`
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run test`
- `cd apps/web && npm run build`
- `cd apps/web && npm run budget:check`

## Gate 4 - Repository Golden Path

Final repository gates from repo root:

- `make lint`
- `make test`

## Acceptance Checklist

1. Source contract gate passed and evidence committed in Phase 1 planning artefacts.
2. Phase 1 pipelines are rerunnable and idempotent.
3. `GET /api/v1/schools/{urn}` and `GET /api/v1/schools/{urn}/trends` are implemented and tested.
4. OpenAPI contract is current and consumed by generated frontend types.
5. Web route navigation from search to profile is functional and test-covered.
6. Site chrome (header, footer, mobile nav, breadcrumbs, skip-to-content, 404) is functional, accessible, and test-covered.
7. Expanded shared components (1F1) are available, token-integrated, and tested.
8. Unsupported metrics are represented as explicit coverage gaps, not silently omitted.
9. All mandatory commands above pass.

## Exit Criteria

Phase 1 is complete only when all gates pass in one consistent state and the profile journey is demoable end-to-end from postcode search to school profile.

## Risks And Mitigations

- Risk: teams bypass source gate under delivery pressure.
  - Mitigation: Gate 0 is blocking and listed first in closeout checklist.
- Risk: API/web contract drift late in phase.
  - Mitigation: explicit contract sync gate with required commands.
- Risk: sparse-history trends are misinterpreted as defects.
  - Mitigation: required sparse-history test coverage and explicit response metadata.
