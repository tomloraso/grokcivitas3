# Phase 2F Design - Web Profile Enhancements (Ofsted Timeline + Area Context)

## Document Control

- Status: Draft
- Last updated: 2026-03-02
- Depends on:
  - `.planning/phases/phase-2/2E-school-profile-api-extensions.md`
  - `.planning/phases/phase-1/1G-web-school-profile-page.md`
  - `.planning/phases/phase-1/1F1-web-component-expansion-data-viz-baseline.md`
  - `.planning/phases/phase-0/0D1-web-foundations.md`
  - `docs/architecture/frontend-conventions.md`

## Objective

Enhance the school profile route (`/schools/:urn`) to present:

1. Ofsted inspection timeline history.
2. Area deprivation context.
3. Area crime context summary.

## Scope

### In scope

- Extend profile feature mapping/types for Phase 2 API sections.
- Add timeline and area-context profile components.
- Explicit loading/empty/partial states for new sections.
- Responsive rendering for desktop and mobile layouts.

### Out of scope

- Compare view changes (Phase 3).
- Premium-gated behavior (Phase 4).
- New shared design-system primitives beyond existing Phase 1F1 baseline.

## Decisions

1. Extend existing `school-profile` feature module; avoid creating parallel profile feature trees.
2. Reuse existing shared components (Card, Badge, Tabs, StatCard, RatingBadge, MetricUnavailable) for consistency.
3. Timeline is rendered in reverse chronological order with event-level outcome text and dates.
4. Area context sections must show explicit "unavailable" states when backend `coverage` flags are false.
5. Crime context visual emphasis is category breakdown + latest month total, not micro-location detail.

## UI Composition

Profile route additions:

1. Ofsted timeline section:
   - chronological event list (latest first),
   - inspection type, date, publication date, and outcome label/text.
2. Area deprivation section:
   - IMD decile and IDACI context indicators,
   - explanatory text for deprivation decile direction.
3. Area crime section:
   - latest month total incidents,
   - top categories list,
   - configurable radius display.

## Feature Structure

Use existing feature root:

- `apps/web/src/features/school-profile/`
  - extend `types.ts`
  - extend `mappers/profileMapper.ts`
  - extend `hooks/useSchoolProfile.ts`
  - add new components under `components/`

## File-Oriented Implementation Plan

1. `apps/web/src/api/client.ts`
   - ensure extended profile contract handling remains typed.
2. `apps/web/src/features/school-profile/types.ts`
   - add timeline and area-context view-model types.
3. `apps/web/src/features/school-profile/mappers/profileMapper.ts`
   - map extended API contract to view model.
4. `apps/web/src/features/school-profile/components/OfstedTimelineCard.tsx` (new)
5. `apps/web/src/features/school-profile/components/AreaDeprivationCard.tsx` (new)
6. `apps/web/src/features/school-profile/components/AreaCrimeSummaryCard.tsx` (new)
7. `apps/web/src/features/school-profile/SchoolProfileFeature.tsx`
   - compose new Phase 2 sections.
8. `apps/web/src/features/school-profile/mappers/profileMapper.test.ts`
   - add Phase 2 mapping cases.
9. `apps/web/src/features/school-profile/school-profile.test.tsx`
   - add render-state coverage for timeline and area context.
10. `apps/web/e2e/*.spec.ts`
    - extend profile journey assertions for timeline + area context presence.

## Testing And Quality Gates

### Required tests

- timeline component:
  - event ordering,
  - empty-state behavior.
- area deprivation component:
  - populated and unavailable states.
- area crime component:
  - populated category summary and no-data state.
- mapper coverage:
  - partial `coverage` behavior mapping.

### E2E updates

- search -> profile path verifies:
  - timeline section visible,
  - deprivation summary visible when data available,
  - crime summary visible when data available.

### Required gates

- `cd apps/web && npm run lint`
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run test`
- `cd apps/web && npm run build`
- `cd apps/web && npm run budget:check`
- `cd apps/web && npm run test:e2e`
- `make lint`
- `make test`

## Acceptance Criteria

1. Profile route shows Ofsted timeline and area context sections from typed API data.
2. New sections handle empty/partial/missing data explicitly.
3. UI remains responsive and accessible across mobile and desktop.
4. Existing Phase 1 profile content remains intact.

## Risks And Mitigations

- Risk: UI clutter from additional profile depth.
  - Mitigation: sectioned card layout and concise summary-first presentation.
- Risk: misleading interpretation of area context as exact local risk.
  - Mitigation: concise contextual copy clarifying aggregate/anonymized nature.
- Risk: mapper drift as API contract expands.
  - Mitigation: explicit mapper tests for all new sections and coverage flags.
