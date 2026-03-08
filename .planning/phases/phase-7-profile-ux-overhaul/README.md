# Phase 7 Design Index - School Profile Parent-First UX Overhaul

## Document Control

- Status: Completed — committed 2026-03-07
- Last updated: 2026-03-07
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

- The brand and colour system — navy/purple palette stays.
- All existing API contracts — data is already available; no backend changes needed.
- TypeScript interfaces — extended only, never broken.

## Architecture View

```
StatCard (apps/web/src/components/data/StatCard.tsx)
  └── BenchmarkBlock (new internal component)
        ├── BarRow    — sm+ proportional bars (school / local / national)
        └── TextRow   — mobile compact text fallback

Section components
  ├── AcademicPerformanceSection  → "Results & Progress"
  ├── AttendanceBehaviourSection  → "Day-to-Day at School"
  └── WorkforceLeadershipSection  → "Teachers & Staff"
  each accepts: benchmarkDashboard: BenchmarkDashboardVM | null
  each builds:  Map<metricKey, BenchmarkMetricVM> → BenchmarkSlot

SchoolProfileFeature
  └── removes BenchmarkComparisonSection render (data now inline)
```

## Deliverables

| ID | File | Status |
|----|------|--------|
| P1 | `P1-design-tokens-benchmark-colours.md` | Completed |
| P2 | `P2-stat-card-visual-redesign.md` | Completed |
| P3 | `P3-benchmark-wiring-sections.md` | Completed |
| P4 | `P4-section-narrative-copy.md` | Completed |
| P5 | `P5-responsive-mobile-polish.md` | Not started |
| P6 | `P6-design-system-documentation.md` | Not started |
| P7 | `P7-school-data-page-redesign-v2.md` | Completed (local, 2026-03-08) |
| P8 | `P8-school-data-page-redesign-v3.md` | Completed (local, 2026-03-08) |

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

- Every metric card (attendance, behaviour, workforce, performance) shows the school's value, trend sparkline, trend delta, and inline benchmark bars for local and England.
- `BenchmarkComparisonSection` standalone section is removed from the profile render.
- Section titles use parent-language headings, not DfE category names.
- Benchmark bars show correct proportional widths on tablet/desktop; compact text fallback on mobile (< 640px).
- No horizontal overflow at 375px (iPhone SE).
- No TypeScript errors; lint passes.
- Rollback available per deliverable via `git checkout -- <file>`.

## Tracking Log

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
