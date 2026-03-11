# Phase 19 Design Index - Similar-School Benchmarking

## Document Control

- Status: Planned
- Last updated: 2026-03-09
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

## Definition Of Done

- Similar-school cohorts are deterministic and reproducible.
- Percentile distributions exist for benchmarked metrics.
- School profile and trends payloads can expose percentile context.
- Benchmark computation remains off the request path.
