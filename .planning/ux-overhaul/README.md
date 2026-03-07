# UX Overhaul — School Profile Page

**Status:** Planning
**Started:** 2026-03-06
**Author:** Design brief by Liora Voss (UX direction), implementation by Claude
**Rollback strategy:** All changes are local-only until explicitly committed. `git checkout -- .` restores the baseline at any point.
**Scope:** School profile page first. If approved, the design system and component patterns built here will be rolled out to search results and any future pages.

---

## The Real Brief

This is not a tidying exercise. The primary user is **a parent making one of the most important decisions of their child's life** — which school to choose. They are not a data analyst. They do not know what Progress 8 means. They are probably on a phone, probably stressed, and they need to quickly answer three questions:

1. **Is this school good?** — Not a dashboard of 40 equal-weight numbers. A clear signal.
2. **Good compared to what?** — Local alternatives and national average, not buried as footnotes.
3. **Is it getting better or worse?** — Trend matters. A school that's improving from a bad baseline is a different proposition to one declining from a good one.

**Everything we build must serve those three questions first.**

### What's fixed (brand, not layout)
- Dark navy/purple colour system — it's distinctive and premium, keep it
- No new npm dependencies
- No backend changes — all data already exists in the API
- TypeScript types — extend only, never break existing interfaces
- Every phase leaves the app in a shippable, non-broken state

### What's flexible (almost everything else)
- Layout and information hierarchy — open to significant restructuring
- Component design — StatCard can look completely different if it serves parents better
- Section order and grouping — the current order was developer-logical, not parent-logical
- Which metrics are prominent vs secondary — we decide based on what parents care about
- Visual treatments — charts, bars, indicators — whatever communicates best
- Mobile layout — can differ significantly from desktop if that's the right call

### What we are explicitly NOT preserving
- The current section-per-data-type structure (Ofsted / Demographics / Performance / Benchmark — all separate) — this is a developer model, not a parent model
- The BenchmarkComparisonSection as a standalone section — duplicate of what should be inline
- "Not available" cards — these must be hidden, not rendered as empty noise
- Equal visual weight for all metrics — some things matter far more than others to parents

---

## Parent Mental Model (design north star)

When a parent lands on a school profile page, their internal monologue is:

> *"OK, give me the headline. Outstanding? Good? Is it going in the right direction? How does it compare to the school down the road? What's the FSM rate — I want to understand the intake. How many kids get good grades? What's it actually like day to day — attendance, exclusions? And what's the area like?"*

This maps to a **narrative structure**, not a dashboard:

```
① THE VERDICT           — Ofsted + trend signal + one-line read
② THE SCHOOL AT A GLANCE — 4-5 key metrics with benchmark bars (not 40 equal cards)
③ ACADEMIC PERFORMANCE  — KS4/KS2 with benchmarks + trend
④ PUPIL EXPERIENCE      — Attendance, behaviour — are kids actually showing up?
⑤ WHO GOES HERE         — Demographics + intake context
⑥ THE STAFF             — Workforce/leadership signals
⑦ THE AREA              — Neighbourhood, deprivation, crime, house prices
```

This is a restructuring of the page narrative, not just the card design.

---

## Data Available (confirmed from codebase)

### BenchmarkMetricVM (`types.ts`)
The richest data we have. Each metric carries:
- `schoolValue` — the school's own value
- `nationalValue` — England average
- `localValue` — local area (LA district or phase peers)
- `localAreaLabel` — e.g. "Cheshire East"
- `schoolVsNationalDelta` — signed delta vs England
- `schoolVsLocalDelta` — signed delta vs local
- `trendPoints[]` — historical school + national + local per year (sparkline data for all three lines)
- `unit` — percent / count / ratio / score

### TrendsVM (`types.ts`)
- `series[]` — one per metric key, with per-year `value`, `delta`, `direction`
- `latestDelta`, `latestDirection` — convenience fields

### What this means for the design
We have enough data to show a **three-line sparkline** (school vs local vs national over time) for every benchmarked metric. This is not just a bar chart — it's a trend story. A school that was below national average 5 years ago but is now above it is a fundamentally different school to one doing the reverse.

