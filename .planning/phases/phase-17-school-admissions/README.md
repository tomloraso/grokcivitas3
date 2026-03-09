# Phase 17 Design Index - School Admissions

## Document Control

- Status: Planned
- Last updated: 2026-03-09
- Phase owner: Product + Engineering
- Source phase: `.planning/phased-delivery.md`
- Legacy workstream IDs: `17A` through `17D`

## Purpose

This folder contains implementation-ready planning for school-level admissions demand and offer signals, including the join-key foundation required to make admissions rows reliably align with the existing school dimension.

## Why This Phase Exists

As of 2026-03-09, the repository has no admissions pipeline, no admissions Gold table, and no admissions metrics in profile, trends, or benchmarks.

The verified live publication is:

- release page:
  - `https://explore-education-statistics.service.gov.uk/find-statistics/primary-and-secondary-school-applications-and-offers/2025-26`
- release version id:
  - `5ed40264-1835-4848-a29b-446ed6c075c2`
- school-level file id:
  - `7c9894e4-9038-4213-823c-bf50bc993cec`

## Delivery Model

1. `17A-join-key-foundation-and-source-contract.md`
2. `17B-admissions-pipeline-and-gold-schema.md`
3. `17C-serving-contract-and-benchmark-integration.md`
4. `17D-quality-gates.md`

## Architecture Constraints

1. `school_laestab` persistence is a prerequisite slice, not a nice-to-have.
2. Bronze keeps the raw school-level CSV download and manifest metadata.
3. Silver derives oversubscription and offer-rate metrics before Gold.
4. Gold stores admissions facts at `(urn, academic_year)` grain.
5. Benchmarks continue to use the post-promote materialization path.

## Definition Of Done

- GIAS school identity persists the join keys needed for admissions alignment.
- Admissions source rows are ingested repeatably into Bronze and Silver.
- Annual admissions metrics are upserted into Gold.
- Profile, trends, and benchmark surfaces expose admissions metrics with completeness metadata.
