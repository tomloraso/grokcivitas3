# P11 — Direction-Only Trend Indicators (2026-03-10)

## Status: Complete

## Problem

All trend indicators previously used:
- `TrendingUp` / `TrendingDown` lucide icons
- `text-trend-up` (teal) for positive deltas
- `text-trend-down` (red) for negative deltas
- `+` / `-` prefixes on the delta number

This implied good/bad judgements based purely on mathematical sign. A falling pupil-teacher ratio (numerically negative) is good for parents. A rising absence rate (numerically positive) is bad. Conditional red/green colouring was misleading and inconsistent.

## Solution

### `TrendIndicator.tsx` rewrite

Replace icons and conditional colour with direction-only triangles, always brand teal:

| Direction | Symbol | Colour |
|---|---|---|
| Up | ▲ | `text-brand` (#00D4C8) |
| Down | ▼ | `text-brand` (#00D4C8) |
| Flat | — | `text-disabled` |

Delta rendered as **absolute value** — triangle already conveys sign. `+` prefix removed.

Examples:
- Before: `↗ +2.1% · 3yr` (teal)  /  `↘ -1.5% · 3yr` (red)
- After: `▲ 2.1% · 3yr` (teal)  /  `▼ 1.5% · 3yr` (teal)

`period` prop unchanged. `asPercentage` / `unit` props unchanged. `iconSize` prop removed (no icon to size).

### `stat-card.tsx` — new `trendDirection` prop

```tsx
trendDirection?: "up" | "down" | null
```

Renders a small ▲/▼ inline immediately after the value number in `text-brand`. Use when you want a direction triangle without a delta number or sparkline. When you need a sparkline or delta text, continue using `footer` + `<TrendIndicator>`.

## Design rule

> Trend indicators are direction facts, not value judgements. The platform never colours a number red because it went down. Parents can interpret direction; they don't need the app to judge for them.

## Cascade

`TrendIndicator` is used via `footer` prop in all four section components. Updating `TrendIndicator.tsx` cascades to all of them automatically — no section component changes needed.

## Files changed

- `apps/web/src/components/data/TrendIndicator.tsx` (rewrite)
- `apps/web/src/components/ui/stat-card.tsx` (new `trendDirection` prop)
- `apps/web/README.md` (new trend indicators design system rule section)
- `README.md` (TrendIndicator added to component inventory)
- `.planning/phases/phase-7-profile-ux-overhaul/README.md` (P11 tracking log, architecture view, deliverables table)

## Files NOT changed

- `AcademicPerformanceSection.tsx` — TrendIndicator update cascades
- `AttendanceBehaviourSection.tsx` — TrendIndicator update cascades
- `WorkforceLeadershipSection.tsx` — TrendIndicator update cascades
- `DemographicsAndTrendsPanel.tsx` — TrendIndicator update cascades
- `NeighbourhoodSection.tsx` — no TrendIndicator usage
- `ProfileHeader.tsx` — no TrendIndicator usage
