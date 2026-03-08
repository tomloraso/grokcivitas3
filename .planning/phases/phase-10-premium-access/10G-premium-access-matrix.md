# 10G - Premium Access Matrix

## Document Control

- Status: Current planning baseline for Phase 10
- Last updated: 2026-03-08
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
6. Premium boundaries should drive engagement before conversion. The free product must be genuinely useful so users trust the product before being asked to pay.
7. Locked premium sections should make the value behind the boundary visible, not hide it. Prefer teaser or partial-preview treatment over empty states or removed sections.
8. Premium as an experience should feel ambient and tasteful, not promotional. Subtle design cues over badges, banners, or celebratory unlock animations.

## Current Implementation Baseline

- The current school profile contract exposes `overview_text` and `analyst_text` as plain nullable strings end to end. That means the analyst surface currently conflates `not published` with `not allowed yet`.
- The current benchmark dashboard route returns either the full dashboard payload or a hard failure. It has no `locked` or teaser response mode yet.
- The current web profile flow background-loads the dashboard after the core profile renders and folds it into the same `benchmarkDashboard` view model consumed by free profile sections. That coupling must be removed before the dashboard can become premium.
- The current app-shell session model carries authentication only. It does not yet expose premium status, capability keys, or an access epoch for cache invalidation.

## Premium Branding Rules

- The paid tier is called `Premium`. All user-facing copy, route names, and CTA labels must use `Premium`.
- `Pro` is reserved for a future B2B tier. Do not use `Pro` in Phase 10 copy, code identifiers, or design assets.
- The header account indicator for a premium user should read `Premium` in brand purple using the display typeface at small scale. It is status, not advertising.
- Do not introduce gold, gradient, or badge-style premium indicators. The design language remains the same navy-and-purple palette used across the free product.

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
- This is strong enough for an initial paid test, but still a thin consumer subscription bundle. Package and merchandise it as deeper school insight, not as access to a "dashboard".

## Launch Surface Clarifications

### Benchmark Dashboard Scope

- The free profile experience keeps the latest benchmark snapshot and inline benchmark cues already rendered inside metric cards.
- `premium_benchmark_dashboard` is the dedicated benchmark drill-down surface: multi-year benchmark series, section-level drill-down, and any route or page that depends on `GET /api/v1/schools/{urn}/trends/dashboard` or an equivalent follow-on benchmark route.
- The free profile route must not depend on the premium benchmark dashboard endpoint to render its baseline content. If the profile page currently preloads the dashboard route, that fetch behavior should change during Phase 10.
- Current implementation note: the web profile currently background-loads the dashboard and merges it into the same benchmark view model used by free metric cards. Phase 10 must split free inline benchmark mapping from premium dashboard mapping before the paywall ships.

### Premium Section State Rules

- Premium-sensitive sections must distinguish `locked` from `unavailable`, `not_published`, or `unsupported`.
- A free user hitting a premium boundary should see a teaser or upgrade prompt, not the same state used when no premium artifact exists yet.
- This rule applies immediately to the profile analyst section and to the premium benchmark dashboard route.

### Premium Display Treatment Rules

Locked premium sections must use teaser or partial-preview treatment rather than hiding content or showing empty upgrade prompts. The goal is to prove value exists behind the boundary so the user can see the premium content is real, school-specific, and worth paying for without making the experience feel manipulative.

**Preview mechanics:**

- Narrative premium text may use a progressive CSS gradient mask: content transitions from fully clear to fully blurred over approximately 60px, then remains fully blurred for the rest of the section.
- Structured benchmark previews should show a partial real preview with a fade or lock boundary, not a fully blurred fake chart. Avoid showing blurred values the backend did not actually send.
- The preview treatment is a frontend-only presentation concern. The backend does not send the full premium payload to unauthorized viewers. Instead the backend sends `teaser_text` or `teaser_payload` alongside `state: locked` for preview-eligible sections.
- The CTA overlays the locked region inline, not as a modal or banner. It is a refined card with a contextual one-liner and a single button.

**Per-section teaser depth:**

