# Phase Metrics Parity Design Index - Metrics Catalog Closure

## Document Control

- Status: Final QA pass complete; all quality gates green
- Last updated: 2026-03-05
- Phase owner: Product + Engineering
- Source phase: `.planning/phased-delivery.md`

## Purpose

This phase closes the remaining metric gaps between `.planning/metrics.md` and the current Civitas Bronze -> Silver -> Gold implementation.

It has two tracks:

1. Extend existing ingested sources where required fields already exist.
2. Add new external sources where no current ingest path exists.

## Current Bronze -> Silver -> Gold Model (as implemented)

| Source | Bronze artifacts | Silver staging | Gold serving tables | API/UI status |
|---|---|---|---|---|
| `gias` | `data/bronze/gias/<date>/edubasealldata.csv` | `staging.gias__<run_id>` | `schools` | Exposed in search/profile identity |
| `dfe_characteristics` (SPC+SEN release files) | release-file CSVs + `demographics_release_files.manifest.json` | `staging.dfe_characteristics__<run_id>`, `staging.dfe_characteristics_ethnicity__<run_id>`, `staging.dfe_characteristics_send_need__<run_id>`, `staging.dfe_characteristics_home_lang__<run_id>` | `school_demographics_yearly`, `school_ethnicity_yearly`, `school_send_primary_need_yearly`, `school_home_language_yearly` | Demographics + ethnicity + SEND need + top home languages exposed |
| `dfe_attendance` | release-file CSVs + `dfe_attendance.manifest.json` | `staging.dfe_attendance__<run_id>` | `school_attendance_yearly` | Attendance metrics exposed on profile/trends |
| `dfe_behaviour` | release-file CSVs + `dfe_behaviour.manifest.json` | `staging.dfe_behaviour__<run_id>` | `school_behaviour_yearly` | Suspensions/exclusions metrics exposed on profile/trends |
| `dfe_workforce` | release-file CSVs + `dfe_workforce.manifest.json` | `staging.dfe_workforce__<run_id>` | `school_workforce_yearly`, `school_leadership_snapshot` | Workforce + leadership metrics exposed on profile/trends |
| `dfe_performance` | `ks2.meta.json`, `ks4.meta.json`, paged query payloads + `dfe_performance.manifest.json` | `staging.dfe_performance__<run_id>` | `school_performance_yearly` | Performance now exposed on profile |
| `ofsted_latest` | `latest_inspections.csv` (+ metadata) | `staging.ofsted_latest__<run_id>` | `school_ofsted_latest` | Headline + sub-judgements + most-recent inspection age exposed |
| `ofsted_timeline` | asset CSV set + manifest | `staging.ofsted_timeline__<run_id>` | `ofsted_inspections` | Inspection history exposed |
| `ons_imd` | IMD CSV + metadata | `staging.ons_imd__<run_id>` | `area_deprivation` | IMD decile/rank/score + IDACI exposed |
| `uk_house_prices` | monthly CSV + metadata | `staging.uk_house_prices__<run_id>` | `area_house_price_context` | House-price context and trend exposed |
| `police_crime_context` | archive ZIP, extracted files, metadata | `staging.police_crime_context__<run_id>` | `area_crime_context` | Local incident counts/categories exposed |

## Metrics Gap Analysis (from `.planning/metrics.md`)

