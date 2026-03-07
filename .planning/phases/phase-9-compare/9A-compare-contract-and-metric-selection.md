# 9A - Compare Contract And Metric Selection

## Goal

Define the exact compare payload shape and the metric set Phase 9 will support before backend and frontend implementation begins.

## Scope

- Comparison of two to four schools.
- One aligned compare contract shared by the compare API and the web compare route.
- Deterministic handling for missing, partial, or differently-dated metrics.

## Contract Ownership

- `GET /api/v1/schools/compare` is the source of truth for aligned compare rows.
- The web compare route may augment API data with client-side selection context such as `distance_miles` captured from postcode search results.
- School identity header metadata is separate from aligned metric rows. School name, postcode, and compare-column ordering belong in the top `schools` block rather than repeated metric rows.

## School Header Block

The compare response must expose one school header object per requested URN in request order. Each object should include:

- `urn`
- `name`
- `postcode`
- `phase`
- `type`
- `age_range_label`

The web compare state may additionally retain:

- `distance_miles` when the school was added from a postcode search result
- source context needed for a "Back to results" or "Back to compare" affordance

## Section Order

The compare experience should ship with these aligned sections in this order:

1. `inspection`
2. `demographics`
3. `attendance`
4. `behaviour`
5. `workforce`
6. `performance`
7. `area`

## Frozen Metric Catalog

The rows below are the frozen Phase 9 compare set. Row ordering must follow this table exactly.

| Section | Metric key | Label | Unit | Notes |
|---|---|---|---|---|
| `inspection` | `ofsted_overall_effectiveness` | Latest Ofsted | `text` | Use the latest published overall effectiveness label or ungraded outcome text. No benchmark payload. |
| `inspection` | `most_recent_inspection_date` | Most recent inspection | `date` | Use the most recent graded or ungraded inspection date. No benchmark payload. |
| `inspection` | `days_since_most_recent_inspection` | Time since inspection | `days` | Display as user-readable text in `value_text`, keep raw days in `value_numeric`. No benchmark payload. |
| `demographics` | `disadvantaged_pct` | Disadvantaged pupils | `percent` | Keep alongside direct FSM so compare does not silently swap one measure for another. Benchmark supported. |
| `demographics` | `fsm_pct` | Free School Meals | `percent` | Benchmark supported. |
| `demographics` | `fsm6_pct` | FSM6 | `percent` | Benchmark supported. |
| `demographics` | `sen_pct` | SEN support | `percent` | Benchmark supported. |
| `demographics` | `ehcp_pct` | EHCP | `percent` | Benchmark supported. |
| `demographics` | `eal_pct` | EAL | `percent` | Benchmark supported. |
| `demographics` | `ethnicity_summary` | Ethnicity summary | `text` | Build from up to the top three ethnicity groups with non-zero percentages, sorted descending. No benchmark payload. |
| `attendance` | `overall_attendance_pct` | Overall attendance | `percent` | Benchmark supported. |
| `attendance` | `overall_absence_pct` | Overall absence | `percent` | Benchmark supported. |
| `attendance` | `persistent_absence_pct` | Persistent absence | `percent` | Benchmark supported. |
| `behaviour` | `suspensions_count` | Suspensions | `count` | Benchmark supported. |
| `behaviour` | `suspensions_rate` | Suspensions rate | `rate` | Benchmark supported. |
| `behaviour` | `permanent_exclusions_count` | Permanent exclusions | `count` | Benchmark supported. |
| `behaviour` | `permanent_exclusions_rate` | Permanent exclusions rate | `rate` | Benchmark supported. |
| `workforce` | `pupil_teacher_ratio` | Pupil to teacher ratio | `ratio` | Benchmark supported. |
| `workforce` | `supply_staff_pct` | Supply staff | `percent` | Benchmark supported. |
| `workforce` | `qts_pct` | Qualified Teacher Status | `percent` | Benchmark supported. |
| `workforce` | `headteacher_name` | Headteacher | `text` | Use the current published headteacher name where available. No benchmark payload. |
| `workforce` | `headteacher_tenure_years` | Headteacher tenure | `years` | Use the latest published leadership snapshot. No benchmark payload. |
| `performance` | `ks2_reading_expected_pct` | KS2 reading expected | `percent` | Show when at least one selected school publishes KS2 data. No benchmark payload in Phase 9. |
| `performance` | `ks2_writing_expected_pct` | KS2 writing expected | `percent` | Show when at least one selected school publishes KS2 data. No benchmark payload in Phase 9. |
| `performance` | `ks2_maths_expected_pct` | KS2 maths expected | `percent` | Show when at least one selected school publishes KS2 data. No benchmark payload in Phase 9. |
| `performance` | `ks2_combined_expected_pct` | KS2 combined expected | `percent` | Show when at least one selected school publishes KS2 data. No benchmark payload in Phase 9. |
| `performance` | `ks2_combined_higher_pct` | KS2 combined higher | `percent` | Show when at least one selected school publishes KS2 data. No benchmark payload in Phase 9. |
| `performance` | `attainment8_average` | Attainment 8 | `score` | Show when at least one selected school publishes KS4 data. Benchmark supported. |
| `performance` | `progress8_average` | Progress 8 | `score` | Show when at least one selected school publishes KS4 data. Benchmark supported. |
| `performance` | `progress8_disadvantaged_gap` | Progress 8 disadvantaged gap | `score` | Show when at least one selected school publishes KS4 data. Benchmark supported. |
| `performance` | `engmath_5_plus_pct` | English and Maths grade 5+ | `percent` | Show when at least one selected school publishes KS4 data. Benchmark supported. |
| `performance` | `ebacc_entry_pct` | EBacc entry | `percent` | Show when at least one selected school publishes KS4 data. Benchmark supported. |
| `area` | `imd_decile` | IMD decile | `decile` | Use school-linked LSOA deprivation context. No benchmark payload. |
| `area` | `area_crime_incidents_per_1000` | Crime incidents per 1,000 | `rate` | Benchmark supported where existing Gold benchmark data already provides local and national context. |
| `area` | `area_house_price_average` | Average house price | `currency` | Benchmark supported where existing Gold benchmark data already provides local and national context. |
| `area` | `area_house_price_annual_change_pct` | House price annual change | `percent` | Benchmark supported where existing Gold benchmark data already provides local and national context. |

