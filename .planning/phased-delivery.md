# Phased Delivery Plan

## Document Control

- Status: Current planning index
- Last updated: 2026-03-06
- Scope: Full-stack delivery sequencing across backend, web, data pipelines, and AI summary generation

## How To Use This Document

- This file is the sprint-style phase index for Civitas.
- Each phase folder contains the implementation-ready planning for that phase.
- Existing workstream IDs such as `H1`, `S1`, `UX-1`, `M1`, and `AI-1` are retained inside the renumbered folders to avoid unnecessary churn in historical sign-off material.

## Guiding Principles

- Phases should deliver a contained user or operator outcome wherever possible.
- Source-dependent work must be gated by verified contracts before implementation.
- Backend contracts remain the source of truth for frontend work.
- Each phase closes with explicit lint, test, and acceptance evidence.
- Deployment and runtime assumptions must stay aligned with `.planning/deployment-strategy.md`.

## Legacy Phase Mapping

| New phase | Legacy name | Folder |
|---|---|---|
| Phase 0 | Phase 0 | `.planning/phases/phase-0/` |
| Phase 1 | Phase 1 | `.planning/phases/phase-1/` |
| Phase 2 | Phase 2 | `.planning/phases/phase-2/` |
| Phase 3 | Phase H | `.planning/phases/phase-3-hardening/` |
| Phase 4 | Phase S | `.planning/phases/phase-4-source-stabilization/` |
| Phase 5 | Phase UX | `.planning/phases/phase-5-ux-uplift/` |
| Phase 6 | Phase M | `.planning/phases/phase-6-metrics-parity/` |
| Phase 7 | Phase AI | `.planning/phases/phase-7-ai-overview/` |
| Phase 8 | Former Phase 3 | `.planning/phases/phase-8-compare/` |
| Phase 9 | Former Phase 4 | `.planning/phases/phase-9-premium-access/` |
| Phase 10 | Former Phase 5 | `.planning/phases/phase-10-post-mvp/` |

## Phase Sequence

### Phase 0 - Data foundation + GIAS search baseline

- Status: Implemented
- Goal: Prove the Bronze -> Silver -> Gold pipeline with one real source, expose postcode search via API, and deliver a production-grade list + map experience.
- Folder: `.planning/phases/phase-0/`
- Detailed design:
  - `README.md`
  - `0A-data-platform-baseline.md`
  - `0E-configuration-foundation.md`
  - `0B-gias-pipeline.md`
  - `0C-postcode-search-api.md`
  - `0D1-web-foundations.md`
  - `0D-web-search-map.md`
- Dependencies: none

### Phase 1 - School profiles + trends + latest Ofsted headline

- Status: Implemented
- Goal: Extend search into school profile depth with school demographics, latest Ofsted headline, profile API, trends API, and profile route.
- Folder: `.planning/phases/phase-1/`
- Detailed design:
  - `README.md`
  - `1A-source-contract-gate.md`
  - `1B-dfe-characteristics-pipeline.md`
  - `1C-ofsted-latest-pipeline.md`
  - `1D-school-profile-api.md`
  - `1E-school-trends-api.md`
  - `1F-web-routing-navigation-foundation.md`
  - `1F1-web-component-expansion-data-viz-baseline.md`
  - `1G-web-school-profile-page.md`
  - `1H-phase-1-quality-gates.md`
- Dependencies: Phase 0

### Phase 2 - Ofsted timeline + area context

- Status: Implemented
- Goal: Deepen the school profile slice with inspection history, deprivation context, and crime context.
- Folder: `.planning/phases/phase-2/`
- Detailed design:
  - `README.md`
  - `2A-source-contract-gate.md`
  - `2B-ofsted-timeline-pipeline.md`
  - `2C-ons-imd-pipeline.md`
  - `2D-police-crime-context-pipeline.md`
  - `2E-school-profile-api-extensions.md`
  - `2F-web-profile-area-context-enhancements.md`
  - `2G-phase-2-quality-gates.md`
- Dependencies: Phase 1

### Phase 3 - Hardening: data reliability + completeness + resilience

- Status: Implemented
- Goal: Stabilize the existing search/profile slices so pipeline correctness, completeness signaling, and operational safety are explicit and enforceable.
- Folder: `.planning/phases/phase-3-hardening/`
- Detailed design:
  - `README.md`
  - `H1-pipeline-run-policy-quality-gates.md`
  - `H2-source-normalization-contracts.md`
  - `H3-historical-demographics-backfill-lookback.md`
  - `H4-data-completeness-contract-api-ui.md`
  - `H5-operational-observability-freshness-coverage-drift.md`
  - `H6-pipeline-resilience-performance-hardening.md`
  - `H7-hardening-quality-gates-signoff.md`
  - `signoff-2026-03-04.md`
- Dependencies: Phase 2

### Phase 4 - Source strategy stabilization + trend history recovery

- Status: Implemented
- Goal: Replace fragile single-year demographics behavior with a verified multi-source strategy that produces reliable trend depth and clear completeness semantics.
- Folder: `.planning/phases/phase-4-source-stabilization/`
- Detailed design:
  - `README.md`
  - `S1-source-contract-and-catalog-freeze.md`
  - `S2-release-file-discovery-and-bronze-ingest.md`
  - `S3-multi-source-normalization-and-gold-upsert.md`
  - `S4-completeness-contract-and-parent-facing-copy.md`
  - `S5-quality-gates-and-signoff.md`
  - `S6-school-level-ethnicity-breakdown-support.md`
  - `source-catalog-2026-03-04.md`
  - `signoff-2026-03-04.md`
