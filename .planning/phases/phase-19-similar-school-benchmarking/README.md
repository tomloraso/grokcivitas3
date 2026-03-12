# Phase 19 Design Index - Similar-School Benchmarking

## Document Control

- Status: Signed off
- Last updated: 2026-03-12
- Phase owner: Product + Engineering
- Source phase: `.planning/phased-delivery.md`
- Legacy workstream IDs: `19A` through `19D`

## Purpose

This folder contains implementation-ready planning for replacing average-only benchmarks with reusable cohort definitions, percentile distributions, and school-specific percentile ranks.

## Why This Phase Exists

As of 2026-03-09, benchmark materialization supports scope averages only. The review gap is not a new external ingest gap; it is a serving-model gap. Similar-school benchmarking needs:

- deterministic cohort definitions
- reusable benchmark distributions
- percentile ranks for individual schools
- API and UI contract support for percentile context

## Source Model

This phase does not add a new external dataset. It consumes existing and newly planned Gold data from:

- school identity and demographics
- attendance, behaviour, performance, workforce
- finance, admissions, destinations, and subject phases where implemented

## Delivery Model

1. `19A-cohort-model-and-benchmark-schema.md`
2. `19B-materialization-and-backfill.md`
3. `19C-api-contract-and-web-adoption.md`
4. `19D-quality-gates.md`

## Delivered Outcome

- Similar-school cohort definitions, reusable distributions, and per-school percentile rows ship through offline benchmark materialization backed by new yearly cohort/distribution/percentile tables.
- Profile, compare, and trends contracts now expose additive benchmark `contexts[]` entries while preserving the existing average benchmark fields used by current clients.
- School profile benchmark cards now render the additive similar-school figure, percentile rank, and cohort size without replacing the existing local/national benchmark bars.
- Benchmark computation remains in the materialization path and out of the request path.

## Deviations From The Original Plan

- Profile benchmark context did not require a new `postgres_school_profile_repository.py` query path. The shipped implementation reuses `PostgresSchoolTrendsRepository` benchmark rows and maps them in the profile use case.
- Compare API responses ship additive benchmark contexts, but compare web rendering still uses the existing average-only benchmark label pattern. Similar-school compare UI remains follow-up work rather than a sign-off blocker for this phase.
- The CLI still accepts `--urn`, but the current repository implementation performs a conservative cache-wide rebuild so shared cohort/distribution state stays internally consistent.

## Validation

- `uv run --project apps/backend pytest apps/backend/tests/integration/test_school_trends_repository.py -q`
  - Result: `8 skipped` in this local environment.
- `uv run --project apps/backend pytest apps/backend/tests/integration/test_school_compare_api.py apps/backend/tests/integration/test_school_trends_api.py -q`
  - Result: `10 passed`.
- `uv run --project apps/backend pytest apps/backend/tests/unit/test_materialize_school_benchmarks_use_case.py apps/backend/tests/unit/test_pipeline_cli.py -q`
  - Result: `34 passed`.
- `npm test -- --runInBand src/features/school-profile/mappers/profileMapper.test.ts src/features/school-profile/school-profile.test.tsx`
  - Result: `21 passed`.
- `make lint`
  - Result: passed.
- `make test`
  - Result: backend `478 passed, 57 skipped`; web `243 passed`.

## Sign-Off

- Phase 19 is signed off as complete on 2026-03-12.
- Follow-up work kept out of scope for this sign-off:
  - compare-page rendering of additive similar-school benchmark contexts
  - true incremental `--urn` benchmark materialization if cache-wide rebuild cost becomes operationally significant
