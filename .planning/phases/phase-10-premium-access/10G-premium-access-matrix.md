# 10G - Premium Access Matrix

## Document Control

- Status: Current planning baseline for Phase 10
- Last updated: 2026-03-09
- Phase owner: Product + Engineering
- Depends on:
  - `.planning/project-brief.md`
  - `.planning/phases/phase-9-compare/README.md`
  - `.planning/phases/phase-10-premium-access/README.md`

## Purpose

This document is the product source of truth for free versus premium boundaries in Civitas.

Phase 10 should not decide premium behavior ad hoc in API handlers, React components, or payment callbacks. The access model starts here, then `10C`, `10D`, and `10E` implement it.

## Principles

1. The free product must still support a credible Civitas research journey end to end.
2. Premium must add obvious value through deeper interpretation, location context, or higher-intent workflow capability.
3. Premium gating should prefer capability-level or section-level boundaries over whole-app lockouts.
4. Compare entry points should stay visible for free users even when compare access itself is paid.
5. Premium decisions remain backend-owned and contract-driven.
6. Locked premium sections should prove value with teaser content rather than disappear entirely.
7. Premium as an experience should feel ambient and tasteful, not promotional.
8. School favourites are explicitly out of Phase 10 and belong to a later follow-on phase.

## Current Implementation Baseline

- The current school profile contract exposes `overview_text` and `analyst_text` as plain nullable strings end to end. That means the analyst surface currently conflates `not published` with `not allowed yet`.
- The current school profile contract exposes `area_context` directly as a free baseline payload. It has no `locked` or teaser response mode yet.
- The current compare route assumes compare is fully available once the user reaches it. It has no locked route state yet.
- The current app-shell session model carries authentication only. It does not yet expose premium status, capability keys, or an access epoch for cache invalidation.

## Premium Branding Rules

- The paid tier is called `Premium`. All user-facing copy, route names, and CTA labels must use `Premium`.
- `Pro` is reserved for a future B2B tier. Do not use `Pro` in Phase 10 copy, code identifiers, or design assets.
- The header account indicator for a premium user should read `Premium` in brand purple at small scale. It is status, not advertising.
- Do not introduce gold, gradient, or badge-style premium indicators.

## Access Vocabulary

- `Free baseline`: available to anonymous users and signed-in users without premium.
- `Premium`: available only when the account holds the required premium capability.
- `Signed-in helper`: requires sign-in but is not itself a paid feature.
- `Deferred`: not part of the Phase 10 launch bundle; keep out of scope until a later phase explicitly picks it up.

## Recommended Phase 10 Launch Bundle

Freeze the first premium launch around three premium capabilities:

1. `premium_ai_analyst`
2. `premium_comparison`
3. `premium_neighbourhood`

Rationale:

- This bundle is stronger than a single-section premium story without requiring a net-new saved-workflow feature in the launch window.
- AI analyst is the clearest interpretation-led premium signal.
- Compare is a high-intent workflow feature that users already understand.
- Neighbourhood context adds location-specific value and can be moved back to free later if post-launch learning warrants it.
- Benchmark context is explicitly not part of the Phase 10 premium bundle. Inline benchmark cues and the benchmark dashboard drill-down remain free.

## Launch Surface Clarifications

### Compare Scope

- Compare entry points remain visible from search, profile, and results surfaces.
- Free viewers should see a locked action or teaser modal rather than a missing compare affordance.
- The compare route itself must still be protected server-side. A direct visit by a free user should render a locked state, not a broken route.

### Neighbourhood Scope

- `premium_neighbourhood` covers the profile section that bundles deprivation, crime, and house-price context.
- This capability should be modelled as one section boundary for launch, not three independent gates.
- If product later decides neighbourhood context should move back to the free baseline, the change should be a policy simplification rather than a schema redesign.

### Premium Section State Rules