No new API calls needed for any of this.

---

## Implementation Phases

### Phase 0 — Design Tokens (no visual change)
**Goal:** Establish the benchmark colour tokens so all subsequent phases use consistent values. These go into the CSS custom properties / Tailwind config — not hardcoded in components.

**Proposed tokens:**
```
--color-benchmark-school:   hsl(262 60% 62%)   /* purple — existing brand */
--color-benchmark-local:    hsl(200 80% 55%)   /* cyan */
--color-benchmark-national: hsl(142 60% 48%)   /* green */
```

**Files changed:**
- `apps/web/src/app/globals.css` or equivalent theme file (to verify location)

**Acceptance criteria:**
- [ ] Three new CSS custom properties defined
- [ ] No visual change to any existing component

---

### Phase 1 — StatCard: Redesign with Benchmark Support
**Goal:** Redesign StatCard to be the single component that can express a metric's value, trend, and benchmark context. This is the core building block everything else depends on.

**New anatomy (mobile-first, 375px):**
```
┌──────────────────────────────────────┐
│ LABEL                  [sparkline ~] │  ← 9px label + right-aligned sparkline
│ 41.0%                        ↑ +2pp │  ← 28px value + trend delta
│ ──────────────────────────────────── │  ← hairline divider (only with benchmark)
│ ▓▓▓▓▓▓▓░  This school   41.0%      │  ← purple bar
│ ▓▓▓▓▓▓░░  Cheshire East 40.5%  +0.5│  ← cyan bar + signed delta
│ ▓▓▓▓▓░░░  England       35.8%  +5.2│  ← green bar + signed delta
└──────────────────────────────────────┘
```

**Key decisions:**
- Benchmark block is **opt-in via prop** — existing callers unchanged
- If `benchmark.schoolValue` is null → entire benchmark block hidden (no "Not available")
- Bar scale: fixed 0–100 for `percent` unit; max-of-three for `score`/`ratio`/`count`
- Sparkline moves to top-right corner of the label row (not the footer)
- `footer` prop retained for backwards compatibility but deprecated in favour of the new layout
- Touch target for the card itself remains ≥ 48px height

**New props interface:**
```ts
interface BenchmarkData {
  schoolValue: number | null;
  localValue: number | null;
  localLabel: string;
  nationalValue: number | null;
  schoolVsLocalDelta: number | null;
  schoolVsNationalDelta: number | null;
  unit: MetricUnit;
}

interface StatCardProps extends HTMLAttributes<HTMLDivElement> {
  label: ReactNode;
  value: string;
  trend?: {                      // replaces footer sparkline+delta pattern
    sparkData: number[];
    delta: number | null;
    direction: "up" | "down" | "flat" | null;
    unit: "pp" | "%" | "";
    yearsCount?: number;
  };
  benchmark?: BenchmarkData;     // NEW — inline benchmark bars
  footer?: ReactNode;            // kept — backwards compat only
  locked?: boolean;
  onUnlock?: () => void;
}
```

**Acceptance criteria:**
- [ ] Renders identically to today when only `label` + `value` props used
- [ ] `trend` prop renders sparkline top-right + delta correctly
- [ ] `benchmark` prop renders bar chart with correct proportional widths
- [ ] Benchmark block hidden when `schoolValue` is null
- [ ] Colours match design tokens (Phase 0)
- [ ] No overflow at 375px
- [ ] Passes TypeScript strict checks

---

### Phase 2 — AcademicPerformanceSection: Benchmarks + Trends Inline
**Goal:** Every performance card shows trend sparkline AND benchmark bars. KS2 cards for secondary schools disappear (null schoolValue = hidden, not "Not available").

**Files changed:**
- `apps/web/src/features/school-profile/components/AcademicPerformanceSection.tsx`
- `apps/web/src/features/school-profile/SchoolProfileFeature.tsx` — pass `benchmarkDashboard`

**Metric key verification needed:**
Before coding, confirm `PERFORMANCE_METRICS[].key` aligns with `BenchmarkMetricVM.metricKey`. Create lookup: `Map<string, BenchmarkMetricVM>` from `benchmarkDashboard.sections[].metrics[]`.

