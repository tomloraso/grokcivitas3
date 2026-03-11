# Phase 19 Design Index - Subject Performance

## Document Control

- Status: Planned
- Last updated: 2026-03-11
- Phase owner: Product + Engineering
- Source phase: `.planning/phased-delivery.md`
- Legacy workstream IDs: `19A` through `19D`

## Purpose

This folder contains implementation-ready planning for school-level subject performance, covering KS4 subject attainment and 16-18 subject entries and grades.

## Why This Phase Exists

As of 2026-03-09, the repository only exposes whole-school KS2 and KS4 performance metrics. Verified live subject-level school datasets exist and are not yet modeled.

This phase also freezes an important scope boundary: verified subject value-added data is national-level, not school-level. The phase therefore plans school-level subject attainment and entries, but not school-level subject progress scores.

## Scope Note

KS4 subject performance aligns with the current project brief. The 16-18 slice extends beyond the current 4-16 MVP brief and should be sequenced accordingly unless the brief is updated.

Implementation sequencing rule:

- ship KS4 end to end first
- keep 16-18 backend-ready but releasable independently
- do not expose 16-18 subject-performance UI/API slices as part of the 4-16 MVP without an explicit brief update

## Delivery Model

1. `19A-source-contract-and-scope-freeze.md`
2. `19B-ks4-subject-performance-pipeline.md`
3. `19C-16-to-18-subject-performance-pipeline.md`
4. `19D-serving-contract-and-quality-gates.md`

## Definition Of Done

- KS4 subject results are ingested at school level.
- 16-18 subject entry and grade results are ingested at school level.
- Subject-performance runs use explicit pipeline sources rather than overloading `dfe_performance`.
- Detailed Gold rows preserve published source-version auditability without overwriting provisional/revised/final variants.
- Subject-performance summaries can be served without request-time CSV parsing and are materialized from an explicit canonical-version selection rule.
- School-level subject value-added remains out of scope until a verified source exists.
