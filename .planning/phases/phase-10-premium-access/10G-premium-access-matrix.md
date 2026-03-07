# 10G - Premium Access Matrix

## Document Control

- Status: Current planning baseline for Phase 10
- Last updated: 2026-03-07
- Phase owner: Product + Engineering
- Depends on:
  - `.planning/project-brief.md`
  - `.planning/phases/phase-9-compare/README.md`
  - `.planning/phases/phase-10-premium-access/README.md`

## Purpose

This document is the product source of truth for free versus premium boundaries in Civitas.

Phase 10 should not decide premium behavior ad hoc in API handlers, React components, or payment callbacks. The access model starts here, then `10C`, `10D`, and `10E` implement it.

## Principles

1. The free product must support the core Civitas research journey end to end.
2. Premium must add value through deeper analysis, richer drill-down, or advanced workflow features, not by breaking the free baseline.
3. Source-backed raw facts that define Civitas' core utility should remain broadly free unless a later product decision explicitly changes the brief.
4. Premium gating should prefer section-level or capability-level boundaries over whole-route lockouts.
5. Premium decisions remain backend-owned and contract-driven.

## Access Vocabulary

- `Free baseline`: available to anonymous users and signed-in users without premium.
- `Premium`: available only when the account holds the required premium capability.
- `Signed-in helper`: requires sign-in but is not itself a paid feature.
- `Deferred`: not part of the Phase 10 launch bundle; keep out of scope until a later phase explicitly picks it up.

## Recommended Phase 10 Launch Bundle

Freeze the first premium launch around two premium capabilities only:

1. `premium_school_analyst`
2. `premium_benchmark_dashboard`

Rationale:

- Both features are clearly additive to the free research journey.
- Both can be explained simply in paywall copy.
- Both use data and infrastructure Civitas already has or already plans to expose cleanly.
- This keeps Phase 10 focused on identity, billing, access, and two concrete premium surfaces instead of trying to monetize every route at once.

## Product Access Matrix

| Surface | Section or feature | Free tier | Premium tier | Launch classification | Capability key | Phase dependency | Notes |
|---|---|---|---|---|---|---|---|
| Search | Postcode search form and radius selection | Full access | Full access | Free baseline | - | Phase 0 | Core discovery must remain open. |
| Search | Result list, map markers, and school cards | Full access | Full access | Free baseline | - | Phase 0 | Includes core school identity and headline signals. |
| Search | Baseline sort and filter controls | Full access | Full access | Free baseline | - | Phase 0 and Phase 5 | Search must stay genuinely usable for non-paying users. |
| Search | Advanced search presets, saved filters, or future power-user search tools | Not available or teaser only | Full access when implemented | Deferred | `premium_advanced_search` | Phase 11 | Do not pull into Phase 10 unless separately prioritized. |
| Profile | Profile header and school identity | Full access | Full access | Free baseline | - | Phase 1 | Core route framing and context stay free. |
| Profile | AI school overview | Full access | Full access | Free baseline | - | Phase 8 | Overview supports discovery and should stay public. |
| Profile | AI school analyst summary | Locked teaser or paywall panel | Full access | Premium | `premium_school_analyst` | Phase 8 and Phase 10 | Strongest immediate premium differentiator. |
| Profile | Ofsted latest judgement and inspection timeline | Full access | Full access | Free baseline | - | Phase 1 and Phase 2 | Official source-backed signal should remain free. |
| Profile | Demographics and core trend signals | Full access | Full access | Free baseline | - | Phase 1, Phase 4, and Phase 6 | Keep raw demographic context in the free product. |
| Profile | Attendance and behaviour sections | Full access | Full access | Free baseline | - | Phase 6 | Core factual evidence stays free. |
| Profile | Workforce and leadership sections | Full access | Full access | Free baseline | - | Phase 6 | Keep core staff context free. |
| Profile | Academic performance section | Full access | Full access | Free baseline | - | Phase 6 | Core academic performance remains a free product pillar. |
| Profile | Neighbourhood and area context | Full access | Full access | Free baseline | - | Phase 2 and Phase 6 | Supports location-based research and should not be premium-gated. |
| Profile | Dedicated benchmark dashboard drill-down | Upgrade prompt or locked section | Full access | Premium | `premium_benchmark_dashboard` | Phase 6 and Phase 10 | Free users still get inline benchmarks; premium gets the deeper dashboard layer. |
| Profile | Completeness and unsupported-metric notices | Full access | Full access | Free baseline | - | Phase 3 and Phase 4 | Never hide data limitations behind premium. |
| Compare | Add or remove schools from compare shortlist | Full access | Full access | Free baseline | - | Phase 9 | Compare workflow entry must remain free. |
| Compare | Baseline compare table for up to four schools | Full access | Full access | Free baseline | - | Phase 9 | Compare is part of the core proposition, not the premium hook. |
| Compare | Advanced compare insights, premium metric packs, or richer benchmark overlays | Not available or teaser only | Full access when implemented | Deferred | `premium_compare_plus` | Phase 10 follow-on or Phase 11 | Do not assume MVP scope until concrete compare-plus design exists. |
| Compare | AI compare commentary | Not available | Full access when implemented | Deferred | `premium_compare_analyst` | Phase 11+ | Future premium candidate only. |
| Trends | Inline trend sparks and small trend summaries inside the profile | Full access | Full access | Free baseline | - | Current product | Keep lightweight trend direction in the free product. |
| Trends | Dedicated cross-domain benchmark dashboard route | Upgrade prompt or locked section | Full access | Premium | `premium_benchmark_dashboard` | Phase 6 and Phase 10 | Reuse the same capability as the profile dashboard drill-down. |
| Account | Sign-in, sign-out, and session state | Sign-in prompt only | Full access | Signed-in helper | - | Phase 10 | Required to purchase and manage premium. |
| Account | Upgrade CTA and plan explanation | Full access | Full access | Free baseline | - | Phase 10 | Paywall explanation should be visible wherever relevant. |
| Account | Current plan or access-status page | Sign-in required | Full access | Signed-in helper | - | Phase 10 | Useful for support and purchase recovery. |
| Billing | Hosted checkout start flow | Sign-in required | Full access | Signed-in helper | - | Phase 10 | Not a paid feature itself; it is the purchase path. |
| AI | Premium AI artifacts beyond the school analyst | Not available | Full access when implemented | Deferred | `premium_ai_plus` | Phase 11+ | Keep future AI premium expansion explicit and capability-based. |
| Export | PDF or report export | Not available | Full access when implemented | Deferred | `premium_report_export` | Phase 11 | Already outside MVP scope. |
| Saved workflow | Saved searches, saved compares, or research workspace features | Not available | Full access when implemented | Deferred | `premium_saved_research` | Phase 11+ | Candidate premium workflow bundle, not a Phase 10 requirement. |

