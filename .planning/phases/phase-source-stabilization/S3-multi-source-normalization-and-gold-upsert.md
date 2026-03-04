# Phase S3 Design - Multi-Source Normalization And Gold Upsert

## Document Control

- Status: Complete
- Last updated: 2026-03-04
- Depends on:
  - `.planning/phases/phase-source-stabilization/S2-release-file-discovery-and-bronze-ingest.md`
  - `.planning/phases/phase-hardening/H2-source-normalization-contracts.md`
  - `.planning/phases/phase-hardening/H3-historical-demographics-backfill-lookback.md`

## Objective

Normalize SPC and SEN school-level files into one consistent yearly demographics model and upsert into `school_demographics_yearly`.

## In scope

- Source-specific row contracts for SPC and SEN files.
- Column mapping to existing Gold fields.
- Join/merge by `(urn, academic_year)`.
- Idempotent promote behavior with provenance.

## Simplification constraints

1. Keep the existing Gold table shape (`school_demographics_yearly`) and fill it with better source coverage.
2. Do not introduce a parallel legacy Gold table.
3. Do not dual-write old/new normalized paths after validation is complete.
4. Remove obsolete normalization path code before phase sign-off.

## Out of scope

- New public API shape.
- New frontend visualization components.

## Normalization mapping

### Academic year

- If `time_period` exists (`YYYYYY`), normalize to `YYYY/YY`.
- If absent (older SPC files), derive from release slug (`2021-22` -> `2021/22`).

### Key fields

- `urn`: from `urn` or `URN`.
- `fsm_pct`: SPC `% of pupils known to be eligible for free school meals` (direct metric).
- `disadvantaged_pct`: SPC `% of pupils known to be eligible for free school meals (Performance Tables)`.
- `eal_pct`: SPC `% of pupils whose first language is known or believed to be other than English`.
- `first_language_english_pct`: SPC `% of pupils whose first language is known or believed to be English`.
- `first_language_unclassified_pct`: SPC `% of pupils whose first language is unclassified`.
- `sen_pct`: `(SEN support / Total pupils) * 100` from SEN file.
- `ehcp_pct`: `(EHC plan / Total pupils) * 100` from SEN file.
- `total_pupils`: prefer SEN `Total pupils`, fallback SPC headcount where compatible.

## Validation rules

1. Percentages must be finite and in `[0, 100]`.
2. Division-based percentages require `Total pupils > 0`; otherwise null.
3. Out-of-range derived values are rejected and logged to `pipeline_rejections`.
4. Join key uniqueness must be one row per `(urn, academic_year)` per source.

## File-oriented implementation plan

1. `apps/backend/src/civitas/infrastructure/pipelines/contracts/demographics_spc.py` (new)
2. `apps/backend/src/civitas/infrastructure/pipelines/contracts/demographics_sen.py` (new)
3. `apps/backend/src/civitas/infrastructure/pipelines/demographics_release_files.py`
   - stage and promote steps with merge logic.
4. `apps/backend/tests/unit/test_demographics_spc_contract.py` (new)
5. `apps/backend/tests/unit/test_demographics_sen_contract.py` (new)
6. `apps/backend/tests/integration/test_demographics_release_files_pipeline.py` (new)
7. `apps/backend/tests/integration/test_school_trends_repository.py`
   - extend for multi-year trend depth behavior.

## Codex execution checklist

1. Add contract tests before pipeline merge implementation.
2. Implement normalization with explicit rejection reasons.
3. Implement merge/upsert and idempotency integration tests.
4. Re-run trends repository tests to verify downstream behavior.

## Required commands

- `uv run --project apps/backend pytest apps/backend/tests/unit/test_demographics_spc_contract.py apps/backend/tests/unit/test_demographics_sen_contract.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/integration/test_demographics_release_files_pipeline.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/integration/test_school_trends_repository.py -q`

## Acceptance criteria

1. Gold table holds multi-year rows for approved lookback years where source exists.
2. Merge is deterministic and idempotent by `(urn, academic_year)`.
3. Derived fields (`sen_pct`, `ehcp_pct`) are validated and rejection-logged when invalid.

## Implementation tracking (2026-03-04)

- [x] Added source contracts:
  - `apps/backend/src/civitas/infrastructure/pipelines/contracts/demographics_spc.py`
  - `apps/backend/src/civitas/infrastructure/pipelines/contracts/demographics_sen.py`
- [x] Added merge/stage/promote logic in `demographics_release_files.py` with rejection logging.
- [x] Populated direct `fsm_pct` from SPC source files in stage/promote merge path.
- [x] Added contract and integration coverage:
  - `apps/backend/tests/unit/test_demographics_spc_contract.py`
  - `apps/backend/tests/unit/test_demographics_sen_contract.py`
  - `apps/backend/tests/integration/test_demographics_release_files_pipeline.py`
- [x] Removed CLI backfill command path from `apps/backend/src/civitas/cli/main.py`.