- Premium-sensitive sections must distinguish `locked` from `unavailable`, `not_published`, or `unsupported`.
- A free user hitting a premium boundary should see a teaser or upgrade prompt, not the same state used when no premium artefact exists yet.
- This rule applies immediately to the profile analyst section, the neighbourhood section, and the compare route or compare action state.

### Premium Display Treatment Rules

Locked premium sections must use teaser or partial-preview treatment rather than hiding content or showing empty upgrade prompts. The goal is to prove value exists behind the boundary so the user can see the premium content is real, school-specific, and worth paying for without making the experience feel manipulative.

Preview mechanics:

- Narrative premium text may use a progressive CSS gradient mask: content transitions from fully clear to fully blurred over approximately 60px, then remains fully blurred for the rest of the section.
- The neighbourhood section may use a teaser line plus blurred body treatment, but it must not render fabricated deprivation, crime, or house-price values the backend did not actually send.
- Compare is a workflow action, not a blur section. Keep the action visible with a lock state and contextual teaser modal.
- The preview treatment is a frontend-only presentation concern. The backend does not send the full premium payload to unauthorized viewers.

Per-surface teaser depth:

| Surface | Teaser content returned by backend | Display treatment | CTA copy pattern |
|---|---|---|---|
| AI analyst summary | First 2-3 sentences of the analyst text | Clear teaser text, then progressive blur over remaining placeholder content, inline CTA overlay | "Get the full analyst view for [School Name]" |
| Neighbourhood context | Short teaser line or minimal teaser payload describing available local context | Visible teaser line, then blur or fade treatment with inline CTA overlay | "See the full neighbourhood context for [School Name]" |
| Compare workflow | Locked action metadata plus requested school context for direct-route locked state | Disabled or locked action with teaser modal, or locked route state if navigated directly | "Compare [School Name] side by side with Premium" |
| Deferred favourites | None | Hidden until Phase 13 | Not applicable |

What must never be blurred or hidden:

- section titles and headers
- completeness notices
- surrounding free baseline content
- the existence of premium sections
- fabricated values or charts the backend never sent

## Premium Ambient Styling Rules

When a signed-in user holds active premium access, the product should communicate that status through ambient quality cues, not badges or promotional elements.

Header:

- Display the word `Premium` near the account email in brand purple at small scale. This is the only explicit premium label in the steady-state UI.

Premium-unlocked sections:

- Add a thin accent border in brand purple on analyst and neighbourhood cards.
- Do not add per-section `Premium` badges, lock or unlock icons, or celebratory transitions.

Compare actions:

- Free state: visible locked compare action with lock icon and teaser modal.
- Premium state: normal enabled compare action without extra premium ornamentation.

## Engagement-First Conversion Model

The premium boundary should sit at the transition from consuming facts to either interpreting them or acting on them.

Expected user loop before conversion:

1. Search - instant, free, satisfying.
2. First profile - rich and genuinely useful across free sections.
3. AI overview - free text confirms the product understands schools, not just data.
4. AI analyst - first 2-3 lines visible, then blur. First premium signal.
5. Core data sections - Ofsted, demographics, attendance, workforce, performance all render fully. Trust deepens.
6. Neighbourhood context - teaser line and locked section. Second premium signal.
7. Compare action - visible but locked. Third premium signal.

Premium copy must position paid access as deeper interpretation and workflow support around public evidence, not as hidden truth or advice.

## Product Access Matrix

