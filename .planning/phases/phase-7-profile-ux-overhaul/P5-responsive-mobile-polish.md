# P5 - Responsive + Mobile Polish

## Status

Not started

## Goal

Audit the full profile page at 375px (iPhone SE), 390px (iPhone 14 Pro), 768px (iPad), and 1440px (desktop) after P1–P4 land. Fix any overflow, cramped layouts, or benchmark block legibility issues.

## Known Risks

### Benchmark block height on mobile
Each stat card in a benchmark-enabled section now has additional height. On mobile (single-column), tall cards create long scroll journeys. The benchmark block uses a mobile fallback (compact text rows, no bars) to manage this, but the text size (`text-[11px]`) must remain legible without zoom.

### Bar widths at 640px (sm breakpoint boundary)
At exactly 640px, bars switch from hidden to visible. The bar track width minus label/value text must leave at least ~40px for a bar to carry meaning. Cards at `sm:p-5` (20px each side) on a 640px viewport = 600px content → 3 columns = ~193px each card → ~153px inner width. Labels + values at 10px text could consume up to 120px, leaving ~30px for the bar track. May need to increase padding or reduce value text at this breakpoint.

### Touch targets
Any interactive element on the card must remain ≥ 48×48px. The card hover state is purely visual and the card itself is not a button, so this is currently unaffected.

## Audit Checklist

- [ ] 375px: No horizontal overflow on any profile section.
- [ ] 375px: Benchmark text rows readable at `text-[11px]` without zoom.
- [ ] 375px: Mobile single-column card height ≤ 200px (no benchmark), ≤ 240px (with benchmark + footer).
- [ ] 640px (sm breakpoint): Bars visible, readable, and proportionally meaningful.
- [ ] 768px: 2-column grid cards have benchmark bars; no crowding.
- [ ] 1024px: 3-column grid, benchmark bars show full three rows cleanly.
- [ ] 1440px: No layout regression on wide desktop.
- [ ] `prefers-reduced-motion`: bar width transitions must respect this (either use `transition-none` or ensure 0ms duration in reduced-motion mode).

## Files Likely Affected

- `apps/web/src/components/data/StatCard.tsx` — tweaks to benchmark block font sizes or visibility thresholds.
- `apps/web/src/components/data/MetricGrid.tsx` — column breakpoints if needed.
- Section components — if subsection or grid adjustments are needed.

## Acceptance Criteria

- [ ] Full audit passed at all four viewport sizes.
- [ ] No horizontal overflow at 375px.
- [ ] Benchmark bars legible at 640px+.
- [ ] Touch targets ≥ 48px for any interactive elements.
- [ ] Reduced-motion respected for bar width transitions.
- [ ] Lint + TypeScript clean.

## Rollback

Per-file: `git checkout -- <file>`
