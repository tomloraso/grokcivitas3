# Phase 20 / 20A Design - Cohort Model And Benchmark Schema

## Document Control

- Status: Planned
- Last updated: 2026-03-09
- Depends on:
  - `.planning/phases/phase-6-metrics-parity/M6-benchmarks-and-trend-dashboard.md`

## Objective

Define the data model for percentile-capable benchmark cohorts, including similar-school cohorts.

## Cohort Dimensions

Primary similar-school cohort signature should use only persisted Gold attributes:

- phase
- establishment type group
- admissions policy where available
- religious character where available
- urban or rural classification
- pupil-roll band
- FSM band
- SEN or EHCP band

Banding rules:

- pupil-roll band: quantized national deciles or fixed product-approved buckets
- FSM band: quantized national deciles or fixed product-approved buckets
- SEN or EHCP band: quantized national deciles or fixed product-approved buckets

## New Tables

Create `metric_benchmark_cohorts_yearly` keyed by `cohort_id`:

- `cohort_id uuid primary key`
- `academic_year text not null`
- `metric_key text not null`
- `benchmark_scope text not null`
- `cohort_type text not null`
- `cohort_label text not null`
- `cohort_signature text not null`
- `definition_json jsonb not null`
- `school_count integer not null`
- `computed_at_utc timestamptz not null`

Create `metric_benchmark_distributions_yearly` keyed by `(cohort_id)`:

- `cohort_id uuid primary key references metric_benchmark_cohorts_yearly(cohort_id)`
- `mean_value numeric(14,4) null`
- `p10_value numeric(14,4) null`
- `p25_value numeric(14,4) null`
- `median_value numeric(14,4) null`
- `p75_value numeric(14,4) null`
- `p90_value numeric(14,4) null`
- `minimum_value numeric(14,4) null`
- `maximum_value numeric(14,4) null`

Create `school_metric_percentiles_yearly` keyed by `(urn, academic_year, metric_key, benchmark_scope)`:

- `urn bigint not null`
- `academic_year text not null`
- `metric_key text not null`
- `benchmark_scope text not null`
- `cohort_id uuid not null references metric_benchmark_cohorts_yearly(cohort_id)`
- `metric_value numeric(14,4) not null`
- `percentile_rank numeric(7,4) not null`
- `computed_at_utc timestamptz not null`

## Compatibility Rule

Keep the existing `metric_benchmarks_yearly` table during transition. Populate it from the new cohort tables for legacy average scopes until API and repository code fully moves over.

## Acceptance Criteria

1. Cohort definitions are reproducible from persisted attributes.
2. Percentile distribution storage supports both legacy scopes and similar-school scopes.
3. Transition does not require request-time cohort recomputation.
