# Phase S6 Design - School-Level Ethnicity Breakdown Support

## Document Control

- Status: Complete
- Last updated: 2026-03-04
- Depends on:
  - `.planning/phases/phase-source-stabilization/S3-multi-source-normalization-and-gold-upsert.md`
  - `.planning/phases/phase-source-stabilization/S4-completeness-contract-and-parent-facing-copy.md`
  - `.planning/phases/phase-source-stabilization/source-catalog-2026-03-04.md`

## Objective

Close the current `Ethnicity breakdown` coverage gap using already approved SPC school-level source files, without adding a new source family.

## In scope

- Add explicit ethnicity breakdown extraction from SPC school-level underlying files.
- Persist school-level yearly ethnicity metrics in Gold storage.
- Expose ethnicity breakdown in profile API contracts and web mapping.
- Flip `ethnicity_supported` based on real source coverage rather than hardcoded defaults.
- Keep completeness messaging aligned with metric availability.

## Out of scope

- `Top non-English languages` support (remains source-gap pending a school-level named-language dataset with URN).
- New ranking/scoring logic based on ethnicity.
- New compare-page features.

## Source Evidence Snapshot (2026-03-04)

1. Existing approved SPC school-level files (release slugs `2019-20` through `2024-25`) already include school-level URN and ethnicity percentage/count columns.
2. Example validated release/file:
   - Release: `school-pupils-and-their-characteristics/2024-25`
   - Release version id: `63491b17-2037-4533-b719-d3656aaf6ed5`
   - File id: `3dc88c32-da52-4aff-b6d0-0126de016844`
3. Ethnicity groups observed in headers include:
   - white British, Irish, traveller of Irish heritage, any other white, Gypsy/Roma
   - white and black Caribbean, white and black African, white and Asian, any other mixed
   - Indian, Pakistani, Bangladeshi, any other Asian
   - Caribbean, African, any other black
   - Chinese, any other ethnic group, unclassified
4. Current Civitas pipeline writes `has_ethnicity_data = FALSE` in promote for demographics sources, so UI shows `Coverage gaps: Ethnicity breakdown` despite source availability.

## Implementation Strategy

## Storage shape

1. Add a dedicated Gold table for ethnicity by school-year:
   - `school_ethnicity_yearly`
   - key: `(urn, academic_year)`
   - explicit typed percentage columns per ethnicity group (plus unclassified)
   - optional count columns where useful for future UX
   - provenance columns (`source_dataset_id`, `source_dataset_version`, `updated_at`)
2. Keep `school_demographics_yearly` as the summary table; avoid widening it with 30+ new columns.
3. Update demographics coverage derivation:
   - `ethnicity_supported = TRUE` when a school-year has at least one valid ethnicity value in `school_ethnicity_yearly`.

## Pipeline and contracts

1. Extend `demographics_spc` contract to validate and normalize required ethnicity columns from school-level underlying files.
2. Extend stage schema in `demographics_release_files.py` to carry normalized ethnicity values.
3. Promote path:
   - upsert summary metrics into `school_demographics_yearly` (existing behavior)
   - upsert ethnicity breakdown into `school_ethnicity_yearly` (new behavior)
   - set `has_ethnicity_data` from normalized row coverage, not static `FALSE`
4. Preserve current behavior for `top_languages_supported` until a valid source exists.

## API/domain/web contract

1. Domain model:
   - add a typed ethnicity breakdown model to demographics latest payload.
2. API schema/OpenAPI:
   - expose ethnicity breakdown as structured list/object in school profile response.
3. Web mapper/UI:
   - map and render ethnicity breakdown when present.
   - stop surfacing `Ethnicity breakdown` in unsupported list when coverage exists.
4. Completeness:
   - keep section status `partial` only when any expected demographics metrics remain unsupported/missing.

## File-oriented implementation plan

