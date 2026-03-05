# M6 - Benchmarks and Cross-Metric Trend Dashboard

## Goal

Provide consistent benchmark context and trend presentation across all metric families.

## Gap Coverage

- "Historical trends dashboard" for all implemented metrics
- National/local benchmark storage and exposure for each metric

## Source Strategy

- Primarily derived from already ingested metric tables.
- Additional reference datasets may be required for local benchmark geographies.

## Bronze -> Silver -> Gold Plan

1. Silver:
   - derive benchmark-ready aggregates per metric/year/geography.
2. Gold:
   - add `metric_benchmarks_yearly` keyed by `(metric_key, academic_year, benchmark_scope, benchmark_area)`;
   - optionally materialize comparison views for API performance.

## API Plan

1. Add benchmark block to profile metric payloads.
2. Extend trends endpoint with benchmark companion series.
3. Add a dedicated dashboard endpoint for multi-domain trend slices.

## Frontend Plan

1. Add unified trend dashboard section combining demographics, performance, attendance, workforce, and area metrics.
2. Display school vs benchmark deltas with clear scope labels.
3. Keep rendering resilient to partial coverage by section.

## Validation and Gates

- Deterministic benchmark aggregation tests.
- API contract tests for benchmark payload shape.
- Frontend tests for mixed benchmark availability and missing-data UX.
