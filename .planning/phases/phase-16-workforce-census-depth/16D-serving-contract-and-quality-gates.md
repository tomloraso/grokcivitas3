# Phase 16 / 16D Design - Serving Contract And Quality Gates

## Document Control

- Status: Planned
- Last updated: 2026-03-09

## Serving Additions

Profile latest should add:

- `workforce_latest.teacher_headcount_total`
- `workforce_latest.teacher_fte_total`
- `workforce_latest.support_staff_headcount_total`
- `workforce_latest.support_staff_fte_total`
- `workforce_latest.leadership_headcount`
- `workforce_latest.teacher_average_mean_salary_gbp`
- `workforce_latest.teacher_absence_pct`
- `workforce_latest.teacher_vacancy_rate`
- `workforce_latest.third_party_support_staff_headcount`

Profile detail or breakdown sections should add:

- teacher sex split
- teacher age split
- teacher ethnicity split
- teacher qualification split
- support-staff post mix

Trend series should add:

- teacher totals
- support-staff totals
- leadership share
- pay
- absence
- vacancies
- third-party support

## Repository File Plan

Likely files:

- `apps/backend/src/civitas/infrastructure/persistence/postgres_school_profile_repository.py`
- `apps/backend/src/civitas/infrastructure/persistence/cached_school_profile_repository.py`
- `apps/backend/src/civitas/infrastructure/persistence/postgres_school_trends_repository.py`
- `apps/backend/src/civitas/infrastructure/persistence/postgres_data_quality_repository.py`
- `apps/backend/src/civitas/application/school_profiles/`
- `apps/backend/src/civitas/application/school_trends/`

## Required Commands

- `uv run --project apps/backend pytest apps/backend/tests/unit/test_dfe_workforce_contract.py apps/backend/tests/integration/test_dfe_workforce_pipeline.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/integration/test_school_profile_repository.py apps/backend/tests/integration/test_school_profile_api.py apps/backend/tests/integration/test_school_trends_repository.py apps/backend/tests/integration/test_school_trends_api.py apps/backend/tests/integration/test_data_quality_repository.py -q`
- `make lint`
- `make test`

## Data Quality Gates

1. Each source file has fixture coverage for suppression tokens.
2. Merge logic is deterministic at `(urn, academic_year)` grain.
3. Empty-source files do not null out already-supported metrics.
4. Completeness metadata distinguishes:
   - source unavailable
   - source empty
   - source suppressed

## Exit Criteria

- One school can be traced Bronze -> Silver -> Gold for teacher characteristics and support staff.
- New workforce metrics are visible in profile and trends payloads.
- Existing workforce metrics from Phase 6 still pass regression tests.
