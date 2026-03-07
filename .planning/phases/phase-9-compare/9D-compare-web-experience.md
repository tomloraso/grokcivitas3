# 9D - Compare Web Experience

## Goal

Deliver a dedicated compare page that makes cross-school evaluation readable on both desktop and mobile.

## Page Requirements

- dedicated compare route at `/compare?urns=<urn1>,<urn2>,...`
- responsive layout for two to four schools
- top compare header showing the selected school columns before deeper metric sections
- sectioned metric presentation matching the compare contract
- clear year labels, units, and availability states

## Layout Direction

- Desktop should use a scrollable comparison matrix with sticky row labels and sticky school headers.
- Mobile should use section cards with metric labels fixed on the left edge of a horizontal school-value scroller so row alignment is preserved.
- The school header should show name, phase, type, postcode, and optional search-derived distance when that client-side context exists.
- The school header should remain visible above deeper metric sections.

## Interaction Requirements

- Remove-school action from compare page.
- Empty, underfilled, loading, and error states should all be explicit.
- Compare view should link to profile routes without losing compare context.
- Underfilled state should keep the currently selected schools visible and explain that at least two schools are required.
- Profile links opened from compare should carry `fromCompare` route state so the profile page can render a return affordance.

## State-Specific Behavior

- Empty state: no valid selected URNs in the URL or compare selection state.
- Underfilled state: exactly one valid selected URN.
- Loading state: compare route is hydrating selection state or waiting on `GET /api/v1/schools/compare`.
- Error state: compare API validation or availability failure.
- Ready state: two to four valid schools returned by the compare API.

## Testing Requirements

- mapper tests for compare view-model shaping
- component tests for aligned row rendering and availability states
- end-to-end coverage for building a compare set and opening the compare page
- end-to-end coverage for removing a school and landing in the underfilled state

## Acceptance Criteria

- Compare page is usable with two, three, or four schools.
- Availability language matches the backend contract and existing completeness semantics.
- Mobile layout remains usable without breaking section alignment.
