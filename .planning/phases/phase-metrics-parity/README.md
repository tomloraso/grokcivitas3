# Phase Metrics Parity Design Index - Metrics Catalog Closure

## Document Control

- Status: Proposed
- Last updated: 2026-03-04
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
| `dfe_characteristics` (SPC+SEN release files) | release-file CSVs + `demographics_release_files.manifest.json` | `staging.dfe_characteristics__<run_id>`, `staging.dfe_characteristics_ethnicity__<run_id>` | `school_demographics_yearly`, `school_ethnicity_yearly` | Demographics + ethnicity exposed |
| `dfe_performance` | `ks2.meta.json`, `ks4.meta.json`, paged query payloads + `dfe_performance.manifest.json` | `staging.dfe_performance__<run_id>` | `school_performance_yearly` | Performance now exposed on profile |
| `ofsted_latest` | `latest_inspections.csv` (+ metadata) | `staging.ofsted_latest__<run_id>` | `school_ofsted_latest` | Headline + sub-judgements + most-recent inspection age exposed |
| `ofsted_timeline` | asset CSV set + manifest | `staging.ofsted_timeline__<run_id>` | `ofsted_inspections` | Inspection history exposed |
| `ons_imd` | IMD CSV + metadata | `staging.ons_imd__<run_id>` | `area_deprivation` | IMD decile/rank/score + IDACI exposed |
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
| FSM6 | Missing | Additional source required |
| Ethnicity breakdown | Implemented | Closed in current repo state |
| SEND primary need categories | Missing | Existing source extension and/or new source slice |
| Gender breakdown | Missing | Existing source extension needed |
| Pupil mobility/turnover | Missing | Existing source extension needed |
| Overall attendance, persistent absence trend | Missing | Additional source required |
| Suspensions/permanent exclusions trend | Missing | Additional source required |
| Workforce metrics (PTR, supply, experience, turnover, QTS, qualifications) | Missing | Additional source required |
| Crime rate per 1,000 + 3-year trend | Partial (counts only) | Existing + additional source required (population denominator) |
| IMD domain scores | Missing (only core IMD/IDACI fields) | Existing source extension needed |
| House prices trend/radius context | Missing | Additional source required |
| Top 5 home languages | Missing | Additional source required (if school-level publishable) |
| Pupil premium impact | Missing | Additional source required |
| Historical trends dashboard for all metrics | Partial (demographics + profile-level performance only) | API/UI extension needed |
| National/local benchmarks on all metrics | Missing | Cross-cutting benchmark model needed |

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

## Exit Criteria

- Every metric in `.planning/metrics.md` is either:
  - implemented end-to-end (pipeline + API + frontend), or
  - explicitly marked unavailable with source-level evidence and user-facing completeness copy.
- All new source integrations include direct endpoint schema validation evidence before implementation.
- Lint/tests pass and phase acceptance evidence is captured in a single repo state.