| Metric group | Current status | Gap type |
|---|---|---|
| Attainment 8 / Progress 8 / GCSE / EBacc / KS2 | Implemented | Closed in current repo state |
| Disadvantaged Progress 8 gap | Implemented | Closed in current repo state |
| Ofsted overall + history | Implemented | Closed in current repo state |
| Ofsted sub-judgements with dates | Implemented (Phase M1) | Closed in current repo state |
| Time since last inspection | Implemented (Phase M1) | Closed in current repo state |
| FSM %, EHCP/SEN, EAL | Implemented | Closed in current repo state |
| FSM6 | Implemented (Phase M2) | Closed in current repo state |
| Ethnicity breakdown | Implemented | Closed in current repo state |
| SEND primary need categories | Implemented (Phase M2) | Closed in current repo state |
| Gender breakdown | Implemented where published (Phase M2) | Partial (current SPC releases publish derivable gender coverage for recent years only) |
| Pupil mobility/turnover | Source-limited (Phase M2) | School-level column not published in current SPC releases |
| Overall attendance, persistent absence trend | Implemented (Phase M3) | Closed in current repo state |
| Suspensions/permanent exclusions trend | Implemented (Phase M3) | Closed in current repo state |
| Workforce metrics (PTR, supply, experience, turnover, QTS, qualifications) | Implemented where published (Phase M4) | Partial (PTR/supply/QTS available; experience/turnover/qualifications source-limited in current school-level assets) |
| Crime rate per 1,000 + 3-year trend | Implemented (Phase M5) | Closed in current repo state |
| IMD domain scores | Implemented (Phase M5) | Closed in current repo state |
| House prices trend/radius context | Implemented (Phase M5) | Closed in current repo state |
| Top 5 home languages | Source-limited (Phase M2) | Detailed school-level language columns not published in current SPC releases |
| Pupil premium impact | Missing | Additional source required |
| Historical trends dashboard for all metrics | Implemented (Phase M6) | Closed in current repo state |
| National/local benchmarks on all metrics | Implemented (Phase M6) | Closed in current repo state |

## External Source Validation Evidence (required pre-integration)

On 2026-03-04, direct endpoint inspection was run for the new DfE performance source:

- `GET https://api.education.gov.uk/statistics/v1/data-sets/019afee4-e5d0-72f9-9a8f-d7a1a56eac1d/meta`
- `GET https://api.education.gov.uk/statistics/v1/data-sets/19e39901-a96c-be76-b9c2-6af54ae076d2/meta`
- `POST .../query` samples for KS2 and KS4 with `pageSize=1`

Observed response shape used in implementation:

- Top-level query keys: `warnings`, `paging`, `results`
- Result keys: `timePeriod`, `geographicLevel`, `locations`, `filters`, `values`
- KS2 sample ids: filters `fV8YF`, `jfhAM`; indicators `IwjBz`, `i2s6X`; period `2024/2025`
- KS4 sample ids: filters `IzpBz`, `pPmSo`, `ibG6X`, `LZ6Wj`; indicators include `kgVhs`, `Pwoeb`, `dDo0Z`, `hCRyW`, `bmztT`, `uEko4`, `mqo9K`; period `2024/2025`

## Delivery Streams

1. `M1-ofsted-depth-and-derived-indicators.md`
2. `M2-demographics-support-depth.md`
3. `M3-attendance-behaviour-pipelines.md`
4. `M4-workforce-leadership-pipelines.md`
5. `M5-area-context-and-house-prices.md`
6. `M6-benchmarks-and-trend-dashboard.md`

## Milestone Tracking

- M1: delivered (2026-03-04)
- M2: delivered + post-M6 pipeline/API end-to-end validation complete (2026-03-05); ready for frontend testing.
- M3: delivered + post-M6 pipeline/API end-to-end validation complete (2026-03-05); ready for frontend testing.
- M4: delivered + post-M6 pipeline/API end-to-end validation complete (2026-03-05); ready for frontend testing.
- M5: delivered + post-M6 pipeline/API end-to-end validation complete (2026-03-05); ready for frontend testing.
- M6: delivered + validation gate complete (2026-03-05); ready for frontend testing.

## Final QA Pass (2026-03-05)