- Dependencies: Phase 2 and Phase 3

### Phase 5 - Research UX uplift

- Status: Partially implemented (`UX-1` through `UX-7` complete; `UX-8` planned)
- Goal: Elevate the search/profile experience into a polished map-first research product with stronger interaction design, visual hierarchy, and theme parity.
- Folder: `.planning/phases/phase-5-ux-uplift/`
- Detailed design:
  - `README.md`
  - `UX-1-maplibre-migration-uk-bounds-landing-state.md`
  - `UX-2-map-interaction-depth.md`
  - `UX-3-overlay-panel-refinement.md`
  - `UX-4-typography-spacing-visual-hierarchy.md`
  - `UX-5-transitions-motion.md`
  - `UX-6-navigation-site-chrome-refinement.md`
  - `UX-7-loading-empty-state-polish.md`
  - `UX-8-theme-mode-toggle.md`
  - `MAP-STYLING-REFINEMENT.md`
- Dependencies: Phase 0 and Phase 1
- Coordination notes:
  - Align with Phase 2 profile sections so styling does not drift.
  - Final UX sign-off must respect Phase 4 completeness semantics.

### Phase 6 - Metrics parity + benchmark dashboard

- Status: Implemented
- Goal: Close the remaining metric gaps in the planning catalog by extending source coverage, adding new pipelines, and exposing benchmarked profile/trend/dashboard views.
- Folder: `.planning/phases/phase-6-metrics-parity/`
- Detailed design:
  - `README.md`
  - `M1-ofsted-depth-and-derived-indicators.md`
  - `M2-demographics-support-depth.md`
  - `M3-attendance-behaviour-pipelines.md`
  - `M4-workforce-leadership-pipelines.md`
  - `M5-area-context-and-house-prices.md`
  - `M6-benchmarks-and-trend-dashboard.md`
- Dependencies: Phase 3 and Phase 4

### Phase 7 - AI overview + school identity enrichment

- Status: Implemented
- Goal: Enrich school identity data and add one stored, factual AI-generated school overview on profile pages.
- Folder: `.planning/phases/phase-7-ai-overview/`
- Detailed design:
  - `README.md`
  - `AI-1-gias-enrichment.md`
  - `AI-2-school-overview-summary.md`
  - `AI-4-extensible-ai-platform.md`
- Dependencies: Phase 2, Phase 3, and Phase 4

### Phase 8 - Compare experience

- Status: Planned
- Goal: Deliver side-by-side comparison for up to four schools with stable metric alignment, benchmark context, and missing-data handling.
- Folder: `.planning/phases/phase-8-compare/`
- Detailed design:
  - `README.md`
  - `8A-compare-contract-and-metric-selection.md`
  - `8B-compare-api.md`
  - `8C-compare-selection-state-and-entry-points.md`
  - `8D-compare-web-experience.md`
  - `8E-compare-quality-gates.md`
- Dependencies: Phase 1, Phase 2, Phase 4, and Phase 6

### Phase 9 - Premium access + entitlements

- Status: Planned
- Goal: Introduce authentication, postcode-level entitlements, payment flow, and backend-enforced premium access boundaries.
- Folder: `.planning/phases/phase-9-premium-access/`
- Detailed design:
  - `README.md`
  - `9A-provider-boundary-gate.md`
  - `9B-auth-session-foundation.md`
  - `9C-entitlements-domain-and-persistence.md`
  - `9D-payment-checkout-and-webhooks.md`
  - `9E-premium-api-and-web-paywall.md`
  - `9F-premium-quality-gates.md`
- Dependencies: Phase 8

### Phase 10 - Post-MVP growth and operational expansion

- Status: Planned
- Goal: Package the next wave of growth, SEO, admin tooling, performance optimization, and export features into scoped follow-on slices.
- Folder: `.planning/phases/phase-10-post-mvp/`
- Detailed design:
  - `README.md`
  - `10A-seo-location-pages.md`
  - `10B-admin-operations-dashboard.md`
  - `10C-report-export.md`
  - `10D-advanced-search-and-filters.md`
  - `10E-performance-and-cache-optimization.md`
  - `10F-post-mvp-prioritization-and-quality-gates.md`
- Dependencies: Phase 8 and Phase 9 for MVP completion; individual slices may also depend on Phase 5 or Phase 7 where relevant

## Phase Summary

| Phase | Outcome | Status |
|---|---|---|
| 0 | Search by postcode with map/list baseline | Implemented |
| 1 | School profiles, trends, latest Ofsted | Implemented |
| 2 | Inspection history and area context | Implemented |
| 3 | Deterministic quality, completeness, resilience | Implemented |
| 4 | Multi-year trend recovery and source stabilization | Implemented |
| 5 | Search/profile UX uplift and theme parity | Partially implemented |
| 6 | Expanded metrics coverage and dashboard benchmarks | Implemented |
| 7 | AI overview and richer school identity data | Implemented |
| 8 | Compare up to four schools | Planned |
| 9 | Auth, entitlements, and premium access | Planned |
| 10 | Growth, admin, SEO, exports, optimization | Planned |

## Open Decisions

1. Authentication provider for Phase 9.
2. Payment provider and premium packaging details for Phase 9.
3. Whether Phase 10 should remain one numbered backlog phase or later split into individually scheduled delivery phases once MVP is complete.
