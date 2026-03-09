# Phased Delivery Plan

## Document Control

- Status: Current planning index
- Last updated: 2026-03-09
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
| Phase 7 | Phase 6a | `.planning/phases/phase-7-profile-ux-overhaul/` |
| Phase 8 | Phase AI | `.planning/phases/phase-8-ai-overview/` |
| Phase 9 | Former Phase 3 | `.planning/phases/phase-9-compare/` |
| Phase 10 | Former Phase 4 | `.planning/phases/phase-10-premium-access/` |
| Phase 11 | New MVP follow-on | `.planning/phases/phase-11-search-results-mvp/` |
| Phase 12 | Former Phase 5 | `.planning/phases/phase-12-post-mvp/` |
| Phase 13 | New launch readiness | `.planning/phases/phase-13-launch-readiness/` |
| Phase 14 | New post-launch follow-on | `.planning/phases/phase-14-favourites-and-saved-research/` |

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

### Phase 7 - School profile parent-first UX overhaul

- Status: Completed — committed 2026-03-07 (P1–P4); P5 responsive polish and P6 design system docs deferred
- Goal: Redesign the school profile page around the parent user model — inline benchmark bars on every metric card, parent-language section headings, and removal of the duplicate standalone benchmark section.
- Folder: `.planning/phases/phase-7-profile-ux-overhaul/`
- Detailed design:
  - `README.md`
  - `P1-design-tokens-benchmark-colours.md`
  - `P2-stat-card-visual-redesign.md`
  - `P3-benchmark-wiring-sections.md`
  - `P4-section-narrative-copy.md`
  - `P5-responsive-mobile-polish.md`
  - `P6-design-system-documentation.md`
- Full brief: `.planning/ux-overhaul/README.md`
- Dependencies: Phase 5 (design token system + component primitives), Phase 6 (benchmark data live in API)
- Coordination notes:
  - No backend changes required — all benchmark data already returned by `GET /api/v1/schools/{urn}`.
  - If StatCard benchmark pattern is approved, apply same pattern to Phase 9 (compare) web experience.
  - P5 and P6 are intentionally deferred — do not close Phase 7 until responsive audit and design system docs are complete.
  - The parent-first UX direction established here (plain-English labels, inline benchmarks, non-evaluative trend colours) is the target standard for all future page overhauls: map page, compare page, Pro/premium pages, and any future routes. Apply the same principles when those pages are redesigned.

### Phase 8 - AI overview + school identity enrichment

- Status: Implemented
- Goal: Enrich school identity data and add one stored, factual AI-generated school overview on profile pages.
- Folder: `.planning/phases/phase-8-ai-overview/`
- Detailed design:
  - `README.md`
  - `AI-1-gias-enrichment.md`
  - `AI-2-school-overview-summary.md`
  - `AI-4-extensible-ai-platform.md`
- Dependencies: Phase 2, Phase 3, and Phase 4

### Phase 9 - Compare experience

- Status: Completed - quality gates passed 2026-03-07
- Goal: Deliver side-by-side comparison for up to four schools with stable metric alignment, benchmark context, and missing-data handling.
- Folder: `.planning/phases/phase-9-compare/`
- Detailed design:
  - `README.md`
  - `9A-compare-contract-and-metric-selection.md`
  - `9B-compare-api.md`
  - `9C-compare-selection-state-and-entry-points.md`
  - `9D-compare-web-experience.md`
  - `9E-compare-quality-gates.md`
- Dependencies: Phase 1, Phase 2, Phase 4, and Phase 6

### Phase 10 - Premium access program

- Status: Planned, but must be delivered as two gated stages
- Goal: Introduce authenticated user context, feature-tier entitlements, payment flow, and backend-enforced premium access boundaries without moving product rules into the frontend.
- Folder: `.planning/phases/phase-10-premium-access/`
- Delivery stages:
  - Stage 10A: identity, app-session, premium-plan, and feature-entitlement foundation
  - Stage 10B: checkout, webhook fulfillment, premium API contracts, and paywall UX
- Detailed design:
  - `10G-premium-access-matrix.md`
  - `README.md`
  - `10A-provider-boundary-gate.md`
  - `10B-auth-session-foundation.md`
  - `10C-entitlements-domain-and-persistence.md`
  - `10D-payment-checkout-and-webhooks.md`
  - `10E-premium-api-and-web-paywall.md`
  - `10F-premium-quality-gates.md`
- Dependencies: Phase 9
- Coordination notes:
  - `10G-premium-access-matrix.md` is the product source of truth for free versus premium boundaries; payment and API wiring should not guess at section-level product boundaries.
  - Existing web caching for profile and compare responses must become access-aware before premium rollout.
  - Stage 10A can be feature-flagged and validated before Stage 10B goes live, but Phase 10 is not complete until both gates pass.

### Phase 11 - Postcode results table MVP

