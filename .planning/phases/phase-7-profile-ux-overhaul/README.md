# Phase 7 Design Index - School Profile Parent-First UX Overhaul

## Document Control

- Status: Extended — P13 complete (2026-03-10)
- Last updated: 2026-03-10
- Phase owner: Product + Design (UX direction: Liora Voss)
- Source phase: `.planning/phased-delivery.md`
- Detailed brief: `.planning/ux-overhaul/README.md`

## Brief

The school profile page was built engineer-first — one section per data domain, all metrics equal weight, benchmark data isolated in a separate section below everything else. The target user is a **parent making a school choice**, not an analyst. They need to answer three questions quickly:

1. **Is this school good?** — A clear signal, not 40 equal-weight cards.
2. **Good compared to what?** — Local and national benchmarks inline with each metric, not buried at the bottom.
3. **Getting better or worse?** — Trend direction matters as much as the current value.

This phase redesigns the school profile around that parent mental model.

## Scope

This phase covers only the school profile route (`/schools/:urn`). If the design system changes land cleanly, the same patterns will be applied to the compare route (Phase 9) and any future routes.

## What Is Not Changing

- ~~The brand and colour system — navy/purple palette stays.~~ **Superseded by P9** — brand colour migrated from purple to teal (#00D4C8); font migrated from Space Grotesk + Public Sans to Inter. See P9 doc.
- All existing API contracts — data is already available; no backend changes needed.
- TypeScript interfaces — extended only, never broken.

## Architecture View

```
StatCard (apps/web/src/components/ui/stat-card.tsx)  ← canonical (P10)
  variants: default | hero | mini
  size: sm | md | lg
  trendDirection: "up" | "down" | null  ← inline ▲/▼ (P11)
  └── BenchmarkBlock (internal)
        └── BarRow — proportional bars (school / local / national)
                     h-2 mobile / h-[5px] sm+, visible at all breakpoints

TrendIndicator (apps/web/src/components/data/TrendIndicator.tsx)  ← (P11)
  ▲/▼ triangles always text-brand (teal) — never red, never conditional
  Flat: — in text-disabled
  Delta shown as absolute value; triangle conveys direction

apps/web/src/components/data/StatCard.tsx  ← re-export shim only (P10)

Section components (import via shim — no changes needed)
  ├── AcademicPerformanceSection  → "Results & Progress"
  ├── AttendanceBehaviourSection  → "Day-to-Day at School"
  ├── WorkforceLeadershipSection  → "Teachers & Staff"
  └── DemographicsAndTrendsPanel  → "Pupil Demographics"  ← benchmarks added P12
  each accepts: benchmarkDashboard: BenchmarkDashboardVM | null
  each builds:  Map<metricKey, BenchmarkMetricVM> → BenchmarkSlot

NeighbourhoodSection (imports from ui/stat-card directly)
  └── variant="mini" size="sm" StatCards inside bordered containers
      (eliminates double-padding that caused desktop overflow)

SchoolProfileFeature
  └── BenchmarkComparisonSection removed (data inline with each section)
```

## Deliverables

| ID | File | Status |
|----|------|--------|
| P1 | `P1-design-tokens-benchmark-colours.md` | Completed |
| P2 | `P2-stat-card-visual-redesign.md` | Completed |
| P3 | `P3-benchmark-wiring-sections.md` | Completed |
| P4 | `P4-section-narrative-copy.md` | Completed |
| P5 | `P5-responsive-mobile-polish.md` | Superseded by P9 |
| P6 | `P6-design-system-documentation.md` | Partially complete — `apps/web/README.md` updated (2026-03-09) |
| P7 | `P7-school-data-page-redesign-v2.md` | Completed (local, 2026-03-08) |
| P8 | `P8-school-data-page-redesign-v3.md` | Completed (local, 2026-03-08) |
| P9 | `P9-loira-voss-design-refresh.md` | Complete — superseded by P10 for StatCard |
| P10 | `P10-statcard-shadcn-standardisation.md` | Complete (2026-03-09) |
| P11 | `P11-trend-indicator-direction-triangles.md` | Complete (2026-03-10) |
| P12 | Demographics benchmark wiring | Complete (2026-03-10) |
| P13 | Compare page rebuild | Complete (2026-03-10) |
| P13.1 | Compare accordion refactor | Complete (2026-03-10) |
| P13.2 | Compare visual polish | Complete (2026-03-10) |
| P13.3 | Compare row readability | Complete (2026-03-10) |
| P13.4 | Compare strip-to-table alignment | Complete (2026-03-10) |
| P13.5 | Fixed 4-slot layout with ghost cards | Complete (2026-03-10) |
| P13.6 | Accordion header visual hierarchy | Complete (2026-03-10) |
| P13.7 | Accordion header background tint | Complete (2026-03-10) |
| P13.8 | Mobile-first accordion content | Complete (2026-03-10) |
| P13.9 | Section heading alignment with profile | Complete (2026-03-10) |
| P14 | Profile action bar redesign | Complete (2026-03-10) |
| P14.1 | Button animation standardisation | Complete (2026-03-10) |
| P14.2 | Site-wide button variant standardisation | Complete (2026-03-10) |

## Execution Sequence

1. **P1 first** — tokens must exist before any component references them.
2. **P2** — StatCard visual redesign; all other work depends on the new interface.
3. **P3** — Wire benchmark data into section components (no visual impact until P2 lands).
4. **P4** — Section copy/labels; safe to do alongside P2/P3.
5. **P5** — Responsive audit after P2–P4 are stable.
6. **P6** — Documentation after everything is signed off.

## Dependencies

- **Phase 5** (`phase-5-ux-uplift`) — design token system and component primitives must be in place.
- **Phase 6** (`phase-6-metrics-parity`) — `BenchmarkDashboardVM` and all benchmark metric data must be live in the API before wiring is testable end-to-end.
- No new backend work required — all data already returned in `GET /api/v1/schools/{urn}`.

## Definition of Done

- Every metric card (attendance, behaviour, workforce, performance, demographics) shows the school's value, trend sparkline, trend delta, and inline benchmark bars for local and England.
- `BenchmarkComparisonSection` standalone section is removed from the profile render.
- Section titles use parent-language headings, not DfE category names.
- Benchmark bars show correct proportional widths on tablet/desktop; compact text fallback on mobile (< 640px).
- No horizontal overflow at 375px (iPhone SE).
- No TypeScript errors; lint passes.
- Rollback available per deliverable via `git checkout -- <file>`.

## Tracking Log

- 2026-03-10 (P14.2 — Site-wide button variant standardisation):
  - **`SchoolProfileFeature.tsx`** — all four `variant="compare" size="none"` button call sites replaced with `variant="primary" size="default"`: header "Add to compare" button, header `CompareActionButton` ("Open compare"), mobile sticky bar compare toggle, and mobile sticky bar `CompareActionButton`. "Remove from compare" remains `variant="secondary"` (correct for secondary action). Manual `text-sm` removed from mobile bar (redundant — included in `size="default"`). Manual `px-4` removed from mobile `CompareActionButton` (included in `size="default"`).
  - **`apps/web/README.md`** — new "Button system" section added documenting all four variants, sizes, animation base, and rules (no raw buttons for actions, no inline animation overrides, variant assignments for profile header states).
  - **Audit result**: Compare page buttons (Share/Back/Clear all/Browse) already use correct standard variants (`secondary`/`ghost`/`primary`). `SaveSchoolButton` uses `secondary`/`ghost` correctly. `CompareActionButton` passes through variant prop correctly. No manual animation overrides found anywhere.

- 2026-03-10 (P14.1 — Button animation standardisation):
  - **`Button.tsx`** — base `cva` string standardised from `transition-colors duration-base` to `transition-all duration-200 ease-out hover:scale-[1.02] active:scale-[0.98]`. All variants (primary, secondary, ghost, compare) now inherit unified micro-animation.
  - **`Button.tsx` compare variant** — replaced `"btn-compare focus-visible:ring-0"` class reference with Tailwind-only: `rounded-xl border border-brand/25 bg-[rgba(10,20,40,0.65)] text-primary/90 backdrop-blur-sm hover:border-brand/50 hover:bg-brand/10 hover:text-primary hover:shadow-[0_0_18px_rgba(0,212,200,0.25)]`. No external CSS dependency.
  - **`tokens.css`** — deleted ~100-line `.btn-compare` CSS block (base styles, `::before` gradient border ring pseudo-element, hover/active/focus-visible states, light theme overrides). All styling now lives in `cva` variant.
  - **`ui-primitives.test.tsx`** — compare variant assertion updated from `btn-compare` class check to `rounded-xl` + `border-brand/25`.

- 2026-03-10 (P14 — Profile action bar redesign):
  - **`SchoolProfileFeature.tsx`** — extracted `handleCompareToggle` callback to deduplicate compare add/remove logic (was copy-pasted in header actions + mobile sticky bar). Header actions now context-aware: when not in compare → teal "Add to compare (N/4)" primary + "Save for later" secondary; when in compare → outline "Remove from compare" + teal "Open compare (N)". Mobile sticky bar mirrors the same two-button layout with `flex gap-2`.
  - **`SaveSchoolButton.tsx`** — icon changed from `Bookmark` to `Heart` (filled when saved). Label changed from "Save" to "Save for later". Added hover tooltip: "Save to your list for alerts, exports & easy re-access" (only shown in `not_saved` state, hidden for saved/locked/auth states).
  - **`CompareActionButton.tsx`** — added `className` prop passthrough to all internal `Button` renders.
  - **`ProfileHeader.tsx`** — actions container gap tightened from `gap-3` to `gap-2` for connected-bar feel.
  - **Tests** — `"Save"` → `"Save for later"` in profile + favourites test assertions; `getByRole` → `getAllByRole[0]` for dual mobile+desktop rendering.

- 2026-03-10 (P13.9 — Section heading alignment with profile):
  - **`compareMapper.ts`** — added `SECTION_LABEL_MAP` mapping backend keys to profile-matching labels: `inspection` → "Ofsted Profile", `performance` → "Results & Progress", `attendance`/`behaviour` → "Day-to-Day at School", `demographics` → "Pupil Demographics", `workforce` → "Teachers & Staff", `area` → "Neighbourhood Context". Added `SECTION_ORDER` for canonical profile order. New `relabelMergeAndOrder()` merges sections sharing the same label (attendance + behaviour → "Day-to-Day at School") and sorts by profile order.
  - **`school-compare.test.tsx`** — assertions updated for dual mobile+desktop rendering (`getByText` → `getAllByText[0]`) and renamed section labels (`"Demographics"` → `"Pupil Demographics"`).

- 2026-03-10 (P13.8 — Mobile-first accordion content):
  - **`CompareMobileContent.tsx`** (new) — mobile-only vertical card layout for `< sm` (640px). Each metric row renders as: teal-accented metric label header → stacked school value cards. Origin school gets `border-l-2 border-l-brand/30` tint. Muted cells use `text-disabled/50` (lighter than desktop). Detail labels suppressed on mobile to reduce density.
  - **`CompareAccordionContent.tsx`** — wraps desktop table in `hidden sm:block`, renders `CompareMobileContent` in `sm:hidden`. Desktop table unchanged.
  - **`CompareSchoolStrip.tsx`** — mobile: 2×2 grid layout (`grid grid-cols-2 gap-2`), desktop: unchanged horizontal strip. Remove button touch target increased to `p-1.5` on mobile. Ghost card min-height `60px` mobile / `72px` desktop.
  - **`compareMapper.ts`** — suppressed `partial_metric_coverage` completeness label at cell level (section-level noise).
  - Removed "Metric" label from table header and URN numbers from strip cards and table headers.

- 2026-03-10 (P13.7 — Accordion header background tint):
  - **`CompareAccordionSections.tsx`** — header background changed from `bg-surface/70` to `bg-brand/[0.04]` for a subtle teal-tinted glass effect. Differentiates headers from content panel (`bg-surface/40`) while staying on-brand. All other styling unchanged.

- 2026-03-10 (P13.6 — Accordion header visual hierarchy):
  - **`CompareAccordionSections.tsx`** — accent bar strengthened from `border-l-brand/60` to `border-l-brand` (full opacity teal). Header font bumped from `text-sm` to `text-base` for clearer visual hierarchy. Padding, metric count badge styling, hover/open states unchanged.

- 2026-03-10 (P13.5 — Fixed 4-slot layout with ghost cards):
  - **`CompareSchoolStrip.tsx`** — now exports `CompareSlot` type (`CompareSchoolColumnVM | null`) and `padToSlots()` helper. Always renders 4 fixed slots: `FilledCard` for real schools, `GhostCard` (dashed border, `+ Add school` link to home) for empty slots. Props changed from `schools` to `slots`.
  - **`CompareAccordionContent.tsx`** — accepts `slots: CompareSlot[]` instead of `schools`. Fixed `minWidth` to `LABEL_COL_WIDTH + TOTAL_SLOTS * SCHOOL_COL_WIDTH` (always 4 columns). Empty slots render blank `<th>`/`<td>` cells with subtle zebra tint `bg-surface/[0.04]`.
  - **`CompareAccordionSections.tsx`** — prop changed from `schools` to `slots: CompareSlot[]`, passed through to `CompareAccordionContent`.
  - **`SchoolCompareFeature.tsx`** — imports `padToSlots`, creates `paddedSlots` memo, passes to both `CompareSchoolStrip` and `CompareAccordionSections`.
  - **`school-compare.test.tsx`** — fixed "Not applicable" assertion to match em-dash prefixed muted cell text (`— Not applicable`).

- 2026-03-10 (P13.4 — Compare strip-to-table alignment):
  - **`CompareSchoolStrip.tsx`** — rewritten for column alignment. Uses same 200px label spacer + 180px school columns as accordion table. Cards compacted: `p-2` padding, `text-xs` name, `text-[9px]` badges/URN with `px-1 py-0` and `h-2.5 w-2.5` icons. Age range + distance collapsed to inline `text-[9px]` text (removed `StatCard` mini). Remove button shrunk to `p-0.5` + `h-3 w-3`. School name truncated with `truncate`.
  - Removed `StatCard` import — no longer used in strip.

- 2026-03-10 (P13.3 — Compare row readability polish):
  - **`CompareAccordionContent.tsx`** — removed "Origin" badge from first school column header. Added zebra striping: even rows `bg-surface/[0.06]` (cells) / `bg-surface/[0.08]` (sticky label). Row hover changed from `hover:bg-brand/[0.03]` to `hover:bg-surface/50` for better cross-column tracking. Row dividers strengthened from `border-border-subtle/15` to `/25`. Origin column tint retained without badge.

- 2026-03-10 (P13.2 — Compare visual polish):
  - **`CompareAccordionSections.tsx`** — teal left accent bar (`border-l-2 border-l-brand/60`) on accordion headers, increased padding (`px-5 py-3.5`), `p-1` inner padding on content panel. Hover intensifies accent. Passes `originUrn` through to content.
  - **`CompareAccordionContent.tsx`** — "This school" column highlight: origin URN gets `border-l-2 border-l-brand/30 bg-brand/[0.02]` on every cell + header. Softer unavailable: muted cells use `text-disabled/60` with em-dash prefix, detail labels `text-disabled/70`. Increased row padding `py-3.5`, softer dividers `border-border-subtle/15`. Lighter availability tinting: `unsupported` → `bg-surface/30`, `unavailable` → `bg-surface/20`. Header row gets bottom border for separation.
  - **`SchoolCompareFeature.tsx`** — passes `originUrn={effectiveUrns?.[0]}` to `CompareAccordionSections`.
  - **`apps/web/README.md`** — added "This school" highlight, unavailable treatment, and visual polish docs.

- 2026-03-10 (P13.1 — Compare accordion refactor):
  - **`CompareAccordionSections.tsx`** (new) — replaces flat table with collapsible accordion per section. First 3 sections default open, rest collapsed. Toggle button styled as `rounded-xl bg-surface/70` with chevron, teal accent bar, and metric count badge. No external dependency — pure React state.
  - **`CompareAccordionContent.tsx`** (new) — metric rows inside each accordion. Sticky label column (`left-0 z-10 bg-surface/95 backdrop-blur`), school value cells with availability tinting, `overflow-x-auto` for horizontal scroll. Extracted `CompareCell`, `cellBgClass`, `unitLabel` from old `CompareMetricTable`.
  - **`SchoolCompareFeature.tsx`** — swapped `CompareMetricTable` import for `CompareAccordionSections`. All state/reducer/URL logic unchanged.
  - **`CompareMetricTable.tsx`** — superseded by accordion layout (kept in repo for reference; no longer imported).
  - **`CompareTableHeader.tsx`** — superseded; header now inline in `CompareAccordionContent`.
  - **`school-compare.test.tsx`** — updated table query to `getAllByRole("table")` (one table per open accordion section).
  - **`apps/web/README.md`** — updated P13 section to P13.1 with accordion pattern docs.

- 2026-03-10 (Phase 14 compat fix):
  - **`favourites/mappers.ts`** — `mapSavedSchoolState()` now accepts `undefined | null` and returns a default `not_saved` state. Phase 14 added `saved_state` to search result types but the backend doesn't always include it; calling the mapper on `undefined` crashed the search page with `Cannot read properties of undefined (reading 'status')`.

- 2026-03-10 (P13 — Compare page rebuild):
  - **`SchoolCompareFeature.tsx`** — full rewrite. Extracted inline components into dedicated files. Slim header with share button (clipboard copy). Premium gate replaced with compact `ComparePremiumBanner` (slim Panel). Dev premium bypass extracted to `isDevUnlocked` boolean. Section matrix replaced with `CompareMetricTable`.
  - **`CompareSchoolStrip.tsx`** (new) — horizontal scrollable school cards with `snap-x snap-mandatory`, badges (phase/type/postcode), `StatCard variant="mini"` for age range and distance, `X` remove button.
  - **`CompareMetricTable.tsx`** (new) — core comparison grid. Sections separated by teal-accented centred dividers (`bg-brand/20` rules). Sticky metric label column (`left-0 z-10 bg-surface/95 backdrop-blur`). Row hover `bg-brand/[0.03]`. Cell availability tinting. Unit labels in Title Case at `text-[10px]`.
  - **`CompareTableHeader.tsx`** (new) — sticky header row with school names and URN links.
  - **`apps/web/README.md`** — added Compare page design system section (P13).

- 2026-03-10 (P11.1 — StatCard Title Case migration):
  - **`stat-card.tsx`** — removed `uppercase tracking-[0.08em]` from label `<span>`, replaced with `tracking-[0.04em]`. Labels now render in their natural Title Case from `metricCatalog.ts` (e.g. "Free School Meals", "English as Additional Language") instead of ALL CAPS. No section component changes needed — source strings were already Title Case.
  - **`apps/web/README.md`** — added "Title case rule" to StatCard design system section.

- 2026-03-11 (P12.1 — Benchmark delta neutrality):
  - **`stat-card.tsx`** — removed conditional teal/red colouring (`deltaColorClass`) from regional/national benchmark delta values; all deltas now render in neutral gray (`#94A3B8`). "This school" bar stays teal. Facts-only Loira Voss style.

- 2026-03-10 (P12 — Demographics benchmark wiring):
  - **`DemographicsAndTrendsPanel.tsx`** — added `benchmarkDashboard: BenchmarkDashboardVM | null` prop; added `barDecimals` / `toBenchmarkSlot` helpers (same pattern as Workforce/Academic sections); builds `benchmarkLookup` Map; passes `benchmark={bm ? toBenchmarkSlot(bm) : undefined}` to each demographics `StatCard`. Now shows school/local/national comparison bars for all demographics metrics (FSM, EAL, SEN, EHCP, etc.) where benchmark data is available.
  - **`SchoolProfileFeature.tsx`** — added `benchmarkDashboard={profile.benchmarkDashboard}` to `<DemographicsAndTrendsPanel>` call site.
  - Note: `"demographics"` section already existed in `METRIC_SECTION_ORDER` / metric catalog and `buildBenchmarkDashboard` already bucketed demographics metrics — this was purely a frontend wiring gap.

- 2026-03-10 (P11 — direction-only trend indicators + alignment fix):
  - **`TrendIndicator.tsx`** — replaced `TrendingUp`/`TrendingDown` lucide icons with ▲/▼ unicode triangles. Both always `text-brand` (teal `#00D4C8`). Flat → `—` in `text-disabled`. Removed `+` prefix and conditional colour logic. Delta rendered as absolute value. Added `whitespace-nowrap shrink-0` — triangle is now always inline-prefixed to the number, never detaches to its own line.
  - **Footer layout** — all four section `renderTrendFooter` functions changed from horizontal `flex justify-between` to vertical `space-y-1.5`: sparkline full-width on top (`className="w-full"`), delta row below. Fixes sparkline collapsing to zero in narrow cards. Period labels shortened to `X-yr trend` format.
  - **`stat-card.tsx` label min-height** — label container gets `min-h-[40px]` so values align horizontally across all cards in a grid row regardless of title wrapping length.
  - **`TrendIndicator.tsx`** two-line format: `▼ 1.2%` (triangle + value, `whitespace-nowrap`) on line 1; period label (`3-yr trend`) on line 2 in `text-disabled`. `flex-col` outer span.
  - **`stat-card.tsx`** — new `trendDirection?: "up" | "down" | null` prop renders ▲/▼ inline *before* the value in `text-brand`. Use when direction triangle is wanted without a delta number. Existing `footer`+`TrendIndicator` pattern unchanged for sparkline+delta use cases.
  - **`apps/web/README.md`** — new `### Trend indicators (P11)` section + `trendDirection` prop doc + inline alignment rule added.
  - **Root `README.md`** — `TrendIndicator` added to component inventory table.
  - **`P11-trend-indicator-direction-triangles.md`** planning doc created.

- 2026-03-10 (P10 — Area Crime card redesign, `NeighbourhoodSection.tsx`):
  - **Period label**: `Latest {month}` → `12 months to {month}` — unambiguous rolling window
  - **Headline stat block**: danger-tinted container (`border-danger/30 bg-danger/5`); values plain white (`text-primary`)
  - **Sparkline container**: matching danger tint (`border-danger/20 bg-danger/5`); label `text-danger/70`
  - **Category rows**: each row gains a proportion bar (`h-1`, `bg-danger/50` fill scaled to % of total incidents) — dominant categories immediately visible at a glance; counts plain white
  - All crime numbers settled on `text-primary` (white) after reviewing teal and danger variants — consistent with all other section stats; danger bars carry the severity signal

- 2026-03-09 (P10 — StatCard shadcn standardisation):
  - **`components/ui/stat-card.tsx`** (new) — canonical shadcn-style primitive with `cva` variants (`default`, `hero`, `mini`) and `size` prop (`sm`/`md`/`lg`). Built-in overflow protection. `tooltip`/`description` info button. `BenchmarkBlock` + `BarRow` internal. Re-exports `BenchmarkSlot` type.
  - **`components/data/StatCard.tsx`** — converted to re-export shim; existing section components unchanged.
  - **`NeighbourhoodSection.tsx`** — migrated from raw `div` blocks to `<StatCard variant="mini" size="sm">`. Double-padding root cause permanently resolved. Domain labels changed from `truncate` to wrapping (`leading-tight`) so long labels like "Living environment" display in full.
  - **`apps/web/README.md`** — StatCard design system rule section (P10) added: variant table, size table, overflow protection spec, tooltip API, shim guidance.
  - **Root `README.md`** — frontend component inventory table added.
  - **`P10-statcard-shadcn-standardisation.md`** planning doc created.

- 2026-03-09 (P9 — Liora Voss design refresh, iteration 3 — mobile density):
  - **Section panel padding**: `p-5 sm:p-6` → `p-4 sm:p-6` across all 8 section components (AcademicPerformance, AttendanceBehaviour, Demographics, Workforce, Neighbourhood, Ofsted, SchoolOverview, SchoolAnalyst).
  - **Section internal rhythm**: `space-y-5/6` → `space-y-4 sm:space-y-5/6` matching padding reduction.
  - **Between-section gap** (`SchoolProfileFeature`): `space-y-8` → `space-y-5 lg:space-y-8`.
  - **Hero metric strip** (`ProfileHeader`): `gap-8 sm:gap-10` → `gap-5 sm:gap-8`.
  - **Accordion chrome** (`ProfileSectionAccordion`): `px-4 py-3` → `px-3 py-2.5 min-h-[44px]` (≥44px touch target preserved).
  - **Bottom guard**: `pb-24` → `pb-20 lg:pb-0`.
  - `SchoolProfileFeature` comment block updated; `apps/web/README.md` mobile density table added.

- 2026-03-09 (P9 — Liora Voss design refresh, iteration 2):
  - `ProfileHeader`: removed decorative UK map SVG watermark (`UKMapWatermark`) added and reverted in same session — hero section is now illustration-free by design rule.
  - `SiteFooter`: both `CIVITAS` occurrences (logo link + copyright line) replaced with `[BRAND]`.
  - `SchoolProfileFeature`: 30-line styling comment block added at top of file; TOC sidebar `top` corrected to `3.75rem` (flush below 56px nav); mobile sticky CTA hardened with `min-h-[52px]` tap target and `env(safe-area-inset-bottom)` iOS safe-area padding.
  - `apps/web/README.md`: new `## School Profile UI` section added covering colour palette, typography, card primitive, mobile/desktop layout rules, brand placeholder locations, and no-illustrations rule.
  - `P9-loira-voss-design-refresh.md` planning doc created.

- 2026-03-09 (P9 — Liora Voss design refresh, iteration 1):
  - **Global token migration** — brand colour `#A855F7` (purple) → `#00D4C8` (teal) across `--ref-color-brand-*` tokens; `--ref-color-navy-900/950/800/700` deepened to match designer spec; `--color-trend-up` set to teal, `--color-trend-down` set to `#FF4D6D` (was both neutral blue).
  - **Font migration** — `@fontsource/inter` installed; `theme.css` imports swapped from Space Grotesk + Public Sans → Inter (400/500/600/700); `--font-family-display` and `--font-family-body` tokens updated.
  - **Hardcoded purple purge** — `btn-compare` border/glow/gradient, panel resize handle, and light-theme overrides all updated to teal in `tokens.css` and `theme.css`.
  - **`SiteHeader`**: `CIVITAS` → `[BRAND]` (display text + aria-label).
  - **`Card`**: `rounded-lg` → `rounded-xl`; hover lift `hover:-translate-y-0.5 hover:shadow-lg transition-all duration-200` added.
  - **`SchoolProfileFeature`**: two-column desktop layout (280px sticky TOC + main content); section IDs for jump-link targets; sections 3–8 wrapped in `ProfileSectionAccordion` (Ofsted + Results open by default, rest closed); mobile sticky "Add to compare" bar added (fixed bottom, `z-nav`, `lg:hidden`); `pb-24` guards content above sticky bar.
  - **`ProfileSectionAccordion`** new component created — zero-dependency React-state accordion; accordion toggles `lg:hidden` so desktop always renders sections in full.
  - Planning doc `P9-loira-voss-design-refresh.md` created.

- 2026-03-08 (Liora Voss design pass — P8, V3 polish, local only):
  - `WorkforceLeadershipSection`: removed `WorkforceMetricCard` helper — catalog null-skip now in `.flatMap()` alongside value null-skip, eliminating ghost-card escape hatch. `StatCard` rendered directly.
  - `LeadershipStrip`: replaced flex-wrap pill strip with single bordered container using `divide-x` CSS dividers. `overflow-x-auto` + `min-w-max` for horizontal scroll on narrow viewports.
  - `SchoolProfileFeature`: added `hover:scale-[1.02] hover:border-brand/60 hover:shadow-[0_0_18px_rgba(168,85,247,0.22)] transition-all duration-200` to "Add to compare" and "Open compare" buttons.
  - Planning doc created: `P8-school-data-page-redesign-v3.md`.

- 2026-03-08 (Liora Voss design pass — P7 in progress, local only):
  - Diagnosed three structural failures: ghost cards, flat hero hierarchy, wrong section order.
  - `MetricGrid`: added `mobileTwo` prop — 2-col mobile layout without breaking existing callers.
  - `StatCard`: bar height 3px → 5px; hero glow `shadow-[0_0_28px_rgba(168,85,247,0.10)]` added.
  - `WorkforceLeadershipSection`: `.flatMap()` null-skip on workforce grid; leadership 2×2 Card replaced with horizontal flex-wrap pill strip — only populated fields render.
  - `AttendanceBehaviourSection`: `.flatMap()` null-skip on attendance + behaviour grids; `mobileTwo` added to both.
  - `DemographicsAndTrendsPanel`: `.flatMap()` null-skip on demographics grid; `mobileTwo` added.
  - `SchoolProfileFeature`: section reorder — Results & Progress moved above Attendance, Demographics, Workforce.
  - Planning doc created: `P7-school-data-page-redesign-v2.md`.
  - Not committed — local test only.

- 2026-03-07 (implementation checkpoint — P1–P4 complete):
  - Completed P1 design token foundation:
    - added `--color-benchmark-school/local/national` tokens to both light and dark theme blocks in `tokens.css`,
    - added `bg-benchmark-school/local/national` Tailwind colour aliases in `tailwind.config.ts`,
    - revised `--color-trend-down` to match `--color-trend-up` (neutral blue) — trend direction is movement, not evaluative.
  - Completed P2 StatCard visual redesign:
    - added `BenchmarkSlot` interface (exported) with `displayDecimals` field for precision-matched bar widths,
    - added `BenchmarkBlock` internal component — proportional bars on sm+, compact text rows on mobile,
    - added `description` prop with ⓘ toggle (not in original spec — emerged from UX review),
    - "This school" row included in benchmark block; "Compared with" heading removed (cleaner),
    - added `period` prop to `TrendIndicator` for trend duration labels (e.g. "+2.1% · 3yr").
  - Completed P3 benchmark wiring:
    - `AcademicPerformanceSection`, `AttendanceBehaviourSection`, `WorkforceLeadershipSection` each accept `benchmarkDashboard` prop,
    - `toBenchmarkSlot()` helper in each section; `displayDecimals` set per unit type via `barDecimals()`,
    - `BenchmarkComparisonSection` deleted (not retained — data is now fully inline with no value in a standalone section),
    - `SchoolProfileFeature` passes `benchmarkDashboard` to all sections; standalone section import removed,
    - `SchoolDetailsSection` also removed from profile render — data not yet complete in current dataset.
  - Completed P4 section narrative copy (extended scope):
    - Section headings: "Results & Progress", "Day-to-Day at School", "Teachers & Staff",
    - Section descriptions rewritten for parents, not analysts,
    - Aria heading IDs updated to match new headings,
    - Full metric label rename pass in `metricCatalog.ts` — EAL, SEN, EHCP, EBacc, KS2, FSM6, supply staff all renamed to plain English,
    - Plain-English `description` added to every metric catalog entry — surfaced via ⓘ toggle on StatCard,
    - `DemographicsAndTrendsPanel` wired with `description` from catalog.
  - Neighbourhood section enhancements (beyond original P4 scope):
    - Area Deprivation card: replaced raw decile stats with plain-English sentence (e.g. "This area is in the bottom 30% of areas in England for deprivation."),
    - Domain tiles redesigned: colour-coded dot + "Decile X / 10" label instead of raw numbers,
    - House Prices sparkline: year range label added (e.g. "2020 – 2024"),
    - District name surfaced as "District: [name]" below the deprivation sentence.

## Change Management

- `.planning/phased-delivery.md` is the high-level source of truth.
- If scope or acceptance criteria evolve, update this `README.md` and `phased-delivery.md` in the same commit.
- The detailed UX brief and progress log lives in `.planning/ux-overhaul/README.md`.