| Section | Teaser content returned by backend | Display treatment | CTA copy pattern |
|---|---|---|---|
| AI school analyst summary | First 2-3 sentences of the analyst text | Clear teaser text, then progressive blur over remaining placeholder content, inline CTA overlay | "Get the full analyst view for [School Name]" |
| Benchmark dashboard drill-down | Dashboard layout structure plus limited real preview content such as metric group headings, column labels, and up to 1-2 latest-year sample rows | Visible layout and sample rows, then a fade or lock boundary with inline CTA overlay. Do not render fully blurred fake charts or hidden values. | "See how [School Name] compares across all benchmarks" |
| Deferred premium features not yet implemented | None | `hidden` — do not tease content that does not exist yet | Not applicable |

**What must never be blurred or hidden:**

- Section titles and headers — always visible so the user knows the section exists.
- Completeness notices — never hide data limitations behind premium.
- Free baseline content in the same route — blur applies only to the premium portion, not surrounding free sections.
- The existence of premium sections — the section container renders even for free users.
- Fabricated values, bars, or deltas — never render blurred numbers or chart states the backend did not actually send.

### Premium Ambient Styling Rules

When a signed-in user holds active premium access, the product should communicate that status through ambient quality cues, not badges or promotional elements.

**Header:**

- Display the word `Premium` near the account email in brand purple, Space Grotesk display typeface, small scale. This is the only explicit premium label in the UI.

**Premium-unlocked sections (analyst, dashboard):**

- Add a thin 2px left border or top accent line in brand purple on the section card. This signals premium content without altering the design language.
- The section renders at full content density. The additional visual presence of more content is itself the premium signal.
- Do not add per-section `Premium` badges, lock/unlock icons, or celebratory transitions.

**What to avoid:**

- No gold or separate premium color palette. The existing brand purple serves as the sole premium accent.
- No confetti, glow, gradient, or unlock animations.
- No layout divergence between free and premium profile pages. The page structure is identical; premium sections simply have content instead of blur.

**Upgrade moment:**

- After checkout reconciliation, show one explicit confirmation moment: route or scroll the user to the unlocked section and briefly highlight it once.
- After that one-time reveal, return to the ambient premium styling rules above. The steady-state experience stays quiet.

### Engagement-First Conversion Model

The premium boundary should sit at the transition from consuming facts to understanding what they mean. Civitas's genuine USP is interpretation, not data availability.

Expected user research loop before conversion:

1. Search — instant, free, satisfying.
2. First profile — rich and genuinely useful across all free sections.
3. AI overview — free text confirms the tool understands schools, not just data.
4. Analyst section — first 2-3 lines visible and school-specific, then blur. First premium signal.
5. Data sections — Ofsted, demographics, attendance, workforce, performance, neighbourhood all render fully. Trust deepens.
6. Inline benchmark cues — school vs. local vs. national bars visible in free metric cards.
7. Benchmark dashboard drill-down — richer framework and sample content visible, then locked. Second premium signal.
8. Compare — works fully for up to 4 schools. Core workflow completes without paying.
9. Returns to another school — hits analyst blur again. Pattern reinforces.

For the benchmark dashboard specifically, the preview should use visible sample content followed by a lock boundary. Do not interpret this loop as a license to blur fabricated charts.

Conversion typically happens at touchpoint 9 or 10, not at the first boundary. The product must prove trustworthiness before asking for money.

Premium copy must position paid access as deeper interpretation of already-public evidence, not as hidden truth or advice. Civitas must never imply that parents are missing undisclosed facts or that premium is required to research responsibly.

CTA copy must be contextual and school-specific, not generic platform-upgrade language. Examples:

- "Get the full analyst view for [School Name]"
- "See how [School Name] compares across all benchmarks"

Avoid: "Unlock Premium", "Upgrade Now", "Go Premium" or similar generic SaaS phrasing.

