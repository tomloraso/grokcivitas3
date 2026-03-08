# P7 — School Data Page Redesign v2 (Liora Voss Design Pass)

## Document Control

- Status: In progress — implemented locally 2026-03-08, not yet committed
- Author: Liora Voss (Principal UX/UI Designer persona)
- Phase: 7 (Profile UX Overhaul)
- Depends on: P1–P4 complete

---

## Diagnosis

Three structural failures identified in the P1–P4 implementation:

### 1. Ghost Cards (Highest Impact)
Sections render `MetricUnavailable` placeholder cards for every null-value metric. On many schools (especially primaries) this means 40–60% of the grid is grey ghost tiles. Result: page feels broken, parents lose trust.

### 2. Flat Visual Hierarchy (High Impact)
Hero cards (`variant="hero"`) had the right typography scale but lacked visual separation from sibling cards. The `shadow-sm` class applies a uniform 1px diffuse shadow — indistinguishable from the default card on most monitors. The bar height of 3px is too fine to register at a glance.

### 3. Wrong Section Order (Medium Impact)
Pre-redesign order: Ofsted → Demographics → Attendance → Workforce → Results.
Parent mental model: Ofsted → Results → Attendance → Demographics → Workforce.
Metrics that answer "is this school good?" were buried at the bottom.

---

## Changes Implemented

### MetricGrid — `mobileTwo` prop
**File:** `apps/web/src/components/data/MetricGrid.tsx`

Added `mobileTwo?: boolean` prop. When true, uses 2 columns on narrow mobile instead of 1. Grid key becomes `"2-{columns}"`.

```
mobileTwo=false (default): grid-cols-1 sm:grid-cols-2 ...
mobileTwo=true:            grid-cols-2 ...
```

### StatCard — Hero visual refinements
**File:** `apps/web/src/components/data/StatCard.tsx`

1. Bar height: `h-[3px]` → `h-[5px]` — benchmark bars now register visually on all screen densities.
2. Hero glow: added `shadow-[0_0_28px_rgba(168,85,247,0.10)]` to hero variant — subtle brand-colour halo differentiates the hero card without adding visual noise.

### WorkforceLeadershipSection — Null-skip + LeadershipStrip
**File:** `apps/web/src/features/school-profile/components/WorkforceLeadershipSection.tsx`

1. `.map()` → `.flatMap()` returning `[]` for null values — ghost cards eliminated from workforce grid.
2. Added `mobileTwo` to workforce MetricGrid.
3. Leadership 2×2 Card grid replaced with a horizontal `flex-wrap` strip of individual pill-style tiles. Each tile renders only if its value is non-null — no empty slots.

### AttendanceBehaviourSection — Null-skip + mobileTwo
**File:** `apps/web/src/features/school-profile/components/AttendanceBehaviourSection.tsx`

1. `.map()` → `.flatMap()` returning `[]` for null values in both attendance and behaviour grids.
2. Added `mobileTwo` to both MetricGrids.

### DemographicsAndTrendsPanel — Null-skip + mobileTwo
**File:** `apps/web/src/features/school-profile/components/DemographicsAndTrendsPanel.tsx`

1. `.map()` → `.flatMap()` returning `[]` for null values — demographics grid no longer shows ghost cards.
2. Added `mobileTwo` to demographics MetricGrid.

### SchoolProfileFeature — Section reorder
**File:** `apps/web/src/features/school-profile/SchoolProfileFeature.tsx`

New section order:
1. Ofsted Profile
2. **Results & Progress** (moved up from bottom)
3. **Day-to-Day at School** (Attendance + Behaviour)
4. Pupil Demographics
5. Teachers & Staff

---

## Acceptance Criteria

- [ ] No ghost/placeholder cards appear for null-value metrics in grids
- [ ] `mobileTwo` grids render 2 columns at 375px (iPhone SE) with no overflow
- [ ] Hero StatCard visually distinct from default (glow visible, bar 5px)
- [ ] Leadership strip shows only populated fields; no "Not published" filler text
- [ ] Section order: Ofsted → Results → Attendance → Demographics → Workforce on profile page
- [ ] TypeScript compiles with zero errors (`npm run typecheck`)
- [ ] All unit tests pass (`npm run test`)

---

## Rollback

Each change is isolated to its file. To revert any single change:

```bash
git checkout -- apps/web/src/components/data/MetricGrid.tsx
git checkout -- apps/web/src/components/data/StatCard.tsx
git checkout -- apps/web/src/features/school-profile/components/WorkforceLeadershipSection.tsx
git checkout -- apps/web/src/features/school-profile/components/AttendanceBehaviourSection.tsx
git checkout -- apps/web/src/features/school-profile/components/DemographicsAndTrendsPanel.tsx
git checkout -- apps/web/src/features/school-profile/SchoolProfileFeature.tsx
```

---

## Out of Scope (Deferred)

- P5 Responsive Mobile Polish — full 375px audit pass
- P6 Design System Documentation — Storybook / style guide entries
- AcademicPerformanceSection null-skip — that section uses a different data shape; review separately
