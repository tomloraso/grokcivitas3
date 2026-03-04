# Phase S4 Design - Completeness Contract And Parent-Facing Copy

## Document Control

- Status: Complete
- Last updated: 2026-03-04
- Depends on:
  - `.planning/phases/phase-source-stabilization/S3-multi-source-normalization-and-gold-upsert.md`
  - `.planning/phases/phase-hardening/H4-data-completeness-contract-api-ui.md`
  - `docs/architecture/frontend-conventions.md`

## Objective

Align trends/profile completeness semantics with source reality and ensure user-facing copy is clear, factual, and non-technical.

## In scope

- Reason-code updates for demographics/trends completeness.
- API contract updates and mapper alignment.
- Parent-facing copy for sparse/partial history states.
- UI suppression logic for `<2` years with explicit explanation.

## Out of scope

- New chart types.
- New premium gating behavior.

## Completeness reason code additions

1. `insufficient_years_published`
2. `source_not_in_catalog`
3. `source_file_missing_for_year`
4. `source_schema_incompatible_for_year`
5. `partial_metric_coverage`

## Message guidelines

1. Use plain language:
   - "We currently have one published year for this school."
2. Avoid internal phrasing:
   - no "pipeline", "join", or "stage" wording in parent-facing text.
3. Keep deterministic behavior:
   - `<2 years` -> suppress trend delta arrows and show explanation.

## File-oriented implementation plan

1. `apps/backend/src/civitas/api/schemas/school_profiles.py`
2. `apps/backend/src/civitas/api/schemas/school_trends.py`
3. `apps/backend/src/civitas/application/school_trends/use_cases.py`
4. `apps/web/src/features/school-profile/mappers/profileMapper.ts`
5. `apps/web/src/features/school-profile/components/PageCompletenessBar.tsx`
6. `apps/web/src/shared/glossary.ts`
7. `apps/web/src/features/school-profile/components/*` (trend/copy surfaces)
8. `apps/backend/tests/integration/test_school_trends_api.py`
9. `apps/web/src/features/school-profile/*.test.tsx`

## Codex execution checklist

1. Extend backend reason-code enums first.
2. Export OpenAPI and regenerate web types immediately after backend schema changes.
3. Update mapper/UI copy and tests in same PR.
4. Verify no parent-facing string contains internal implementation terms.

## Required commands

1. `uv run --project apps/backend python tools/scripts/export_openapi.py`
2. `cd apps/web && npm run generate:types`
3. `uv run --project apps/backend pytest apps/backend/tests/integration/test_school_trends_api.py apps/backend/tests/integration/test_school_profile_api.py -q`
4. `cd apps/web && npm run test -- school-profile`
5. `cd apps/web && npm run lint`
6. `cd apps/web && npm run typecheck`

## Acceptance criteria

1. API exposes source-aware reason codes for sparse/partial trends.
2. UI shows clear parent-facing explanations for `<2` year history.
3. Contract and mapper changes remain synchronized and test-covered.

## Implementation tracking (2026-03-04)

- [x] Extended backend completeness reason-code unions in domain/application/api layers.
- [x] Updated trends completeness logic for:
  - `insufficient_years_published`
  - `source_file_missing_for_year`
  - `partial_metric_coverage`
- [x] Updated demographics completeness reasoning in profile repository to use `partial_metric_coverage` and `source_file_missing_for_year`.
- [x] Regenerated API contract artifacts:
  - `apps/web/src/api/openapi.json`
  - `apps/web/src/api/generated-types.ts`
- [x] Updated web mapper/types and parent-facing copy surfaces:
  - `apps/web/src/features/school-profile/types.ts`
  - `apps/web/src/features/school-profile/mappers/profileMapper.ts`
  - `apps/web/src/features/school-profile/components/SectionCompletenessNotice.tsx`
  - `apps/web/src/features/school-profile/components/TrendPanel.tsx`
- [x] Updated backend and web tests for new reason codes and `<2`-year trend explanation behavior.