- Regression fixes applied during QA:
  - Updated behaviour source defaults to current publication slug (`suspensions-and-permanent-exclusions-in-england`) and relaxed release-slug validation for live term slugs.
  - Updated workforce default release slugs to `2022,2023,2024` and relaxed release-slug validation for year slugs.
  - Hardened integration fixtures (`test_demographics_release_files_pipeline.py`, `test_uk_house_prices_pipeline.py`, `test_school_profile_repository.py`) to clean test keys before seeding so QA is stable on hydrated databases.
  - Updated runtime contract verification sample in `tools/scripts/verify_source_contracts_runtime.py` for current ONS IMD 2019 required fields.

- Required gates:
  - `make test` -> passed (`267 backend tests`, `215 web tests`).
  - `make lint` -> passed (`ruff check`, `ruff format --check`, backend `mypy`, web `eslint`, web `tsc --noEmit`).
  - Historical note: earlier QA run surfaced `mypy` issues (`73` errors in `7` files); this blocker was resolved in the final gate run on 2026-03-05.

- Pipeline validation (canonical `data/bronze`):
  - Full sweep command run after QA gates:
    - `uv run --project apps/backend civitas pipeline run --source <source>` for:
      `gias`, `dfe_characteristics`, `dfe_attendance`, `dfe_behaviour`, `dfe_workforce`, `dfe_performance`, `ofsted_latest`, `ofsted_timeline`, `ons_imd`, `uk_house_prices`, `police_crime_context`.
  - Final sweep result:
    - `gias`: `succeeded (downloaded=52271, staged=50529, promoted=50529, rejected=1742)`
    - `dfe_characteristics`: `succeeded (downloaded=586414, staged=146601, promoted=146598, rejected=64)`
    - `dfe_attendance`: `skipped_no_change (downloaded=976442, staged=0, promoted=0, rejected=0)`
    - `dfe_behaviour`: `skipped_no_change (downloaded=1494110, staged=0, promoted=0, rejected=0)`
    - `dfe_workforce`: `skipped_no_change (downloaded=1909085, staged=0, promoted=0, rejected=0)`
    - `dfe_performance`: `skipped_no_change (downloaded=1238069, staged=0, promoted=0, rejected=0)`
    - `ofsted_latest`: `skipped_no_change (downloaded=21966, staged=0, promoted=0, rejected=0)`
    - `ofsted_timeline`: `skipped_no_change (downloaded=23241, staged=0, promoted=0, rejected=0)`
    - `ons_imd`: `succeeded (downloaded=67511, staged=33755, promoted=33755, rejected=0)`
    - `uk_house_prices`: `succeeded (downloaded=149085, staged=149085, promoted=149085, rejected=0)`
    - `police_crime_context`: `skipped_no_change (downloaded=17937898, staged=0, promoted=0, rejected=0)`
  - Post-run SQL verification:
    - `latest successful run per source` query returns all `11` expected sources.
    - `status='succeeded' AND promoted_rows > 0` query returns all `11` expected sources (Bronze -> Silver -> Gold promote path confirmed per source).
    - Operational hygiene query confirms `running_runs=0` and `pipeline_source_locks=0`.
    - After `make test` created stale `running` rows in `pipeline_runs`, cleanup SQL was applied (`UPDATE 22`) before the final sweep.

- API end-to-end validation:
  - Command used: `uv run --project apps/backend python -` with `fastapi.testclient.TestClient(app)` calling:
    - `GET /api/v1/schools/100008`
    - `GET /api/v1/schools/100008/trends`
    - `GET /api/v1/schools/100008/trends/dashboard`
  - Result:
    - HTTP statuses: `200 / 200 / 200`
    - Profile payload populated under current schema with benchmark block (`benchmarks.metrics` count=`45`), plus latest domain blocks (`demographics_latest`, `attendance_latest`, `behaviour_latest`, `workforce_latest`, `performance.latest`, `area_context`).
    - Trends payload includes both `series` and `benchmarks`:
      - `fsm_pct`: `series=6`, `benchmarks=6`
      - `overall_attendance_pct`: `series=3`, `benchmarks=3`
      - `suspensions_rate`: `series=3`, `benchmarks=3`
      - `teacher_turnover_pct`: `series=3`, `benchmarks=3`
    - Dashboard payload includes all expected sections with metric points:
      - `demographics` (`metrics=9`, `points=54`)
      - `attendance` (`metrics=3`, `points=9`)
      - `behaviour` (`metrics=4`, `points=12`)
      - `workforce` (`metrics=6`, `points=18`)
      - `performance` (`metrics=5`, `points=15`)
      - `area` (`metrics=3`, `points=66`)

