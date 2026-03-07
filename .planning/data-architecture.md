# Data Architecture

## Document Control

- Status: Current planning baseline
- Last updated: 2026-03-06
- Scope: Active Bronze -> Silver -> Gold model for Civitas school research

## Principles

1. Every served value should be traceable back to a Bronze asset.
2. Bronze is immutable and is the reproducibility checkpoint.
3. Silver is the normalization and contract-enforcement layer.
4. Gold is optimized for API and web query patterns, not generic data warehousing.
5. Source-limited fields must be represented with explicit completeness semantics rather than silent omission.
6. AI-generated summaries are derived artifacts with provenance, not source records.

## Zone Definitions

### Bronze - Raw asset archive

- Location: `data/bronze/<source>/<run-date>/`
- Content: original CSV, ZIP, JSON, metadata, manifests, and verification artifacts
- Behavior: immutable, timestamped, and safe to re-read for reruns

### Silver - Run-scoped normalized staging

- Location: `staging.<source>__<run_id>` tables in PostgreSQL
- Responsibilities:
  - type coercion
  - contract normalization
  - column renaming
  - row rejection capture
  - source-specific validation
- Behavior: recreated per run and dropped after successful promote

### Gold - Serving store

- Engine: PostgreSQL + PostGIS
- Responsibilities:
  - denormalized serving tables for profile, trends, and search
  - spatial and keyed indexes
  - current and historical school facts
  - area-context aggregates
  - AI summary storage and provenance

## Active Source Set

| Source key | Primary source | Current role |
|---|---|---|
| `gias` | GIAS bulk downloads | Canonical school identity and geography |
| `dfe_characteristics` | DfE SPC + SEN school-level release files | Demographics, ethnicity, SEND, language coverage |
| `dfe_attendance` | DfE attendance release files | Attendance and persistent absence |
| `dfe_behaviour` | DfE suspensions and exclusions release files | Behaviour indicators |
| `dfe_workforce` | DfE workforce release files | Workforce and leadership |
| `dfe_performance` | DfE KS2 and KS4 statistics APIs | Performance indicators |
| `ofsted_latest` | Ofsted latest inspection asset | Headline rating and sub-judgements |
| `ofsted_timeline` | Ofsted inspection history assets | Full inspection timeline |
| `ons_imd` | IMD release files | Deprivation context |
| `police_crime_context` | Police UK archive files | Local crime aggregates |
| `uk_house_prices` | Land Registry monthly files | House-price context |
| `postcodes_io` | Postcodes.io API | User-postcode resolution and LSOA enrichment |

## Gold Tables

### Core school serving tables

| Table | Purpose | Key |
|---|---|---|
| `schools` | Canonical school identity, location, and enriched GIAS fields | `urn` |
| `postcode_cache` | Cached postcode resolution results | `postcode` |
| `school_ofsted_latest` | Latest inspection headline and sub-judgements | `urn` |
| `ofsted_inspections` | Full inspection history | `inspection_number` |

### Yearly school fact tables

| Table | Purpose | Key |
|---|---|---|
| `school_demographics_yearly` | Core yearly demographics and need fields | `(urn, academic_year)` |
| `school_ethnicity_yearly` | Ethnicity breakdown by year | `(urn, academic_year, ethnicity_group)` |
| `school_send_primary_need_yearly` | SEND primary-need breakdown by year | `(urn, academic_year, need_code)` |
| `school_home_language_yearly` | School-level home-language coverage where published | `(urn, academic_year, language_code)` |
| `school_attendance_yearly` | Attendance and absence metrics | `(urn, academic_year)` |
| `school_behaviour_yearly` | Suspensions and exclusions metrics | `(urn, academic_year)` |
| `school_workforce_yearly` | Workforce metrics | `(urn, academic_year)` |
| `school_performance_yearly` | KS2 and KS4 performance indicators | `(urn, academic_year)` |

### Snapshot and area-context tables

| Table | Purpose | Key |
|---|---|---|
| `school_leadership_snapshot` | Latest leadership and staffing snapshot fields | `urn` |
| `area_deprivation` | IMD and IDACI by LSOA | `lsoa_code` |
| `area_crime_context` | Local crime aggregates by month and radius | `(urn, month, crime_category, radius_meters)` |
| `area_house_price_context` | House-price aggregates and trends for local area context | `(area_code, month)` |

### AI and operational support tables

| Table | Purpose | Key |
|---|---|---|
| `school_ai_summaries` | Current stored overview summary per school | `urn` |
| `school_ai_summary_history` | Archived summary versions | synthetic history key |
| `pipeline_runs` | Pipeline execution history | `id` |
| `pipeline_rejections` | Rejected-row diagnostics | `id` |
| `app_cache_versions` | Cache invalidation tokens | `cache_key` |

## Serving Patterns

### Search

- Search reads from `schools` with spatial filtering and joins lightweight headline fields.
- User postcode resolution is cache-first through `postcode_cache` and Postcodes.io fallback.

### Profile

- Profile responses assemble latest school facts from current-serving tables.
- Completeness metadata is attached at the section level so the UI can explain gaps.

### Trends and dashboard

- Trend endpoints read typed yearly fact tables directly.
- Benchmark responses are derived alongside school series so frontend views stay contract-driven.

### AI overview

- AI overview generation runs after data assembly, not inline with profile requests.
- Stored summaries include prompt version, provider or model information, timestamps, and data version hashes.

## Pipeline Module Layout

Active source pipelines live under `apps/backend/src/civitas/infrastructure/pipelines/`.

Current pipeline families include:

- `gias.py`
- `demographics_release_files.py`
- `dfe_attendance.py`
- `dfe_behaviour.py`
- `dfe_workforce.py`
- `dfe_performance.py`
- `ofsted_latest.py`
- `ofsted_timeline.py`
- `ons_imd.py`
- `police_crime_context.py`
- `uk_house_prices.py`

Each pipeline follows the same shape:

1. Download or resolve source assets into Bronze.
2. Normalize and validate rows into Silver staging.
3. Promote into Gold with upsert semantics.

## Data Quality Rules

- Quality gates must fail the run when counters or reject ratios breach thresholds.
- Source verification scripts are part of the contract surface for unstable or discovery-driven feeds.
- Trend coverage and completeness behavior are product requirements, not just data-engineering concerns.
- Reruns must remain idempotent at the Gold key level.

## Open Questions

1. Whether additional benchmark materialization is needed once compare and premium workloads are live.
2. Whether `school_ai_summaries` should remain profile-only or later expand to export or report use cases.
3. Whether Phase 11 optimization work should introduce materialized views for compare-heavy workloads.
