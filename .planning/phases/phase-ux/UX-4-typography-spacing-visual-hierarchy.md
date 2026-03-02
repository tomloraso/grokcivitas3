# Phase UX-4 Design - Typography, Spacing, And Visual Hierarchy

## Document Control

- Status: Draft
- Last updated: 2026-03-02
- Depends on:
  - `.planning/phases/phase-ux/README.md`
  - `.planning/phases/phase-0/0D1-web-foundations.md`
  - `.planning/phases/phase-1/1F1-web-component-expansion-data-viz-baseline.md`
  - `.planning/phases/phase-1/1G-web-school-profile-page.md`
  - `docs/architecture/frontend-conventions.md`

## Objective

Shift Civitas web presentation from functional dashboard density to an editorial, data-storytelling hierarchy while preserving accessibility and token consistency.

## Scope

### In scope

- Search hero heading and supporting text hierarchy refinement.
- Result card visual hierarchy and metadata density tuning.
- Stat and metric label treatment for profile sections.
- Section divider and spacing rhythm refinements.
- Font weight/family usage audit and normalization.

### Out of scope

- Motion choreography (UX-5).
- Header/footer behavior changes (UX-6).
- Map interaction behavior (UX-2).

## Decisions

1. Existing font stack remains: Space Grotesk (display), Public Sans (body), IBM Plex Mono (data accents).
2. Typography changes must remain token-driven; avoid hardcoded ad-hoc font values in feature components.
3. Visual hierarchy priority for result cards: school name -> distance -> key metadata.
4. Profile data cards prioritize large numeric signal with muted explanatory labels.
5. Contrast compliance from Phase 0 remains mandatory after all palette/weight changes.

## Frontend Design

### Search route

- Increase primary heading prominence.
- Reduce competing secondary text weight and opacity.
- Ensure first viewport scan quickly communicates action and context.

### Result cards

- Consolidate secondary metadata into compact row.
- Increase whitespace around headline and distance elements.
- Align hover/active states with UX-2/UX-3 interaction affordances.

### Profile route

- Normalize section spacing and divider rhythm.
- Emphasize key metric values visually without increasing content clutter.

## File-Oriented Implementation Plan

1. `apps/web/src/styles/tokens.css`
   - add/adjust typography and spacing tokens only where needed.
2. `apps/web/src/styles/theme.css`
   - global heading/body defaults and divider utility refinements.
3. `apps/web/src/features/schools-search/SchoolsSearchFeature.tsx`
   - hero text and spacing composition updates.
4. `apps/web/src/components/ui/ResultCard.tsx`
   - hierarchy and metadata row refinement.
5. `apps/web/src/components/data/StatCard.tsx`
   - large-value and muted-label treatment update.
6. `apps/web/src/features/school-profile/components/*.tsx`
   - spacing and section rhythm adjustments for profile cards.
7. `apps/web/src/components/data/data-components.test.tsx`
   - update assertions where text semantics/structure change.

## Testing And Quality Gates

### Required tests

- Unit/component:
  - result card semantic and accessibility labels remain intact.
  - stat card and profile sections preserve meaningful heading structure.
- A11y regression:
  - contrast checks remain passing.
  - no touch target regressions on interactive card elements.
- Visual baseline:
  - screenshot snapshots for search hero, result list, and profile metrics.

### Required commands

- `cd apps/web && npm run lint`
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run test`
- `cd apps/web && npm run build`
- `cd apps/web && npm run budget:check`
- `cd apps/web && npm run lighthouse:check`
- `make lint`
- `make test`

## Acceptance Criteria

1. Search hero and result cards read with clear editorial hierarchy.
2. Profile metrics emphasize numeric signal without reducing clarity.
3. Spacing/divider rhythm feels consistent across search and profile routes.
4. Contrast and accessibility requirements remain satisfied.

## Risks And Mitigations

- Risk: visual refinements introduce inconsistent one-off styles.
  - Mitigation: constrain changes to tokens/theme/shared components first.
- Risk: larger typography reduces useful content density on mobile.
  - Mitigation: validate responsive scale and wrap behavior at mobile breakpoints.
- Risk: hierarchy updates unintentionally weaken established brand cohesion.
  - Mitigation: use existing token palette and font system rather than new brand primitives.