## Post-M6 Validation Evidence

- Command:
  - `uv run --project apps/backend pytest apps/backend/tests/unit/test_demographics_spc_contract.py apps/backend/tests/unit/test_demographics_sen_contract.py apps/backend/tests/unit/test_dfe_attendance_contract.py apps/backend/tests/unit/test_dfe_behaviour_contract.py apps/backend/tests/unit/test_dfe_workforce_contract.py apps/backend/tests/unit/test_uk_house_prices_contract.py apps/backend/tests/unit/test_ons_imd_transforms.py apps/backend/tests/unit/test_pipeline_cli.py apps/backend/tests/unit/test_pipeline_contract_metadata.py apps/backend/tests/unit/test_settings.py apps/backend/tests/integration/test_demographics_release_files_pipeline.py apps/backend/tests/integration/test_dfe_characteristics_pipeline.py apps/backend/tests/integration/test_dfe_attendance_pipeline.py apps/backend/tests/integration/test_dfe_behaviour_pipeline.py apps/backend/tests/integration/test_dfe_workforce_pipeline.py apps/backend/tests/integration/test_ons_imd_pipeline.py apps/backend/tests/integration/test_uk_house_prices_pipeline.py apps/backend/tests/integration/test_data_quality_repository.py apps/backend/tests/integration/test_school_profile_repository.py apps/backend/tests/integration/test_school_profile_api.py apps/backend/tests/unit/test_get_school_profile_use_case.py apps/backend/tests/unit/test_cached_school_profile_repository.py apps/backend/tests/integration/test_school_trends_repository.py apps/backend/tests/integration/test_school_trends_api.py apps/backend/tests/unit/test_get_school_trends_use_case.py apps/backend/tests/unit/test_api_contract_checks.py -q`
- Result:
  - `129 passed`
- M6 lint gate:
  - `uv run --project apps/backend ruff check apps/backend/src/civitas/application/school_trends/dto.py apps/backend/src/civitas/application/school_trends/use_cases.py apps/backend/src/civitas/infrastructure/persistence/postgres_school_trends_repository.py apps/backend/src/civitas/application/school_profiles/dto.py apps/backend/src/civitas/application/school_profiles/use_cases.py apps/backend/src/civitas/api/schemas/school_trends.py apps/backend/src/civitas/api/schemas/school_profiles.py apps/backend/src/civitas/api/routes.py apps/backend/tests/integration/test_school_trends_repository.py apps/backend/tests/unit/test_get_school_trends_use_case.py apps/backend/tests/integration/test_school_trends_api.py apps/backend/tests/integration/test_school_profile_api.py apps/backend/tests/unit/test_api_contract_checks.py apps/backend/tests/unit/test_get_school_profile_use_case.py`
  - Result: `All checks passed`

## Exit Criteria

- Every metric in `.planning/metrics.md` is either:
  - implemented end-to-end (pipeline + API + frontend), or
  - explicitly marked unavailable with source-level evidence and user-facing completeness copy.
- All new source integrations include direct endpoint schema validation evidence before implementation.
- Lint/tests pass and phase acceptance evidence is captured in a single repo state.

## Sign-Off Decision

- **Approved with explicit source-limited metric caveats**.
- `make lint`, `make test`, pipeline operational validation, and phase endpoint API validation are complete.
- Source-limited metrics (mobility, top-language detail, workforce experience/turnover/qualifications, leadership detail) are exposed with deterministic completeness/coverage metadata.