1. `apps/backend/alembic/versions/*` (new migration for `school_ethnicity_yearly`)
2. `apps/backend/src/civitas/infrastructure/pipelines/contracts/demographics_spc.py`
3. `apps/backend/src/civitas/infrastructure/pipelines/demographics_release_files.py`
4. `apps/backend/src/civitas/infrastructure/persistence/postgres_school_profile_repository.py`
5. `apps/backend/src/civitas/domain/school_profiles/models.py`
6. `apps/backend/src/civitas/application/school_profiles/*`
7. `apps/backend/src/civitas/api/schemas/school_profiles.py`
8. `apps/backend/src/civitas/api/routes.py`
9. `apps/web/src/api/openapi.json`
10. `apps/web/src/api/generated-types.ts`
11. `apps/web/src/features/school-profile/types.ts`
12. `apps/web/src/features/school-profile/mappers/profileMapper.ts`
13. `apps/web/src/features/school-profile/components/*` (demographics surface)
14. Backend + web tests for pipeline, repository, API, mapper, and UI rendering paths.

## Codex execution checklist

1. Add contract/unit tests for ethnicity normalization before pipeline promote changes.
2. Add migration + repository reads and then wire domain/application/API contracts.
3. Regenerate OpenAPI and web generated types immediately after API schema changes.
4. Update web mapper/components and remove unsupported badge path for ethnicity when payload exists.
5. Run full lint/test gates and verify profile response for a known school row includes ethnicity breakdown.

## Required commands

1. `uv run --project apps/backend pytest apps/backend/tests/unit/test_demographics_spc_contract.py -q`
2. `uv run --project apps/backend pytest apps/backend/tests/integration/test_demographics_release_files_pipeline.py apps/backend/tests/integration/test_school_profile_repository.py apps/backend/tests/integration/test_school_profile_api.py -q`
3. `uv run --project apps/backend python tools/scripts/export_openapi.py`
4. `cd apps/web && npm run generate:types`
5. `cd apps/web && npm run test -- school-profile`
6. `make lint`
7. `make test`

## Acceptance criteria

1. Profile API returns school-level ethnicity breakdown for schools/years where SPC source contains data.
2. `coverage.ethnicity_supported` is true when ethnicity rows exist for the latest academic year.
3. UI no longer shows `Coverage gaps: Ethnicity breakdown` for those schools.
4. Backfill/lookback runs preserve idempotent behavior and do not regress existing demographics/trends metrics.
5. `Top non-English languages` remains explicitly unsupported with unchanged reasoning.

## Implementation tracking (2026-03-04)

- [x] Added migration for `school_ethnicity_yearly` with typed school-year ethnicity columns.
- [x] Extended SPC normalization contract and release-files pipeline stage/promote for ethnicity extraction and upsert.
- [x] Updated demographics promote behavior so `has_ethnicity_data` reflects actual ethnicity row coverage.
- [x] Extended profile repository/domain/application/API contracts to return structured ethnicity breakdown.
- [x] Regenerated API contract artifacts:
  - `apps/web/src/api/openapi.json`
  - `apps/web/src/api/generated-types.ts`
- [x] Updated school-profile web mapper and rendering to show ethnicity breakdown and suppress unsupported-gap badge when ethnicity rows exist.
- [x] Passed repository gates:
  - `make lint`
  - `make test`

## Runtime verification (2026-03-04)

- [x] Ran migration head:
  - `uv run --project apps/backend alembic -c apps/backend/alembic.ini upgrade head`
- [x] Ran live demographics pipeline:
  - `uv run --project apps/backend civitas pipeline run --source dfe_characteristics`
  - Result: `succeeded (downloaded=586414, staged=146601, promoted=146580, rejected=64)`
- [x] Verified SQL population and consistency:
  - `school_demographics_yearly`: `146780` rows
  - `school_ethnicity_yearly`: `141739` rows
  - `has_ethnicity_data = TRUE`: `141739` rows
  - `TRUE flag without ethnicity row`: `0`
  - `FALSE flag with ethnicity row`: `0`
- [x] Verified profile API contract against live DB:
  - `GET /api/v1/schools/100000` returns `coverage.ethnicity_supported = true` and `ethnicity_breakdown` length `19`
  - `GET /api/v1/schools/100303` returns `coverage.ethnicity_supported = false` and empty `ethnicity_breakdown`

## Risks and open questions

1. Suppression tokens (`SUPP`, `NE`, etc.) may create partial group-level sparsity; rendering rules for null categories should be explicit.
2. Decide whether v1 UI uses percentages only, or percentages + counts.
3. Confirm whether `unclassified` should be shown by default or behind an optional toggle.
