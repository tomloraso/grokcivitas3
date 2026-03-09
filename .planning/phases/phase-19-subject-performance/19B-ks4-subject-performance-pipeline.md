# Phase 19 / 19B Design - KS4 Subject Performance Pipeline

## Document Control

- Status: Planned
- Last updated: 2026-03-09
- Depends on:
  - `.planning/phases/phase-19-subject-performance/19A-source-contract-and-scope-freeze.md`

## Objective

Ingest school-level KS4 subject results into Bronze, Silver, and Gold.

## Gold Schema

Create `school_ks4_subject_results_yearly` keyed by `(urn, academic_year, qualification_type, subject, grade)` with:

- `urn bigint not null`
- `academic_year text not null`
- `school_laestab text null`
- `school_name text not null`
- `old_la_code text null`
- `new_la_code text null`
- `la_name text null`
- `source_version text not null`
- `establishment_type_group text null`
- `pupil_count integer null`
- `qualification_type text not null`
- `qualification_detailed text null`
- `grade_structure text not null`
- `subject text not null`
- `discount_code text null`
- `subject_discount_group text null`
- `grade text not null`
- `number_achieving integer null`

## Silver Rules

1. Parse one row per published grade bucket.
2. Reject rows without `school_urn`.
3. Preserve `version` so revised and final releases remain auditable.
4. Do not collapse grades during Silver normalization.

## Repository File Plan

Add:

- `apps/backend/src/civitas/infrastructure/pipelines/ks4_subject_performance.py`
- `apps/backend/src/civitas/infrastructure/pipelines/contracts/ks4_subject_performance.py`
- `apps/backend/alembic/versions/<new>_phase_19_ks4_subject_results.py`

Tests:

- `apps/backend/tests/unit/test_ks4_subject_performance_contract.py`
- `apps/backend/tests/integration/test_ks4_subject_performance_pipeline.py`

## Vertical Slice Sequence

1. Slice 19B.1:
   - Bronze CSV ingest
   - contract tests
2. Slice 19B.2:
   - Silver normalization
   - Gold table upsert
3. Slice 19B.3:
   - derived summary materialization for serving

## Acceptance Criteria

1. KS4 subject rows are available by school, year, subject, and grade.
2. No whole-school performance logic is mixed into this pipeline.
3. Revised/final source versions remain visible in stored data.