Keep CTA generation template-based. The only dynamic inputs should be school name and section type.

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
- Latest benchmark snapshot data embedded in the main profile payload

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
| `premium_school_analyst` | Profile analyst section | user session + requested section capability | `GET /api/v1/schools/{urn}` returns free baseline plus locked analyst section with `teaser_text` (first 2-3 sentences) when absent; full analyst payload when present | Clear teaser text then progressive blur, inline contextual CTA overlay | Profile cache must vary by access state or be invalidated on upgrade and sign-out | First premium launch capability. The first contract migration should replace the current raw `analyst_text` field; keep the free overview field unchanged unless a shared wrapper materially reduces complexity. |
| `premium_benchmark_dashboard` | Dedicated dashboard drill-down from profile or trends surfaces | user session + dashboard capability | `GET /api/v1/schools/{urn}/trends/dashboard` or equivalent returns locked metadata with `teaser_payload` (layout structure plus limited real preview content) when absent; full dashboard when present | Partial real preview with fade or lock boundary, inline contextual CTA overlay | Dashboard and related profile drill-down caches must vary by access state | Second premium launch capability; free inline benchmark cues remain in the main profile payload. The current web benchmark view model must split into free inline snapshot mapping and premium drill-down mapping. |
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
5. Premium-sensitive contracts must distinguish `locked` from `unavailable` or `not_published`.
6. The free profile route must not require the premium benchmark dashboard endpoint for its baseline render path.
7. Any new premium candidate after this document must update this file before implementation starts.
8. Locked premium responses must include a `teaser_text` or `teaser_payload` field so the frontend can render the approved preview treatment. The backend must never send the full premium payload to unauthorized viewers.
9. CTA copy in locked sections must be contextual and school-specific. The backend should include the school name in locked-section metadata so the frontend can render copy like "Get the full analyst view for [School Name]" without deriving it from route params.
10. All user-facing premium copy must use `Premium`, never `Pro`. `Pro` is reserved for a future B2B tier.
11. The premium ambient styling on unlocked sections (thin brand-purple accent border) is a frontend-only concern and does not require backend contract changes. It is driven by the session or access context already available from the auth feature.
12. Phase 10 must split the current web benchmark view-model path: free inline benchmark cues come from the main profile payload, while premium dashboard preview and full drill-down come from the premium-aware dashboard response.
13. The initial contract migration should change the analyst payload first; do not refactor the free overview field unless that reduces total implementation complexity.
14. Premium copy and preview treatment must not imply hidden facts or recommendations. Paid access is deeper interpretation of public evidence, not privileged truth.

## Open Questions

1. Whether the Phase 10 launch bundle should include only the two recommended launch capabilities, or also one compare-plus enhancement if Phase 9 lands early.
2. Whether the dedicated benchmark dashboard should remain one bundled premium capability or later split into profile-dashboard and compare-dashboard capabilities.
3. Whether the AI school analyst launches as the only premium AI artifact at first, or whether a future AI-plus bundle is desirable after launch learning.

## Resolved Decisions

1. **Teaser or partial preview over hide** (2026-03-08): Locked premium sections must prove value with teaser content. Narrative text may use progressive blur; structured benchmark previews should show partial real samples with a fade or lock boundary rather than fully blurred charts.
2. **Premium branding, not Pro** (2026-03-08): The paid tier is `Premium`. `Pro` is reserved for future B2B. All user-facing copy, code identifiers, and design assets must use `Premium`.
3. **Ambient premium styling** (2026-03-08): Premium status is communicated through a quiet header label and thin accent borders on unlocked sections. No badges, gold palettes, gradients, confetti, or unlock animations.
4. **Contextual CTAs** (2026-03-08): Upgrade prompts must be school-specific and action-oriented, not generic platform-upgrade language.
5. **Cache epoch strategy** (2026-03-08): The recommended default for access-aware caching is a session or access epoch included in cache keys for premium-sensitive GET routes. This is documented in `10E`.
6. **Minimal summary contract migration** (2026-03-08): The first premium contract migration should replace the current raw analyst field with a typed premium-aware section wrapper. The free overview field stays unchanged unless a shared wrapper materially simplifies implementation.
7. **Benchmark view-model split** (2026-03-08): The current web benchmark dashboard view model is too coupled to free profile cards. Phase 10 must separate free inline benchmark mapping from premium dashboard drill-down mapping before paywall UI lands.