## Contract Rules

- Each metric row must expose a stable metric identifier, label, unit, section key, and deterministic row order.
- Each school cell must expose:
  - `urn`
  - `value_text`
  - `value_numeric`
  - `year_label`
  - `snapshot_date`
  - `availability`
  - `completeness_status`
  - `completeness_reason_code`
  - `benchmark` metadata where already supported
- Rows should align by metric identifier, not by raw source column names.
- Numeric rows must populate both `value_numeric` and a preformatted `value_text`.
- Text and date rows must populate `value_text`; `value_numeric` should be `null`.
- Different years across schools are allowed, but year labels must remain visible in every populated yearly cell.

## Missing-Data Rules

- `available` means the cell has a usable published value.
- `unsupported` means the metric is not published for that school, school phase, or school type at the required level.
- `unavailable` means the metric is part of the compare set but is missing for that school and latest usable year or snapshot.
- `suppressed` means the source publishes the metric but the value is withheld by source suppression rules.
- `completeness_status` and `completeness_reason_code` must reuse the existing profile and trends completeness vocabulary whenever a current reason is known.
- A row should remain visible when at least one selected school is `available`, `unavailable`, or `suppressed`.
- A row should be hidden only when every selected school would be `unsupported`.

## Phase And School-Type Gating

- Do not synthesize a single mixed-phase performance score.
- Show KS2 performance rows when at least one selected school publishes KS2 data.
- Show KS4 performance rows when at least one selected school publishes KS4 data.
- For selected schools where a visible row is not phase-appropriate, set the cell to `unsupported`.
- Distance is not part of the backend compare payload. When present, it is rendered from client-side selection context captured on search routes.

## Acceptance Criteria

- Compare metric list is frozen and documented.
- Missing-data semantics are shared with existing profile and trends completeness language.
- API contract design is specific enough for schema and web mapping work to start.