## Launch Scope Decision Summary

### Freeze As Free Baseline

- Search and map discovery
- Full school profile across identity, Ofsted, demographics, attendance, behaviour, workforce, performance, and neighbourhood context
- AI school overview
- Inline trend cues and inline benchmark cues already present in the profile
- Baseline compare flow for up to four schools

### Freeze As Premium In Phase 10

- AI school analyst summary
- Dedicated benchmark dashboard drill-down

### Explicitly Defer

- Advanced search tools
- Compare-plus feature pack
- Compare AI commentary
- Report export
- Saved research workflows
- Broader premium AI bundles beyond the analyst view

## Technical Capability Matrix

| Capability key | Covered surfaces | Backend decision input | API contract behavior | Web behavior | Cache implications | Notes |
|---|---|---|---|---|---|---|
| `premium_school_analyst` | Profile analyst section | user session + requested section capability | `GET /api/v1/schools/{urn}` returns free baseline plus locked analyst metadata when absent; full analyst payload when present | Render locked teaser or upgrade CTA in the analyst slot | Profile cache must vary by access state or be invalidated on upgrade and sign-out | First premium launch capability. |
| `premium_benchmark_dashboard` | Dedicated dashboard drill-down from profile or trends surfaces | user session + dashboard capability | `GET /api/v1/schools/{urn}/trends/dashboard` or equivalent returns locked metadata when absent; full dashboard when present | Free users see upgrade prompt instead of full dashboard view | Dashboard and related profile drill-down caches must vary by access state | Second premium launch capability. |
| `premium_compare_plus` | Future advanced compare features | user session + compare-plus capability | Compare contract extends with locked premium feature metadata until enabled | Hide or lock only the premium compare additions, not the base compare table | Compare cache must vary by access state once introduced | Deferred until concrete compare-plus scope exists. |
| `premium_compare_analyst` | Future AI compare commentary | user session + compare-analyst capability | Separate premium compare analysis payload or premium section inside compare response | Locked premium insight panel | Compare commentary cache must vary by access state | Not part of Phase 10 launch. |
| `premium_advanced_search` | Future advanced search tools | user session + advanced-search capability | Search response or search-settings endpoints expose locked premium controls | Upgrade CTA around advanced controls, not around the whole search route | Search state caches must separate premium control state from free results | Phase 11 candidate. |
| `premium_report_export` | Future export endpoints | user session + export capability | Export endpoints reject or return paywall metadata when absent | Export CTA locked until premium is active | Minimal cache impact; authorization check on mutation path | Phase 11 candidate. |
| `premium_saved_research` | Future saved workflows | user session + saved-workflow capability | Saved-search and saved-compare endpoints gated server-side | Upgrade CTA around save actions | Per-user cache and state only | Phase 11+ candidate. |

## Implementation Rules Derived From This Matrix

1. `10C` must model premium products as bundles of named capabilities, not as one-off route flags.
2. `10D` should sell one launch premium product that grants both launch capabilities by default.
3. `10E` should treat locked premium sections as first-class response states rather than generic HTTP authorization failures on public read routes.
4. The free profile response must remain complete enough that Civitas is still useful without premium.
5. Any new premium candidate after this document must update this file before implementation starts.

## Open Questions

1. Whether the Phase 10 launch bundle should include only the two recommended launch capabilities, or also one compare-plus enhancement if Phase 9 lands early.
2. Whether the dedicated benchmark dashboard should remain one bundled premium capability or later split into profile-dashboard and compare-dashboard capabilities.
3. Whether the AI school analyst launches as the only premium AI artifact at first, or whether a future AI-plus bundle is desirable after launch learning.
