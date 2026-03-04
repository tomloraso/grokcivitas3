# Phase 2G Design - Phase 2 Quality Gates And Sign-Off

## Document Control

- Status: Implemented
- Last updated: 2026-03-02
- Depends on:
  - `.planning/phases/phase-2/2A-source-contract-gate.md`
  - `.planning/phases/phase-2/2B-ofsted-timeline-pipeline.md`
  - `.planning/phases/phase-2/2C-ons-imd-pipeline.md`
  - `.planning/phases/phase-2/2D-police-crime-context-pipeline.md`
  - `.planning/phases/phase-2/2E-school-profile-api-extensions.md`
  - `.planning/phases/phase-2/2F-web-profile-area-context-enhancements.md`
  - `.agents/tooling.md`
  - `.agents/testing.md`

## Tracking Update (2026-03-02)

- Final gate verification status:
  - Gate 0 source contract verification: passed (`2A` evidence previously captured with `verify_phase2_sources.py`).
  - Gate 1 backend verification: passed (`make test` includes full backend unit + integration suite).
  - Gate 2 contract sync: passed (completed during `2E`; no subsequent contract schema deltas in `2F`).
  - Gate 3 web quality:
    - `cd apps/web && npm run lint` -> pass
    - `cd apps/web && npm run typecheck` -> pass
    - `cd apps/web && npm run test` -> pass
    - `cd apps/web && npm run build` -> pass
    - `cd apps/web && npm run budget:check` -> pass (`Lazy map chunk JS (gzip): 231.5 KiB` vs budget `300.0 KiB`)
    - `cd apps/web && npm run test:e2e` -> pass (`9 passed`)
  - Gate 4 repository golden path:
    - `make lint` -> pass
    - `make test` -> pass
- Result: all mandatory Phase 2 gates are green in one repository state.

## Objective

Define mandatory verification gates and sign-off criteria for Phase 2 completion.

## Quality Gates (Mandatory)

## Gate 0 - Source Contract Gate

- Run Phase 2 source verification checks before source-dependent implementation.
- Must pass `2A` criteria (callable endpoints, required fields, fallback path).

Required command target:

- `uv run --project apps/backend python tools/scripts/verify_phase2_sources.py`

## Gate 1 - Backend Unit And Integration

Minimum required backend coverage:

- Ofsted timeline transforms + pipeline integration.
- ONS IMD transforms + pipeline integration.
- Police crime context transforms + pipeline integration.
- Extended school profile use case + repository + API contract tests.
- Import boundary tests remain green.

Required commands:

- `uv run --project apps/backend pytest`
- `uv run --project apps/backend pytest apps/backend/tests/unit/test_import_boundaries.py -q`

## Gate 2 - Contract Sync

OpenAPI and frontend generated types must remain in sync after backend profile schema changes.

Required commands:

1. `uv run --project apps/backend python tools/scripts/export_openapi.py`
2. `cd apps/web && npm run generate:types`

## Gate 3 - Web Quality

Minimum required web coverage:

- profile timeline rendering states,
- area deprivation and area crime context rendering states,
- partial-data and unavailable-data coverage behavior,
- search -> profile E2E journey including Phase 2 sections.

Required commands:

- `cd apps/web && npm run lint`
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run test`
- `cd apps/web && npm run build`
- `cd apps/web && npm run budget:check`
- `cd apps/web && npm run test:e2e`

## Gate 4 - Repository Golden Path

Final repository gates from repo root:

- `make lint`
- `make test`

## Acceptance Checklist

1. Source contract gate passed and evidence committed in Phase 2 planning artifacts.
2. Phase 2 pipelines are rerunnable and idempotent.
3. `ofsted_inspections`, `area_deprivation`, and `area_crime_context` are implemented and tested.
4. Extended `GET /api/v1/schools/{urn}` contract is implemented, tested, and synced to OpenAPI/web types.
5. Profile web route presents timeline + area context with explicit partial-data handling.
6. All mandatory commands pass in one consistent repository state.

## Exit Criteria

Phase 2 is complete only when all gates pass and the profile journey is demoable end-to-end with:

- latest Ofsted headline,
- Ofsted timeline history,
- area deprivation context,
- area crime summary context.

## Sign-Off

- Phase 2 quality gate sign-off completed on 2026-03-02.
- The profile journey is verified end-to-end from search to profile with Ofsted timeline and area context sections rendered and tested.

## Risks And Mitigations

- Risk: source drift invalidates planned mappings mid-implementation.
  - Mitigation: blocking source gate and executable verification script.
- Risk: API/web contract drift while adding profile fields.
  - Mitigation: explicit contract sync gate and generated-type regeneration.
- Risk: large police monthly archives create unstable processing behavior.
  - Mitigation: dedicated pipeline tests around archive ingestion and deterministic aggregation.
