# Phase 16 Design Index - Workforce Census Depth

## Document Control

- Status: Planned
- Last updated: 2026-03-09
- Phase owner: Product + Engineering
- Source phase: `.planning/phased-delivery.md`
- Legacy workstream IDs: `16A` through `16D`

## Purpose

This folder contains implementation-ready planning for expanding the current workforce coverage from a small summary set into a fuller school-workforce view built from published school-level DfE workforce files.

Phase 6 already created the workforce foundation. Phase 16 extends it with:

- teacher characteristics
- support staff composition
- leadership structure
- teacher pay
- teacher sickness absence
- teacher vacancies
- third-party support staff

## Why This Phase Exists

As of 2026-03-09, the repository only exposes a narrow subset of workforce metrics. The verified live 2024 DfE workforce release contains materially richer school-level data that is not yet modeled.

The current verified release page is:

- `https://explore-education-statistics.service.gov.uk/find-statistics/school-workforce-in-england/2024`
- release version id: `ba5318f9-2f18-4ef5-8c71-a4db8546758c`

This phase intentionally plans around the files that are live and non-empty today. Two current school-level files are still zero-byte and are therefore treated as source-limited inputs, not delivery blockers:

- `Size of the school workforce - school level`
- `Teacher turnover - school level`

## Delivery Model

1. `16A-source-catalog-and-schema-freeze.md`
2. `16B-teacher-characteristics-pipeline.md`
3. `16C-support-staff-and-derived-metrics.md`
4. `16D-serving-contract-and-quality-gates.md`

## Architecture Constraints

1. Extend the existing `dfe_workforce` source family unless a code split is justified by tests.
2. Keep raw CSV and ZIP assets in Bronze.
3. Normalize each source file independently in Silver before merging at school-year grain.
4. Use explicit metric-level completeness instead of inventing backfills for empty files.
5. Keep benchmark cache computation on the existing post-promote path.

## Definition Of Done

- Teacher and support-staff depth is available in Gold at school-year grain.
- Leadership size and staffing mix derive from published teacher/support data.
- Pay, absence, vacancies, and external-support metrics are exposed through serving layers.
- Existing workforce metrics remain stable and are not regressed.
- Empty-source limitations remain explicit in completeness metadata and docs.
