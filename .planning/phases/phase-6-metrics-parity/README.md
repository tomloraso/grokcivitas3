# Phase 6 Design Index - Metrics Parity And Benchmark Dashboard

## Document Control

- Status: Implemented
- Last updated: 2026-03-06
- Phase owner: Product + Engineering
- Source phase: `.planning/phased-delivery.md`
- Legacy workstream IDs retained: `M1` through `M6`

## Purpose

Phase 6 closed the remaining metric gaps between the planning catalog and the implemented Civitas Bronze -> Silver -> Gold platform.

It has two tracks:

1. Extend existing ingested sources where required fields already exist.
2. Add new external sources where no current ingest path exists.

## Current Bronze -> Silver -> Gold Model

This phase assumes the active source and serving model documented in `.planning/data-architecture.md` and expands the shipped product surface across:

- profile latest views
- trend series
- benchmark responses
- dashboard payloads

## Delivery Streams

1. `M1-ofsted-depth-and-derived-indicators.md`
2. `M2-demographics-support-depth.md`
3. `M3-attendance-behaviour-pipelines.md`
4. `M4-workforce-leadership-pipelines.md`
5. `M5-area-context-and-house-prices.md`
6. `M6-benchmarks-and-trend-dashboard.md`

## Exit Criteria

- Every metric in `.planning/metrics.md` is either implemented end to end or explicitly marked source-limited with user-facing completeness handling.
- All new source integrations include direct endpoint schema validation evidence before implementation.
- Lint, tests, pipeline validation, and API validation pass in one repository state.

## Sign-Off Decision

- Approved with explicit source-limited caveats for the remaining unavailable or partially published metrics.