- Status: Planned
- Goal: Turn postcode search into a shortlist-friendly decision table backed by a server-side, pipeline-maintained search summary projection while keeping linked map context and compare entry points.
- Folder: `.planning/phases/phase-11-search-results-mvp/`
- Detailed design:
  - `README.md`
  - `11A-search-summary-projection.md`
  - `11B-search-summary-api-and-sort-contract.md`
  - `11C-results-table-web-experience.md`
  - `11D-phase-11-quality-gates.md`
- Dependencies: Phase 0, Phase 1, Phase 6, and Phase 9
- Coordination notes:
  - Keep request-time work limited to postcode resolution, geospatial radius filtering, distance calculation, and final `ORDER BY`.
  - Default postcode ranking remains straight-line distance in this phase; do not introduce blended quality scoring or personalization.
  - Mobile parity is required, but it should use stacked result cards rather than a compressed horizontal table.

### Phase 12 - Post-MVP growth and operational expansion

- Status: Planned
- Goal: Package the next wave of growth, SEO, admin tooling, performance optimization, and export features into scoped follow-on slices.
- Folder: `.planning/phases/phase-12-post-mvp/`
- Detailed design:
  - `README.md`
  - `11A-seo-location-pages.md`
  - `11B-admin-operations-dashboard.md`
  - `11C-report-export.md`
  - `11D-advanced-search-and-filters.md`
  - `11E-performance-and-cache-optimization.md`
  - `11F-post-mvp-prioritization-and-quality-gates.md`
- Dependencies: Phase 10 and Phase 11 for MVP completion; individual slices may also depend on Phase 5 or Phase 8 where relevant

### Phase 13 - Product foundation and launch readiness

- Status: Planned
- Goal: Deliver the foundational product pages (About, Data Sources, Contact), legal compliance pages (Privacy, Terms, Accessibility), SEO infrastructure (meta tags, structured data, robots.txt, sitemap, favicon), and cookie consent required before public launch or Phase 10 billing.
- Folder: `.planning/phases/phase-13-launch-readiness/`
- Detailed design:
  - `README.md`
  - `L1-content-page-foundation.md`
  - `L2-seo-and-discoverability-infrastructure.md`
  - `L3-about-and-data-sources.md`
  - `L4-legal-and-compliance.md`
  - `L5-quality-gates.md`
- Dependencies: Phase 5 (design tokens, component primitives, site chrome)
- Coordination notes:
  - L4 (Legal and Compliance) is a hard prerequisite for Phase 10 Stage 10B. Cookie consent must be live before Stage 10A sets session cookies in non-local environments.
  - L2 SEO infrastructure is the foundation that Phase 12 location-based SEO pages build on.
  - No backend dependencies — this is a frontend-only phase.
  - Can run in parallel with Phase 10 Stage 10A identity work.

### Phase 14 - Favourites and saved research workflows

- Status: Planned, deferred until after go-live unless spare pre-launch capacity appears
- Goal: Add account-owned school favourites and a lightweight saved research library on top of the Phase 10 identity and entitlement foundation.
- Folder: `.planning/phases/phase-14-favourites-and-saved-research/`
- Detailed design:
  - `README.md`
  - `14A-account-favourites-foundation.md`
  - `14B-favourites-web-and-library.md`
  - `14C-phase-14-quality-gates.md`
- Dependencies: Phase 9, Phase 10, and Phase 11
- Coordination notes:
  - This phase is intentionally outside the Phase 10 launch bundle even though favourites may later use a premium capability.
  - Pull this phase forward before go-live only if Phase 10 Stage 10B and Phase 13 launch blockers are already complete.
  - Keep the saved-research scope narrow at first: school favourites and a personal library, not a full workspace product.
  - Reuse the `school_search_summary` read model for account-library rows rather than hydrating full school profiles.
  - Use explicit save and remove mutations plus viewer-aware saved-state on search and profile routes; do not depend on browser-only toggle state.

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
| 7 | School profile parent-first UX overhaul | Completed (P1–P4) |
| 8 | AI overview and richer school identity data | Implemented |
| 9 | Compare up to four schools | Completed |
| 10 | Identity, feature entitlements, payments, and premium enforcement | Planned (two gated stages) |
| 11 | Fast postcode results table with server-side shortlist signals | Planned |
| 12 | Growth, admin, SEO, exports, optimization | Planned |
| 13 | Product pages, legal compliance, SEO infra, cookie consent | Planned |
| 14 | Account favourites and saved research workflows | Planned |

## Open Decisions

1. Final payment-provider choice and launch packaging for the account-level premium tier.
2. Whether neighbourhood context should remain premium after launch learning or move back into the free baseline.
3. Whether Stage 10A should ship dark before Stage 10B, or remain internal-only until the full premium flow is ready.
4. Whether Phase 12 should remain one numbered backlog phase or later split into individually scheduled delivery phases once MVP is complete.
5. Whether Phase 14 favourites work should stay strictly post-launch or be pulled forward if pre-launch capacity remains after launch blockers close.
