# Phase 18 Design Index - Leaver Destinations

## Document Control

- Status: Implemented - leaver destinations pipeline, serving integration, and unsupported-stage completeness flow complete (2026-03-11)
- Last updated: 2026-03-11
- Phase owner: Product + Engineering
- Source phase: `.planning/phased-delivery.md`
- Legacy workstream IDs: `18A` through `18D`

## Purpose

This folder contains implementation-ready planning for adding school-level destination outcomes for KS4 and 16-18 leavers.

## Why This Phase Exists

As of 2026-03-11, the repository still has no destination pipeline or Gold tables, but the live EES data-catalogue routes are working and have now been proved into local Bronze under:

- `data/bronze/leaver_destinations/2026-03-11/ks4/2022-23/`
- `data/bronze/leaver_destinations/2026-03-11/16_to_18/2022-23/`

The earlier draft for this phase contained stale dataset ids and stale column assumptions. Those have now been replaced with the proved live contract.

## Source Contract Summary

1. The public Bronze contract is the data-catalogue `.../csv` route, not a direct content-API URL.
2. The current 2023/24 release pages publish destination-year `2022/23` CSV assets.
3. The raw files contain mixed count and percentage rows plus breakdown dimensions, so Gold and serving design must pivot that raw shape rather than assume pre-flattened percentage columns.

## Scope Note

The KS4 slice aligns with the current project brief. The 16-18 slice goes beyond the current 4-16 MVP brief and should therefore be scheduled after launch-critical work unless the brief is updated.

## Delivery Model

1. `18A-source-contract-and-bronze-strategy.md`
2. `18B-destinations-pipeline-and-gold-schema.md`
3. `18C-serving-contract-and-completeness.md`
4. `18D-quality-gates.md`

## Definition Of Done

- School-level destination datasets are ingested repeatably through the proved public CSV routes.
- KS4 and 16-18 rows share a coherent Gold model that matches the real raw file shape.
- Profile and trends surfaces expose destination outcomes with explicit completeness.
- The implementation is source-contract-tested and does not depend on stale dataset ids or unproved direct content-API calls.
