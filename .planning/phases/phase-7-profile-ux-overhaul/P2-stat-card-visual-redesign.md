# P2 - StatCard Visual Redesign

## Status

Completed — 2026-03-07

## Goal

Redesign `StatCard` to be the single component that expresses a metric's value, trend, and benchmark context. This is the core building block that all subsequent wiring depends on.

## File

- `apps/web/src/components/data/StatCard.tsx`

## New Anatomy

### Tablet / desktop (sm+)

```
┌──────────────────────────────────────────┐
│ METRIC LABEL                             │  ← text-xs uppercase text-secondary
│ 85.4%                                    │  ← font-display text-3xl/4xl font-bold
│ [sparkline ≋≋≋≋≋≋≋] ▲ +2.1pp           │  ← existing footer slot (unchanged)
│ ────────────────────────────────────     │
│ Compared with                            │  ← 9px uppercase tracking text-disabled
│ This school  ████████████████░░░░  ·     │  ← purple bar, no value (shown above)
│ Local area   ██████████░░░░░░░░░░  83.2% +2.2pp  │  ← cyan bar
│ England      ████████████░░░░░░░░  84.1% +1.3pp  │  ← green bar
└──────────────────────────────────────────┘
```

### Mobile (< sm)

```
┌──────────────────────────────────────────┐
│ METRIC LABEL                             │
│ 85.4%                                    │
│ [sparkline] ▲ +2.1pp                    │
│ ──────────────────────────────────────── │
│ Compared with                            │
│ ● Local area  83.2%  +2.2pp             │  ← text only, no bar
│ ● England     84.1%  +1.3pp             │  ← text only, no bar
└──────────────────────────────────────────┘
```

(Bars omitted on mobile to prevent cards exceeding ~180px in a single-column scroll.)

## New Interface

### BenchmarkSlot (exported)

```ts
export interface BenchmarkSlot {
  localLabel: string;
  schoolRaw: number | null;      // used for bar width
  localRaw: number | null;       // used for bar width
  nationalRaw: number | null;    // used for bar width
  isPercent: boolean;            // true → scale 0-100; false → scale to max(three)
  localValueFormatted: string | null;
  nationalValueFormatted: string | null;
  schoolVsLocalDelta: number | null;
  schoolVsNationalDelta: number | null;
  schoolVsLocalDeltaFormatted: string | null;
  schoolVsNationalDeltaFormatted: string | null;
}
```

### StatCard props

```ts
interface StatCardProps extends HTMLAttributes<HTMLDivElement> {
  label: ReactNode;
  value: string;
  footer?: ReactNode;       // existing — sparkline + TrendIndicator
  icon?: ReactNode;
  benchmark?: BenchmarkSlot; // new — optional benchmark block
}
```

## Design Decisions

- Bar height: `h-[3px]` — thin enough not to overwhelm the metric value.
- Bar scale: `percent` → 0–100 fixed; all others → `Math.max(school, local, national)`.
- School bar shows no value label (the hero number above is already visible).
- Delta colours: `text-trend-up` (blue) for positive, `text-trend-down` (grey) for negative. Directional only — not evaluative (avoids red/green for absence rate etc.).
- Label opacity override (`style={{ opacity: "var(--text-opacity-muted)" }}`) removed — `text-secondary` is already the correct muted treatment.
- `footer` prop retained for backwards compatibility — existing callers unchanged.

## Acceptance Criteria

- [x] Renders identically when only `label` + `value` passed (no regression).
- [x] `benchmark` prop renders bars on sm+ and text rows on mobile.
- [x] Bar widths are mathematically proportional to the scale rule.
- [x] Benchmark block absent when `benchmark` prop is undefined.
- [x] No horizontal overflow at 375px.
- [x] TypeScript strict — no errors.
- [x] Lint passes.

**Deviations from spec:**
- "Compared with" heading removed — cleaner without it; bars are self-explanatory.
- `BenchmarkSlot` extended with `displayDecimals: number` and `schoolValueFormatted` — raw values are rounded to display precision before bar scale computation, fixing a precision mismatch bug where bars showed different widths for values that displayed identically (e.g. permanent exclusion rate = 1.00 for all three but bars differed).
- `description?: string` prop added to `StatCardProps` — plain-English metric explanation shown via ⓘ toggle button. Not in original spec; emerged from UX review session.
- `period` prop added to `TrendIndicator` — appends time span to delta label (e.g. "+2.1% · 3yr"). Required to make sparklines meaningful without axis labels.

## Rollback

```
git checkout -- apps/web/src/components/data/StatCard.tsx
```
