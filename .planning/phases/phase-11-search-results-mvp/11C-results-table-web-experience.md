# 11C - Results Table Web Experience

## Goal

Deliver a postcode-results experience on the main page that supports rapid shortlist creation without sacrificing mobile usability.

## Scope

- postcode-mode search only
- existing name search remains functionally unchanged in this phase
- existing linked map stays in place

## Desktop Requirements

- show postcode results in a dense decision table
- required MVP columns:
  - school name
  - distance
  - phase
  - type
  - latest Ofsted headline
  - phase-aware academic metric
  - pupil count
  - compare action
- school name links to the detail page
- compare action uses the existing compare shortlist behavior

## Mobile Requirements

- do not force a full-width horizontal data table
- render each row as a stacked result card carrying the same MVP signals
- keep sort, phase filter, compare, and detail actions available without requiring desktop affordances

## Filter And Sort Controls

- keep the postcode search input on the main page
- keep the radius selector limited to `1`, `3`, `5`, and `10`
- replace generic phase chips in postcode mode with explicit `Primary` and `Secondary` controls
- expose the MVP sort choices:
  - `Closest`
  - `Ofsted`
  - `Academic`
- disable or hide `Academic` when the current phase selection does not resolve to a single family

## Ranking Explanation

- show one short explanation above the results surface
- examples:
  - `Sorted by distance from SW1A 1AA.`
  - `Sorted by latest Ofsted judgement, then distance.`
  - `Sorted by latest published academic metric for primary schools, then distance.`

## State Requirements

- loading state should preserve perceived speed and not flash between unrelated layouts
- invalid postcode, no-results, and stale-results-plus-error states should remain explicit
- missing Ofsted or academic metrics should render as unavailable values, not disappear

## Out Of Scope

- blended quality ranking
- custom weighting
- saved searches
- travel-time search
- advanced filters beyond the MVP phase filter
- redesign of name-search mode
- account-based personalization

## Acceptance Criteria

- Users can search by postcode and scan shortlist-grade headline signals without leaving the main page.
- Users can add schools to compare directly from postcode results and reach the existing compare route.
- Mobile remains usable without requiring a desktop table metaphor.
