# Phase 18 / 18C Design - 16 To 18 Subject Performance Pipeline

## Document Control

- Status: Planned
- Last updated: 2026-03-11
- Depends on:
  - `.planning/phases/phase-19-subject-performance/19A-source-contract-and-scope-freeze.md`

## Objective

Ingest school-level 16-18 subject entry and grade data into Bronze, Silver, and Gold.

## Gold Schema

Create `school_16_to_18_subject_results_yearly` keyed by `(urn, academic_year, exam_cohort, qualification_detailed, subject, grade, source_version)` with:

- `urn bigint not null`
- `academic_year text not null`
- `school_laestab text null`
- `school_name text not null`
- `old_la_code text null`
- `new_la_code text null`
- `la_name text null`
- `source_version text not null`
- `source_downloaded_at_utc timestamptz not null`
- `exam_cohort text not null`
- `qualification_detailed text not null`
- `qualification_level text null`
- `a_level_equivalent_size numeric(9,2) null`
- `gcse_equivalent_size numeric(9,2) null`
- `grade_structure text not null`
- `subject text not null`
- `grade text not null`
- `entries_count integer null`

## Silver Rules

1. Preserve the published grade buckets and cohort labels.
2. Normalize misspelled source columns into correctly named database fields:
   - `a_level_equivelent_size` -> `a_level_equivalent_size`
   - `gcse_equivelent_size` -> `gcse_equivalent_size`
3. Do not treat `All subjects` as a ranked subject in serving summaries.
4. Persist one Gold detail row per published `source_version`; do not overwrite multiple release states that share the same cohort/subject/grade business key.
5. Normalize a serving-facing `qualification_family` from the published qualification fields before ranking logic is introduced.
6. The `exam_cohort` value remains part of the detailed Gold key and must not be collapsed away during Silver normalization.
7. Persist the Bronze/manifest download timestamp into Gold detail rows so canonical-version tie-breaks do not require request-time or materialization-time filesystem reads.

## Repository File Plan

Add:

- `apps/backend/src/civitas/infrastructure/pipelines/sixteen_to_eighteen_subject_performance.py`
- `apps/backend/src/civitas/infrastructure/pipelines/contracts/sixteen_to_eighteen_subject_performance.py`
- `apps/backend/src/civitas/infrastructure/config/settings.py` updates for 16-18 subject-performance source URLs
- `apps/backend/src/civitas/infrastructure/pipelines/__init__.py` updates to register `sixteen_to_eighteen_subject_performance`
- `apps/backend/src/civitas/infrastructure/pipelines/base.py` updates to add `PipelineSource.SIXTEEN_TO_EIGHTEEN_SUBJECT_PERFORMANCE`
- `apps/backend/alembic/versions/<new>_phase_19_16_to_18_subject_results.py`

Tests:

- `apps/backend/tests/unit/test_16_to_18_subject_performance_contract.py`
- `apps/backend/tests/integration/test_16_to_18_subject_performance_pipeline.py`
- `apps/backend/tests/unit/test_settings.py` updates for explicit subject-performance settings

## Acceptance Criteria

1. 16-18 subject rows are available by school, year, subject, and grade.
2. Source spelling oddities are normalized once in Silver, not leaked throughout the codebase.
3. This slice remains optional for release sequencing if the brief stays 4-16.
4. Qualification-family and cohort distinctions survive into Gold strongly enough that serving does not need to guess later.
