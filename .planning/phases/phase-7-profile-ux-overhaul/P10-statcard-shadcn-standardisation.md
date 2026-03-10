# P10 — StatCard shadcn Standardisation (2026-03-09)

## Status: Complete

## Problem

P9 iterations 6–9 applied ad-hoc `valueClassName` overrides and inline raw `div` stat blocks to work around overflow/cramping issues in the Neighbourhood Context section. The root cause was architectural: `StatCard` (from `components/data/StatCard.tsx`) was a full `Card`-based component with `p-4 sm:p-5` padding. Nesting it inside another `Card` doubled the padding, leaving almost no horizontal room for labels or values in 2-column grids.

Specific failures fixed by this work:
- "Incidents" and domain labels spilling outside card boundaries
- "Three-Year Change" label wider than its grid column
- Inconsistent value font sizes across the six Neighbourhood mini-stats (default `text-3xl sm:text-4xl` vs overridden `text-lg sm:text-xl`)
- Long IMD domain labels ("Health Deprivation and Disability", "Education, Skills and Training") overflowing their 2-col grid cells

## Solution

### New canonical primitive: `components/ui/stat-card.tsx`

shadcn-style component using `cva` for variant and size control. Three variants:

| Variant | Element | Padding | Use when |
|---|---|---|---|
| `default` | `<Card>` | `p-4 sm:p-5` | Standalone metric in a `MetricGrid` |
| `hero` | `<Card>` | `p-4 sm:p-5` | Most important metric in a section |
| `mini` | plain `<div>` | none | Embedded inside an existing section `Card` |

`variant="mini"` has zero card chrome — no border, shadow, hover, or padding. The parent container controls layout and spacing. This eliminates double-padding permanently.

Size prop maps to value font size across variants:

| Size | `default` | `hero` | `mini` |
|---|---|---|---|
| `sm` | `text-2xl sm:text-3xl` | `text-3xl sm:text-4xl` | `text-xl` |
| `md` _(default)_ | `text-3xl sm:text-4xl` | `text-4xl sm:text-5xl` | `text-2xl` |
| `lg` | `text-4xl sm:text-5xl` | `text-5xl sm:text-6xl` | `text-2xl sm:text-3xl` |

Built-in overflow protection on every render:
- Label: `min-w-0 leading-tight` — long labels wrap cleanly inside grid cells
- Value: `tabular-nums break-all` — numbers never overflow
- Wrapper: `overflow-hidden` — nothing escapes the card boundary

`tooltip` prop (preferred) + `description` legacy alias — same expandable ⓘ info paragraph behavior as before.

`BenchmarkSlot` interface and `BenchmarkBlock` bars are internal. `BenchmarkSlot` is re-exported for caller type use.

### Shim: `components/data/StatCard.tsx`

Converted to a one-line re-export of the new canonical location. All four section components (`AcademicPerformanceSection`, `AttendanceBehaviourSection`, `DemographicsAndTrendsPanel`, `WorkforceLeadershipSection`) continue working without modification — they import from the shim path, which transparently forwards to `components/ui/stat-card`.

### Migration: `NeighbourhoodSection.tsx`

Replaced raw `div` inline stat blocks (introduced in P9 iteration 9 as a stopgap) with `<StatCard variant="mini" size="sm">` inside the existing light-bordered containers:

```tsx
<div className="grid grid-cols-2 gap-x-4 gap-y-1 rounded-md border border-border-subtle/60 bg-surface/50 px-3 py-2.5">
  <StatCard variant="mini" size="sm" label="Incidents" value={...} />
  <StatCard variant="mini" size="sm" label="Per 1,000" value={...} />
</div>
```

All four house price stats are in a single unified grid (previously split across two `MetricGrid`+`StatCard` pairs, which caused the inconsistent sizing).

Domain decile label overflow fix: `min-w-0 leading-tight` on the label container. Labels wrap onto a second line rather than truncating — `truncate` was removed after "Living environment" was observed truncating in the UI.

Area Crime card redesign (2026-03-10): period label clarified to "12 months to {month}"; headline stat block and sparkline container danger-tinted; each crime category row gains a proportional fill bar (`bg-danger/50`) scaled to share of total incidents. All numeric values use `text-primary` (white) — consistent with other section stats; danger bars carry the severity signal.

## Files changed

- `apps/web/src/components/ui/stat-card.tsx` (new — canonical primitive)
- `apps/web/src/components/data/StatCard.tsx` (shim — re-export only)
- `apps/web/src/features/school-profile/components/NeighbourhoodSection.tsx` (mini variant migration)
- `apps/web/README.md` (StatCard design system rule section)
- `README.md` (frontend component inventory table)
- `.planning/phases/phase-7-profile-ux-overhaul/P9-loira-voss-design-refresh.md` (status updated, iteration 10 entry added)
- `.planning/phases/phase-7-profile-ux-overhaul/README.md` (architecture view + deliverables table updated)

## Files NOT changed

- `AcademicPerformanceSection.tsx` — works via shim, no changes needed
- `AttendanceBehaviourSection.tsx` — works via shim, no changes needed
- `DemographicsAndTrendsPanel.tsx` — works via shim, no changes needed
- `WorkforceLeadershipSection.tsx` — works via shim, no changes needed
- `ProfileHeader.tsx` — hero signals use bespoke sub-components, not StatCard

## Superseded by P11 (partial)

Trend indicators rendered via `TrendIndicator.tsx` have been updated in P11 (2026-03-10) to use ▲/▼ direction triangles always in `text-brand` — replacing the conditional `text-trend-up` (teal) / `text-trend-down` (red) colour logic. The `StatCard` primitive gained a `trendDirection` prop in the same change. The StatCard variant/size system and overflow protection from P10 are unaffected.

## Design rules enforced going forward

1. **Never use `variant="default"` or `variant="hero"` inside another `Card`.** Always use `variant="mini"` for nested stats.
2. **Use `size` prop to control value font size.** Do not use `valueClassName` for routine sizing — it is an escape hatch only.
3. **New code imports from `components/ui/stat-card` directly.** The shim path (`components/data/StatCard`) is for existing callers only.