**Acceptance criteria:**
- [ ] Each performance card: value + sparkline (top-right) + trend delta + benchmark bars
- [ ] Secondary school: KS4 cards shown, KS2 cards absent (not "Not available")
- [ ] Primary school: KS2 cards shown, KS4 cards absent
- [ ] Benchmark bars show school vs local vs England with correct deltas

---

### Phase 3 — AttendanceBehaviourSection: Benchmarks Inline
**Goal:** Absence rate and persistent absence cards show benchmark bars — these are high-signal metrics for parents and currently have no comparative context.

**Files changed:**
- `apps/web/src/features/school-profile/components/AttendanceBehaviourSection.tsx`

**Acceptance criteria:**
- [ ] Overall absence, persistent absence: benchmark bars visible
- [ ] Exclusions/suspensions: benchmark bars where data exists
- [ ] Existing trend sparklines preserved

---

### Phase 4 — Demographics Section: Benchmark Context
**Goal:** Key demographic metrics (disadvantaged %, FSM) get benchmark bars. Parents want to understand the school's intake relative to the area — this answers "is high FSM here normal for this area?"

**Files changed:**
- `apps/web/src/features/school-profile/components/DemographicsAndTrendsPanel.tsx`

**Note:** DemographicsAndTrendsPanel already has sparklines + delta working well. This phase adds benchmark bars beneath, same pattern as Phases 2+3.

**Acceptance criteria:**
- [ ] Disadvantaged %, FSM %, SEN %: benchmark bars vs local + national
- [ ] Existing sparklines + trend delta preserved
- [ ] No layout breakage

---

### Phase 5 — Remove BenchmarkComparisonSection
**Goal:** With benchmarks now inline across all sections, the standalone BenchmarkComparisonSection is pure duplication. Remove it from the page render.

**Files changed:**
- `apps/web/src/features/school-profile/SchoolProfileFeature.tsx` — remove render

**Component file `BenchmarkComparisonSection.tsx` is NOT deleted** — it stays in the codebase for potential future use (e.g. comparison modal, print view).

**Acceptance criteria:**
- [ ] BenchmarkComparisonSection no longer rendered on profile page
- [ ] No TypeScript errors
- [ ] No duplicate data visible anywhere on the page
- [ ] Rollback is one line: re-add `<BenchmarkComparisonSection ... />`

---

### Phase 6 — Responsive Polish + Mobile Audit
**Goal:** Audit the full page at 375px (iPhone SE), 390px (iPhone 14), 768px (iPad), 1440px (desktop). Fix anything that breaks or feels cramped.

**Known risks:**
- Benchmark bars at 375px may be too cramped with 3 rows of text + bars
- Consider collapsing benchmark block to a simple "vs region +2.1pp / vs England +5.4pp" text row on very small screens
- Section headings may need size reduction on mobile

**Acceptance criteria:**
- [ ] Full page review at 375px with no horizontal overflow
- [ ] Benchmark bars readable at 375px (≥ 10px text)
- [ ] Touch targets ≥ 48px for any interactive elements
- [ ] No layout regression on desktop

---

### Phase 7 — Design System Documentation (future-proofing)
**Goal:** Document the new StatCard patterns so the same approach can be applied to search results, comparison page, and any future pages without re-designing from scratch.

**Deliverable:** `/.planning/ux-overhaul/design-system.md` — StatCard variants with props reference, benchmark bar colour tokens, when to use each variant.

This phase unlocks rolling the design out to other pages.

---

## Rollback Plan

Each phase is independently reversible:

| Phase | Rollback |
|-------|----------|
| 0 — Tokens | `git checkout -- apps/web/src/app/globals.css` |
| 1 — StatCard | `git checkout -- apps/web/src/components/data/StatCard.tsx` |
| 2 — Performance | `git checkout -- apps/web/src/features/school-profile/components/AcademicPerformanceSection.tsx` |
| 3 — Attendance | `git checkout -- apps/web/src/features/school-profile/components/AttendanceBehaviourSection.tsx` |
| 4 — Demographics | `git checkout -- apps/web/src/features/school-profile/components/DemographicsAndTrendsPanel.tsx` |
| 5 — Remove section | Re-add `<BenchmarkComparisonSection />` in SchoolProfileFeature.tsx |
| 6 — Polish | `git checkout -- apps/web/src/` |

