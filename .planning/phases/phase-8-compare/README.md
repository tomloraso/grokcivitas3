# Phase 8 Design Index - Compare Experience

## Document Control

- Status: Planned
- Last updated: 2026-03-06
- Phase owner: Product + Engineering
- Source phase: `.planning/phased-delivery.md`

## Purpose

This folder contains implementation-ready planning for the compare slice of Civitas.

Phase 8 should turn the existing search and profile journeys into a shortlist-and-compare workflow that lets users evaluate up to four schools side by side.

## Delivery Model

Phase 8 is split into five deliverables:

1. `8A-compare-contract-and-metric-selection.md`
2. `8B-compare-api.md`
3. `8C-compare-selection-state-and-entry-points.md`
4. `8D-compare-web-experience.md`
5. `8E-compare-quality-gates.md`

## Execution Sequence

1. Complete `8A` first to freeze the metric set and missing-data rules.
2. Complete `8B` once the compare contract is agreed.
3. Complete `8C` so users can build a compare set from search and profile routes.
4. Complete `8D` once API types are frozen and synced.
5. Complete `8E` as final closeout and sign-off.

## Definition Of Done

- Users can add and remove schools from a compare set across search and profile routes.
- Users can compare two to four schools in one dedicated compare view.
- Metrics align deterministically even when year coverage differs between schools.
- Missing or unavailable values are explained consistently instead of silently omitted.
- Repository lint, tests, and critical frontend journeys pass.
