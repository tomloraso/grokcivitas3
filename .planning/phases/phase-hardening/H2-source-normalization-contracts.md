# Phase H2 Design - Source Normalization Contracts At Bronze To Staging Boundary

## Document Control

- Status: Proposed
- Last updated: 2026-03-03
- Depends on:
  - `.planning/phases/phase-hardening/H1-pipeline-run-policy-quality-gates.md`
  - `.planning/phases/phase-1/1A-source-contract-gate.md`
  - `.planning/phases/phase-2/2A-source-contract-gate.md`
  - `apps/backend/src/civitas/infrastructure/pipelines/*`
  - `docs/architecture/backend-conventions.md`

## Objective

Implement explicit, versioned normalization contracts per source family so source-format drift is handled predictably without corrupting Gold tables.

## Scope

### In scope

- Define canonical normalization contracts for GIAS, DfE, Ofsted latest, Ofsted timeline, ONS IMD, and Police crime.
- Keep Bronze assets immutable and apply normalization in stage only.
- Standardize sentinel handling, date parsing, numeric parsing, and enum mapping.
- Add schema drift detection and contract-version visibility in pipeline metadata.

### Out of scope

- Historical backfill logic (owned by `H3`).
- API/UI completeness messaging (owned by `H4`).

## Normalization Boundary Decision

1. Bronze:
   - raw transport artifacts only.
2. Stage (effective Silver boundary):
   - all semantic normalization and validation.
3. Gold:
   - typed, stable, application-serving records.

## Contract Priorities

1. DfE:
   - accept both `YYYY/YY` and compact `YYYYYY` style period tokens.
   - canonicalize to `YYYY/YY`.
2. Ofsted latest and timeline:
   - normalize `"NULL"`, `"Not judged"`, and code `9` behavior explicitly.
   - preserve ungraded outcomes when graded code absent.
3. GIAS:
   - strict but comprehensive date-format acceptance.
4. ONS and Police:
   - enforce finite numeric ranges and explicit null semantics.

## File-Oriented Implementation Plan

1. `apps/backend/src/civitas/infrastructure/pipelines/contracts/` (new folder)
   - create per-source contract modules:
     - `dfe.py`
     - `ofsted_latest.py`
     - `ofsted_timeline.py`
     - `gias.py`
     - `ons_imd.py`
     - `police.py`
   - include:
     - required headers,
     - supported schema versions,
     - sentinel tokens,
     - parser and mapper functions.
2. `apps/backend/src/civitas/infrastructure/pipelines/*`
   - replace ad-hoc inline parsing with contract-module imports.
   - write contract version into metadata sidecars and staged rows where applicable.
3. `apps/backend/src/civitas/infrastructure/pipelines/base.py`
   - add optional `contract_version` field to pipeline stage results.
4. `tools/scripts/verify_source_contracts_runtime.py` (new)
   - execute contract checks against Bronze samples and fail on mismatch.
5. `apps/backend/tests/unit/test_*_transforms.py`
   - keep coverage at pipeline adapter boundary and add drift regression cases for contract behavior.
6. `apps/backend/tests/fixtures/*`
   - reuse existing source fixtures as Bronze-like runtime contract samples to avoid duplicate fixture trees.

## Testing And Quality Gates

### Required tests

- DfE year normalization supports both compact and slash formats.
- Ofsted normalization maps `"NULL"` and code `9` per policy.
- Header drift fails fast with descriptive contract error.
- Contract version is emitted in metadata and test-asserted.

### Required gates

- `uv run --project apps/backend pytest apps/backend/tests/unit/test_dfe_characteristics_transforms.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/unit/test_ofsted_latest_transforms.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/unit/test_ofsted_timeline_transforms.py -q`
- `uv run --project apps/backend python tools/scripts/verify_source_contracts_runtime.py`
- `make lint`
- `make test`

## Acceptance Criteria

1. Source normalization behavior is contract-driven and versioned for all active feeds.
2. Compact-vs-slash year format drift no longer collapses staged rows to zero.
3. Ofsted ungraded outcomes are preserved instead of being dropped by code-only validation.
4. Contract drift is visible and blocks promote paths through hard gates from `H1`.

## Risks And Mitigations

- Risk: contract modules add maintenance overhead.
  - Mitigation: shared parser utilities and fixture-driven tests.
- Risk: policy mistakes can over-normalize invalid data.
  - Mitigation: explicit reason-coded rejections and gate thresholds from `H1`.
