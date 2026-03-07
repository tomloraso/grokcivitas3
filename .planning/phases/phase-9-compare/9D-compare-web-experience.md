# 8D - Compare Web Experience

## Goal

Deliver a dedicated compare page that makes cross-school evaluation readable on both desktop and mobile.

## Page Requirements

- dedicated compare route
- responsive layout for two to four schools
- sectioned metric presentation matching the compare contract
- clear year labels, units, and availability states

## Layout Direction

- Desktop should favor a columnar comparison layout with sticky row labels or section headers.
- Mobile should use a stacked or horizontally scrollable pattern that preserves metric alignment and readability.
- Identity summary should remain visible above deeper metric sections.

## Interaction Requirements

- Remove-school action from compare page.
- Empty, underfilled, loading, and error states should all be explicit.
- Compare view should link back to profile routes without losing context.

## Testing Requirements

- mapper tests for compare view-model shaping
- component tests for aligned row rendering and availability states
- end-to-end coverage for building a compare set and opening the compare page

## Acceptance Criteria

- Compare page is usable with two, three, or four schools.
- Availability language matches the backend contract and existing completeness semantics.
- Mobile layout remains usable without breaking section alignment.
