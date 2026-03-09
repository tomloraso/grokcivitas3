# Phase 18 Design Index - Leaver Destinations

## Document Control

- Status: Planned
- Last updated: 2026-03-09
- Phase owner: Product + Engineering
- Source phase: `.planning/phased-delivery.md`
- Legacy workstream IDs: `18A` through `18D`

## Purpose

This folder contains implementation-ready planning for adding school-level destination outcomes for KS4 and 16-18 leavers.

## Why This Phase Exists

As of 2026-03-09, the repository has no destination pipeline or Gold tables, even though verified DfE destination datasets are live.

This phase uses the live data-catalogue school-level datasets rather than the current release-file download endpoints, because the latest release-file payloads were verified as empty while the data-catalogue datasets remain browser-accessible and documented.

## Scope Note

The KS4 slice aligns with the current project brief. The 16-18 slice goes beyond the current 4-16 MVP brief and should therefore be scheduled after launch-critical work unless the brief is updated.

## Delivery Model

1. `18A-source-contract-and-bronze-strategy.md`
2. `18B-destinations-pipeline-and-gold-schema.md`
3. `18C-serving-contract-and-completeness.md`
4. `18D-quality-gates.md`

## Definition Of Done

- School-level destination datasets are ingested repeatably.
- KS4 and 16-18 rows share a coherent Gold model.
- Profile and trends surfaces expose destination outcomes with explicit completeness.
- The implementation is source-contract-tested and does not rely on the empty release-file path.
