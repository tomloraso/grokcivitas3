# M3 - Attendance and Behaviour Pipelines

## Goal

Introduce attendance and behaviour metrics with three-year history.

## Gap Coverage

- Overall attendance rate
- Persistent absence rate (trend)
- Suspensions and permanent exclusions (trend)

## Source Strategy

- New external sources required (DfE statistics data-sets for attendance and exclusions).
- Mandatory pre-build step: call source endpoints directly and capture real schema keys before contract design.

## Bronze -> Silver -> Gold Plan

1. Bronze:
   - add source pipelines for attendance and exclusions dataset downloads;
   - persist manifests with dataset id/version, indicator/filter ids, and checksums.
2. Silver:
   - normalize to school-level yearly rows with explicit suppression handling.
3. Gold:
   - add `school_attendance_yearly` and `school_behaviour_yearly` tables keyed by `(urn, academic_year)`.

## API Plan

1. Extend profile response with latest attendance/behaviour slice.
2. Extend trends endpoint for attendance and behaviour series.
3. Add completeness section metadata for both domains.

## Frontend Plan

1. Add attendance/behaviour panels with latest values + sparkline deltas.
2. Integrate with existing completeness notice and unsupported messaging.
3. Add regression tests for mixed coverage schools.

## Validation and Gates

- Endpoint schema evidence committed to planning notes.
- Pipeline unit tests for filter/indicator mapping and suppression parsing.
- Integration tests for profile + trends payload additions.
- Data quality gates for reject ratio, row counts, and freshness SLA.