| Surface | Section or feature | Free tier | Premium tier | Launch classification | Capability key | Phase dependency | Notes |
|---|---|---|---|---|---|---|---|
| Search | Postcode search form and radius selection | Full access | Full access | Free baseline | - | Phase 0 | Core discovery must remain open. |
| Search | Result list, map markers, and school cards | Full access | Full access | Free baseline | - | Phase 0 | Includes core school identity and headline signals. |
| Search | Baseline sort and filter controls | Full access | Full access | Free baseline | - | Phase 0 and Phase 5 | Search must stay genuinely usable for non-paying users. |
| Profile | Profile header and school identity | Full access | Full access | Free baseline | - | Phase 1 | Core route framing and context stay free. |
| Profile | AI school overview | Full access | Full access | Free baseline | - | Phase 8 | Overview supports discovery and should stay public. |
| Profile | AI school analyst summary | Locked teaser or paywall panel | Full access | Premium | `premium_ai_analyst` | Phase 8 and Phase 10 | Strongest premium differentiator. |
| Profile | Ofsted latest judgement and inspection timeline | Full access | Full access | Free baseline | - | Phase 1 and Phase 2 | Official source-backed signal should remain free. |
| Profile | Demographics and core trend signals | Full access | Full access | Free baseline | - | Phase 1, Phase 4, and Phase 6 | Keep raw demographic context in the free product. |
| Profile | Attendance and behaviour sections | Full access | Full access | Free baseline | - | Phase 6 | Core factual evidence stays free. |
| Profile | Workforce and leadership sections | Full access | Full access | Free baseline | - | Phase 6 | Keep core staff context free. |
| Profile | Academic performance section | Full access | Full access | Free baseline | - | Phase 6 | Core academic performance remains a free product pillar. |
| Profile | Neighbourhood and area context | Locked teaser or paywall panel | Full access | Premium | `premium_neighbourhood` | Phase 2, Phase 6, and Phase 10 | Premium launch bundles local deprivation, crime, and house-price context into one section. |
| Profile | Dedicated benchmark dashboard drill-down | Full access | Full access | Free baseline | - | Phase 6 | Not part of the Phase 10 premium hook. |
| Profile | Completeness and unsupported-metric notices | Full access | Full access | Free baseline | - | Phase 3 and Phase 4 | Never hide data limitations behind premium. |
| Compare | Compare entry points from search or profile | Visible locked action | Full access | Premium | `premium_comparison` | Phase 9 and Phase 10 | Free users should still see the compare affordance. |
| Compare | Compare route and side-by-side table | Locked route state or upgrade prompt | Full access | Premium | `premium_comparison` | Phase 9 and Phase 10 | Compare is a paid workflow in the launch bundle. |
| Trends | Inline trend sparks and small trend summaries inside the profile | Full access | Full access | Free baseline | - | Current product | Keep lightweight trend direction in the free product. |
| Trends | Dedicated cross-domain benchmark dashboard route | Full access | Full access | Free baseline | - | Phase 6 | Keep benchmark drill-down free in the Phase 10 launch cut. |
| Account | Sign-in, sign-out, and session state | Sign-in prompt only | Full access | Signed-in helper | - | Phase 10 | Required to purchase and manage premium. |
| Account | Upgrade CTA and plan explanation | Full access | Full access | Free baseline | - | Phase 10 | Paywall explanation should be visible wherever relevant. |
| Account | Current plan or access-status page | Sign-in required | Full access | Signed-in helper | - | Phase 10 | Useful for support and purchase recovery. |
| Billing | Hosted checkout start flow | Sign-in required | Full access | Signed-in helper | - | Phase 10 | Not a paid feature itself; it is the purchase path. |
| Saved workflow | School favourites and saved research library | Not available | Full access when implemented | Deferred | `premium_favourites` | Phase 13 | Explicitly deferred out of the Phase 10 launch bundle. |
| Export | PDF or report export | Not available | Full access when implemented | Deferred | `premium_report_export` | Phase 20 | Already outside MVP scope. |

## Launch Scope Decision Summary

### Freeze As Free Baseline

- Search and map discovery
- Full school profile across identity, Ofsted, demographics, attendance, behaviour, workforce, performance, and benchmark context
- AI school overview
- Benchmark context in both forms:
  - inline benchmark cues in the main profile
  - the dedicated benchmark dashboard drill-down
