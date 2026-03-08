# Phase 11 Design Index - Postcode Results Table MVP

## Document Control

- Status: Planned
- Last updated: 2026-03-08
- Phase owner: Product + Engineering
- Source phase: `.planning/phased-delivery.md`

## Purpose

This folder contains implementation-ready planning for the MVP refinement of the main postcode-search experience.

Phase 11 should keep postcode search map-first while adding a fast results-analysis mode over the same result set: a route-backed overlay with a server-ranked desktop decision table, stacked mobile result cards, and direct compare/detail entry points.

## Delivery Model

Phase 11 is split into four deliverables:

1. `11A-search-summary-projection.md`
2. `11B-search-summary-api-and-sort-contract.md`
3. `11C-results-table-web-experience.md`
4. `11D-phase-11-quality-gates.md`

## Execution Sequence

1. Complete `11A` first to freeze the Gold read model and pipeline ownership.
2. Complete `11B` once the projection fields and sort rules are agreed.
3. Complete `11C` once the backend contract is stable and frontend types are regenerated.
4. Complete `11D` as final MVP cutline validation and sign-off.

## Definition Of Done

- Postcode search returns an enriched, server-ordered result set backed by a pipeline-maintained read model.
- Desktop postcode mode keeps the existing map + sidebar search journey and adds a results overlay with the agreed MVP table columns.
- Mobile postcode mode opens the same results overlay as a full-screen analysis sheet with stacked result cards.
- Users can filter by primary and secondary, switch between `closest` and `ofsted`, add schools to compare, and open detail pages.
- Request-time work is limited to postcode resolution, geo filtering, distance calculation, and final ordering.
