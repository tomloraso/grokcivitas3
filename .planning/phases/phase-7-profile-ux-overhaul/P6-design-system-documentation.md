# P6 - Design System Documentation

## Status

Not started

## Goal

Document the `StatCard` with benchmark patterns so the same approach can be applied to the compare route (Phase 9) and any future routes without redesigning from scratch.

## Deliverable

`/.planning/ux-overhaul/design-system.md` — StatCard variants reference covering:

- StatCard with `label` + `value` only (basic).
- StatCard with `footer` (sparkline + TrendIndicator).
- StatCard with `benchmark` (inline bars).
- StatCard with both `footer` and `benchmark`.
- `BenchmarkSlot` interface field-by-field reference.
- When to pass `isPercent: true` vs `false` and the effect on bar scale.
- Benchmark colour tokens (`--color-benchmark-school/local/national`) and their Tailwind aliases.
- Mobile vs desktop rendering differences.
- Rollout checklist for applying the pattern to new pages.

## Acceptance Criteria

- [ ] `design-system.md` written and committed to `.planning/ux-overhaul/`.
- [ ] `phased-delivery.md` references this deliverable under Phase 7.
- [ ] Phase 9 (compare) team can implement `StatCard` with benchmark bars without re-reading this phase's implementation files.