**Nuclear rollback** (everything): `git checkout -- apps/web/src/`

---

## What We Are NOT Doing in This Round (and why)

| Idea | Status | Reason |
|------|--------|--------|
| Restructure full page narrative (7-act model) | 🔜 Future | Requires more user testing first — get the card design right, then restructure |
| Redesign ProfileHeader | 🔜 Future | Works well, lower priority |
| WorkforceLeadershipSection benchmarks | 🔜 Phase 9 | Do after core sections proven |
| NeighbourhoodSection redesign | 🔜 Future | Different data type, different treatment needed |
| Three-line sparkline (school + local + national) | 🔜 Future | Requires Sparkline component extension — do after Phase 6 proven |
| New page structure / tabs | 🔜 Future | After card design is proven at 6 weeks |
| Search results page redesign | 🔜 Future | Blocked on this page being approved |
| Colour palette changes | ❌ Never | Brand is working — leave it |
| Backend / API changes | ❌ Never (this sprint) | All data already available |

---

## Open Questions (resolve before Phase 1 code)

1. **CSS token location:** Where do global CSS custom properties live in this codebase? Check `globals.css`, `index.css`, or Tailwind config.
2. **Metric key alignment:** Confirm `PERFORMANCE_METRICS[].key` in `AcademicPerformanceSection.tsx` matches `BenchmarkMetricVM.metricKey` values. If they diverge, a mapping table is needed.
3. **Benchmark bar on very small screens:** At 375px, 3 benchmark rows (label + bar + value) may be too tall. Fallback option: show only the signed deltas ("vs area +2pp / vs England +5pp") and hide the bars. Decision needed before Phase 6.

---

## Progress Log

> **All code changes are local only — nothing below has been committed to the repository.**
> The planning structure for this work is committed at `.planning/phases/phase-7-profile-ux-overhaul/`
> and referenced in `.planning/phased-delivery.md` as Phase 7.
> Implementation will be committed once design is reviewed and approved.

| Date | Deliverable | Local status | Committed to repo |
|------|-------------|-------------|-------------------|
| 2026-03-06 | Brief + Planning | Done | ✅ Yes (this file + phase-6a folder) |
| 2026-03-06 | P1 — Design tokens | Done locally | ❌ Not committed |
| 2026-03-06 | P2 — StatCard v1 (text rows) | Done locally — superseded by v2 | ❌ Not committed |
| 2026-03-06 | P3 — Benchmark wiring (all sections) | Done locally | ❌ Not committed |
| 2026-03-06 | P4 — Section narrative copy | Done locally | ❌ Not committed |
| 2026-03-06 | P2 redesign — StatCard v2 (visual bars + mobile fallback) | Done locally | ❌ Not committed |
| — | P5 — Responsive + mobile polish | Not started | ❌ |
| — | P6 — Design system documentation | Not started | ❌ |

### Phase 1 v2 — What's actually being built

**StatCard benchmark block (sm+ / tablet+):**
```
─ Compared with ─────────────────
This school  ████████████████░░  (bar only, value shown as hero number)
Local area   ██████████████░░░░  83.2%  +2.2pp
England      ████████████████░░  84.1%  +1.3pp
```
**StatCard benchmark block (mobile, < sm):**
```
─ Compared with ─────────────────
● Local area  83.2%  ▲ +2.2pp
● England     84.1%  ▲ +1.3pp
```
(No bars on mobile — cards are full width so readable, but adding bars would make cards 300px+ tall in a single-column scroll. Text fallback is still a significant improvement over nothing.)

**Other changes in this pass:**
- Remove `style={{ opacity: "var(--text-opacity-muted)" }}` from label — text-secondary is already appropriately muted
- "Attendance and Behaviour" → description rewritten to parent language
- "Workforce and Leadership" → renamed "Teachers & Staff", description rewritten
- "Academic Performance" → renamed "Results & Progress"
