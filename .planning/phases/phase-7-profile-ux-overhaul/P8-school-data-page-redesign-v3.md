# P8 — School Data Page Redesign V3

## Document Control

- Status: Completed — local, 2026-03-08
- Author: Liora Voss (UX direction)
- Phase: 7 — Profile UX Overhaul

## Context

V2 (P7) landed the structural improvements: section reorder, `.flatMap()` null-skip pattern, `mobileTwo` prop, and trend period labels. V3 is a targeted polish pass addressing three residual issues found during the 2026-03-08 review.

## Issues Addressed

### 1. Ghost-card escape hatch in WorkforceMetricCard

**Problem:** `WorkforceMetricCard` checked for a missing catalog entry internally and returned `<MetricUnavailable>` — meaning a missing catalog key still rendered a card (ghost tile). The `.flatMap()` null-skip on the outer grid did not catch this because the component always returned a valid JSX element.

**Fix:** Remove `WorkforceMetricCard` helper entirely. Inline both checks (catalog null, value null) in `.flatMap()` returning `[]` for either. Render `<StatCard>` directly. Consistent with `AttendanceBehaviourSection` pattern.

### 2. Leadership layout — flex-wrap pill strip

**Problem:** Leadership data rendered as floating `min-w` pills that wrapperd unpredictably on narrow screens and had no visual grouping.

**Fix:** Replace pill strip with a single bordered container using CSS `divide-x` dividers between fields. All fields sit in one row with `overflow-x-auto` and `min-w-max` — scrolls horizontally on narrow viewports rather than wrapping. Cleaner at all sizes.

### 3. Premium CTA hover state

**Problem:** "Add to compare" and "Open compare" buttons had no hover affordance beyond a cursor change. The buttons are premium-adjacent CTAs and benefit from a subtle interactive signal.

**Fix:** Add `transition-all duration-200 hover:scale-[1.02] hover:border-brand/60 hover:shadow-[0_0_18px_rgba(168,85,247,0.22)]` to both buttons. The glow matches the hero StatCard shadow — brand purple, low opacity, non-distracting.

## Files Changed

| File | Change |
|------|--------|
| `apps/web/src/features/school-profile/components/WorkforceLeadershipSection.tsx` | Full replacement — remove `WorkforceMetricCard`, add `LeadershipStrip` with `divide-x` |
| `apps/web/src/features/school-profile/SchoolProfileFeature.tsx` | Add hover className to "Add to compare" and "Open compare" buttons |

## Acceptance Criteria

- [ ] No ghost tiles render in Workforce grid when catalog entry is missing
- [ ] Leadership strip renders as a single horizontal container with `divide-x` separators
- [ ] Leadership strip scrolls horizontally on narrow viewports; no wrap
- [ ] "Add to compare" button shows purple glow on hover
- [ ] "Open compare" button shows purple glow on hover
- [ ] TypeScript: zero errors (`npm run typecheck`)
- [ ] Tests: all passing (`npm run test`)

## Rollback

```bash
git checkout -- apps/web/src/features/school-profile/components/WorkforceLeadershipSection.tsx
git checkout -- apps/web/src/features/school-profile/SchoolProfileFeature.tsx
```
