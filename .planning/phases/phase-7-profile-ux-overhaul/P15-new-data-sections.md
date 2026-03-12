# P15 — New Data Sections: Subject Performance, Destinations Upgrade, Workforce Empty States (2026-03-12)

## Status: Complete

## Problem

Three data pipeline additions (school_admissions, leaver_destinations, ks4_subject_performance, sixteen_to_eighteen_subject_performance) landed data into the backend but the frontend needed alignment:

1. **Subject Performance** — backend serves `strongest_subjects`, `weakest_subjects`, and `stage_breakdowns` per school but had zero frontend representation. No types, mapper, or component existed.

2. **Leaver Destinations** — section existed but was visually flat compared to other sections. Just a grid of StatCards with no visual hierarchy or proportional representation, despite destinations data being naturally suited to a stacked breakdown view.

3. **Teachers & Staff** — for schools with no published workforce census data (e.g. URN 136655), all three metric sub-groups (Snapshot, Stability, Pressure) were silently hidden by the `flatMap` null-skip pattern + `.filter(cards.length > 0)`, leaving the section looking broken rather than clearly empty.

## Solution

### 1. Subject Performance Section (`SubjectPerformanceSection.tsx`)

New component rendered inside the "Results & Progress" accordion, below `AcademicPerformanceSection`. Subject results are a drill-down from headline measures (Attainment 8, Progress 8), so they belong in the same section rather than a new TOC entry.

**Layout:**
- Section header with academic year badge + last-updated date
- **Strongest / Weakest subjects** — ranked tables (top 5 each) showing subject name, entries count, high-grade %, pass %. Desktop: side-by-side `xl:grid-cols-2`. Mobile: stacked cards.
- **All Subjects by Qualification** — expandable `SubjectBreakdownGroup` per qualification family (GCSE, Vocational, A Level). Each group has:
  - Stacked proportional bar (weighted by entries count, coloured by chart palette)
  - Bidirectional hover between bar segments and table rows
  - Expand/collapse toggle for the full subject table
- No benchmarks (none available in backend for per-subject data — confirmed)
- No trend sparklines (subject performance not in the trends series)

**Data flow:**
- Types: `SubjectSummaryVM`, `SubjectPerformanceGroupVM`, `SubjectPerformanceVM` added to `types.ts`
- Mapper: `mapSubjectPerformance()` added to `profileMapper.ts` with defensive typing against the untyped API response field
- Profile VM: `subjectPerformance: SubjectPerformanceVM | null` added to `SchoolProfileVM`

### 2. Destinations Visual Upgrade (`SchoolDestinationsSection.tsx`)

Replaced the flat StatCard grid with the design-system Stacked Bar + Legend pattern:

- **Hero StatCard** — `variant="hero"` for the overall sustained destinations % per stage, with trend sparkline
- **Stacked proportion bar** — `DestinationBar` showing education / apprenticeship / employment / not sustained / unknown segments. Fixed colour mapping (teal for education, sky for apprenticeship, violet for employment, gray for not sustained/unknown)
- **Legend grid** — `DestinationLegend` with colour dots, percentage values, and inline trend indicators. Bidirectional hover with the bar (per design-system.md pattern)
- **Education sub-breakdown** — `EducationBreakdownList` as a legend-style list (FE, sixth form, HE etc.) rather than flat StatCards
- All design system rules followed: solid hex chart colours, `duration-fast` transitions, `role="img"` on the bar, `tabular-nums` on values

### 3. Workforce Empty-State Notices (`WorkforceLeadershipSection.tsx`)

Changed from silently hiding empty sub-groups to showing all three groups with a "No published data for this period" notice when a group has zero metrics:

- Removed `.filter((group) => group.cards.length > 0)` — all groups now always render
- Added conditional: if `group.cards.length > 0`, render `MetricGrid`; else render the notice text
- Top-level "Workforce unavailable" fallback retained when ALL groups are empty
- Gives the user visibility into what data dimensions exist, even when empty for a specific school

## Design System Compliance

- Stacked Bar + Legend pattern from `design-system.md` section "Stacked Bar + Legend Pattern"
- Chart colours from `CHART_COLORS` palette (solid hex, never opacity-based Tailwind)
- `panel-surface` on section containers, `border-border-subtle` on inner cards
- Mobile-first: stacked cards below `sm`, tables above `sm`
- Title Case labels, `text-brand` accent bars
- `MetricUnavailable` fallback for missing data
- Trend indicators always teal, direction-only (P11 rules)

## Files Changed

- `apps/web/src/features/school-profile/types.ts` — added subject performance VMs
- `apps/web/src/features/school-profile/mappers/profileMapper.ts` — added `mapSubjectPerformance()`
- `apps/web/src/features/school-profile/components/SubjectPerformanceSection.tsx` — new component
- `apps/web/src/features/school-profile/components/SchoolDestinationsSection.tsx` — visual upgrade
- `apps/web/src/features/school-profile/components/WorkforceLeadershipSection.tsx` — empty-state notices
- `apps/web/src/features/school-profile/SchoolProfileFeature.tsx` — wired `SubjectPerformanceSection`
