# Phase 15 Design Index - School Financial Benchmarks

## Document Control

- Status: Planned
- Last updated: 2026-03-09
- Phase owner: Product + Engineering
- Source phase: `.planning/phased-delivery.md`
- Legacy workstream IDs: `15A` through `15D`

## Purpose

This folder contains implementation-ready planning for adding annual school finance metrics from the Academies Accounts Return (AAR) into the existing Civitas Bronze -> Silver -> Gold pipeline model.

The goal is to expose finance metrics as first-class school evidence, not as a separate reporting subsystem. The same product surfaces used for demographics, attendance, performance, and workforce should also serve finance:

- profile latest values
- finance trend series
- benchmark materialization
- compare-ready metric registration

## Why This Phase Exists

As of 2026-03-09, the repository has no registered finance pipeline, no finance Gold table, and no benchmarkable school finance metrics. The review gap is real.

The verified live source is the DfE Financial Benchmarking and Insights Tool annual workbook:

- `https://financial-benchmarking-and-insights-tool.education.gov.uk/files/AAR_2023-24_download.xlsx`

The workbook is academy-focused. This phase therefore scopes the first delivery to academy finance coverage and does not claim maintained-school financial parity without a separately verified source contract.

## Delivery Model

1. `15A-source-contract-and-schema-freeze.md`
2. `15B-aar-pipeline-and-gold-schema.md`
3. `15C-serving-contract-and-benchmark-integration.md`
4. `15D-quality-gates.md`

## Architecture Constraints

1. Stay on the current documented Bronze -> Silver -> Gold model.
2. Bronze keeps the raw annual workbook asset plus manifest metadata.
3. Silver normalizes workbook rows into deterministic annual staging rows.
4. Gold stores school finance yearly facts keyed by `(urn, academic_year)`.
5. Benchmark materialization remains a post-promote workflow and must not move into the request path.

## Scope Boundaries

In scope:

- annual academy finance ingest from verified AAR workbooks
- per-pupil and ratio metrics derived from published fields
- finance latest and trend exposure in the backend serving layer
- benchmark registration for finance metrics

Out of scope:

- maintained-school CFR parity without a verified school-level source contract
- trust-level finance rollups beyond school-level facts needed for a school profile
- request-time workbook reads or ad hoc spreadsheet parsing in the API layer

## Definition Of Done

- AAR workbooks can be ingested repeatably into Bronze with manifest metadata.
- Annual school finance rows exist in Gold for academy schools with valid URNs.
- Finance metrics are available in profile latest, trends, and benchmark materialization.
- Suppressed or missing finance values surface through explicit completeness semantics.
- `make lint` and `make test` pass in one repository state with finance tests included.
