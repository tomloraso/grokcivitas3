# P6 - Design System Documentation

## Status

Complete (2026-03-10)

## Goal

Document the `StatCard` with benchmark patterns so the same approach can be applied to the compare route (Phase 9) and any future routes without redesigning from scratch.

## Deliverable

Central design system guide created at `docs/architecture/design-system.md` (referenced from `AGENTS.md` rule 3b). Covers:

- Full Loira Voss colour palette and typography
- Button system (primary/secondary/ghost/compare variants with cva animation)
- Card primitive (panel-surface glass styling)
- StatCard variants (default/hero/mini), size prop, benchmark delta neutrality, title min-height
- Trend indicators (always teal, vertical footer layout)
- Layout patterns (mobile-first 375px, school profile, compare page)
- Premium access gates and shareability
- Stacked bar + legend pattern (chart colour palette, bidirectional hover, remainder slice, canonical implementations)
- Anti-patterns list (14 explicit "do not" rules)

This supersedes the original plan for `.planning/ux-overhaul/design-system.md` — the guide lives in `docs/architecture/` alongside other architecture docs, making it discoverable by all agents and contributors.

## Acceptance Criteria

- [x] `design-system.md` written and committed to `docs/architecture/`.
- [x] `AGENTS.md` references this deliverable (rule 3b + agent guides table).
- [x] `docs/index.md` includes the guide in the docs index.
- [x] Phase 9 (compare) team can implement `StatCard` with benchmark bars without re-reading this phase's implementation files.
