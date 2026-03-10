# Phase 9 Design Index - Compare Experience

## Document Control

- Status: Completed - quality gates passed 2026-03-07
- Last updated: 2026-03-07
- Phase owner: Product + Engineering
- Source phase: `.planning/phased-delivery.md`

## Purpose

This folder contains implementation-ready planning for the compare slice of Civitas.

Phase 9 should turn the existing search and profile journeys into a shortlist-and-compare workflow that lets users evaluate up to four schools side by side.

## Delivery Model

Phase 9 is split into five deliverables:

1. `9A-compare-contract-and-metric-selection.md`
2. `9B-compare-api.md`
3. `9C-compare-selection-state-and-entry-points.md`
4. `9D-compare-web-experience.md`
5. `9E-compare-quality-gates.md`

## Execution Sequence

1. Complete `9A` first to freeze the metric set and missing-data rules.
2. Complete `9B` once the compare contract is agreed.
3. Complete `9C` so users can build a compare set from search and profile routes.
4. Complete `9D` once API types are frozen and synced.
5. Complete `9E` as final closeout and sign-off.

## Definition Of Done

- Users can add and remove schools from a compare set across search and profile routes.
- Users can compare two to four schools in one dedicated compare view.
- Metrics align deterministically even when year coverage differs between schools.
- Missing or unavailable values are explained consistently instead of silently omitted.
- Repository lint, tests, and critical frontend journeys pass.

## Tracking Log

- 2026-03-10 (post-launch UX iterations under Phase 7 umbrella):
  - P13–P13.9: Full compare page rebuild — accordion layout, visual polish, row readability, strip-to-table alignment, fixed 4-slot layout with ghost cards, accordion header hierarchy, mobile-first content, section heading alignment with profile. See `.planning/phases/phase-7-profile-ux-overhaul/README.md` tracking log for details.
  - BUG-007 fixed: Compare "Clear all" race condition — `skipUrlSyncRef` prevents URL→selection sync from repopulating cleared items.
  - BUG-008 fixed: Noisy `insufficient_years_published` completeness labels suppressed in compare cells.
  - Design system guide (`docs/architecture/design-system.md`) now documents all compare page layout patterns, accordion rules, "This school" highlight, mobile/desktop breakpoints, and unavailable treatment.

- 2026-03-07:
  - 9A completed: compare metric set, ordering, and completeness semantics frozen.
  - 9B completed: backend compare API, presenter, OpenAPI export, and frontend generated types aligned.
  - 9C completed: compare selection context, storage, routing helpers, and search/profile entry points shipped.
  - 9D completed: dedicated `/compare` route, responsive compare UI, compare-to-profile return affordance, and explicit empty/underfilled/loading/error/ready states shipped.
  - 9E completed: compare mapper/component tests, compare end-to-end coverage, `frontend build`, `make lint`, and `make test` passed in one repository state.