- Baseline trends

### Freeze As Premium In Phase 10

- AI school analyst summary
- Compare workflow
- Neighbourhood and area context

### Explicitly Defer

- School favourites and saved research workflows
- Advanced search tools
- Report export
- Broader premium AI bundles beyond the analyst view

## Technical Capability Matrix

| Capability key | Covered surfaces | Backend decision input | API contract behavior | Web behavior | Cache implications | Notes |
|---|---|---|---|---|---|---|
| `premium_ai_analyst` | Profile analyst section | user session + requested section capability | `GET /api/v1/schools/{urn}` returns free baseline plus locked analyst section with `teaser_text` when absent; full analyst payload when present | Clear teaser text then progressive blur, inline contextual CTA overlay | Profile cache must vary by access state or be invalidated on upgrade and sign-out | First launch capability. |
| `premium_neighbourhood` | Profile neighbourhood section | user session + requested section capability | `GET /api/v1/schools/{urn}` returns a locked neighbourhood section with teaser metadata when absent; full area-context payload when present | Visible teaser line, then blur or fade treatment with inline CTA overlay | Profile cache must vary by access state or be invalidated on upgrade and sign-out | Launch capability designed so policy can later move neighbourhood back to free without redesign. |
| `premium_comparison` | Compare entry points and compare route | user session + compare capability | Compare endpoint returns locked metadata plus requested school context when absent; full compare payload when present | Visible locked compare action and teaser modal, plus locked direct-route state | Compare cache must vary by access state | Launch workflow capability. |
| `premium_favourites` | Future favourites and saved-library flows | user session + favourites capability | Future save or library endpoints expose locked metadata until enabled | Visible save affordance or library CTA once implemented | Per-user cache and state only | Deferred to Phase 13. |
| `premium_report_export` | Future export endpoints | user session + export capability | Export endpoints reject or return paywall metadata when absent | Export CTA locked until premium is active | Minimal cache impact; authorization check on mutation path | Phase 20 candidate. |

## Implementation Rules Derived From This Matrix

1. `10C` must model premium products as bundles of named capabilities, not as one-off route flags.
2. `10D` should sell one launch premium product that grants all three launch capabilities by default.
3. `10E` should treat locked premium sections and compare locks as first-class response states rather than generic HTTP authorization failures on public read routes.
4. The free profile response must remain complete enough that Civitas is still useful without premium.
5. Premium-sensitive contracts must distinguish `locked` from `unavailable` or `not_published`.
6. Compare entry points should remain visible even when locked.
7. Any new premium candidate after this document must update this file before implementation starts.
8. Locked premium responses must include teaser metadata and the school name so the frontend can render contextual CTAs.
9. All user-facing premium copy must use `Premium`, never `Pro`.
10. Favourites are explicitly out of Phase 10 and belong to the dedicated follow-on phase.

## Open Questions

1. Whether neighbourhood context should remain premium after launch learning or move back into the free baseline.
2. Whether the compare teaser experience should default to an inline locked card, a modal, or both.
3. Whether a later launch should expand Premium again with favourites after Phase 13 is designed.

## Resolved Decisions

1. **Premium branding, not Pro** (2026-03-08): The paid tier is `Premium`. `Pro` is reserved for future B2B. All user-facing copy, code identifiers, and design assets must use `Premium`.
2. **Visible compare affordance** (2026-03-09): Compare stays visibly present in free journeys even though the compare workflow itself is premium.
3. **Neighbourhood is premium for launch** (2026-03-09): Local deprivation, crime, and house-price context move behind one premium section boundary for the first launch cut.
4. **Favourites deferred** (2026-03-09): School favourites move into a later dedicated phase and are not required for the first premium launch.
5. **Ambient premium styling** (2026-03-08): Premium status is communicated through a quiet header label and thin accent borders on unlocked sections. No badges, gold palettes, gradients, confetti, or unlock animations.
