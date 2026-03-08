# 11C - Results Table Web Experience

## Goal

Deliver a postcode-results analysis mode that supports rapid ranking and comparison without disrupting the existing map-first search flow.

## Scope

- postcode-mode search only
- existing name search remains functionally unchanged in this phase
- existing linked map and sidebar search stay as the default exploration mode
- results view is a second mode over the same active postcode result set, not a separate search experience

## Mode Model

- keep the current postcode search journey as `Map` mode
- add a route-backed `Results` mode that opens as an overlay over the map experience
- `Results` must preserve the active postcode, radius, result set, map context, and compare state
- leaving `Results` returns the user to the same postcode search state without feeling like a hard page navigation

## Overlay Requirements

- entering `Results` should dim or blur the map context behind the analysis surface rather than fully replace it
- the overlay should feel like a deliberate analysis workspace, not a small modal dialog
- include a clear close or back-to-map affordance
- the overlay header should restate the active postcode, radius, and result count
- browser back should close the overlay and return to map mode for the same search

## Desktop Requirements

- keep the existing sidebar search visible as the map-mode anchor
- open results mode in a large overlay surface over the map area
- show postcode results in a dense decision table inside the overlay
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
- compare action uses the existing compare workflow
- include one compact ranking explanation above the table

## Mobile Requirements

- open results mode as a full-screen sheet or overlay rather than a desktop-style floating table
- do not force a full-width horizontal data table
- render each row as a stacked result card carrying the same MVP signals
- keep sort, phase filter, compare, and detail actions available without requiring desktop affordances

## Filter And Sort Controls

- keep the postcode search input on the main page
- keep the radius selector limited to `1`, `3`, `5`, and `10`
- replace generic phase chips in results mode with explicit `Primary` and `Secondary` controls
- expose the MVP sort choices:
  - `Closest`
  - `Ofsted`
- keep the academic metric visible in the result rows, but do not expose academic sorting in the initial web MVP
- controls may be repeated in the overlay header, but the experience should still read as one shared search state

## Ranking Explanation

- show one short explanation above the results surface
- examples:
  - `Sorted by distance from SW1A 1AA.`
  - `Sorted by latest Ofsted judgement, then distance.`

## State Requirements

- loading state should preserve perceived speed and not flash between unrelated layouts
- invalid postcode, no-results, and stale-results-plus-error states should remain explicit
- missing Ofsted or academic metrics should render as unavailable values, not disappear
- if the overlay is opened without an active postcode result set, redirect or fall back cleanly to map mode

## Out Of Scope

- blended quality ranking
- custom weighting
- saved searches
- travel-time search
- advanced filters beyond the MVP phase filter
- redesign of name-search mode
- account-based personalization

## Acceptance Criteria

- Users can search by postcode in the existing map-first flow and enter results mode without losing context.
- Users can add schools to compare directly from postcode results and reach the existing compare route.
- Mobile remains usable without requiring a desktop table metaphor.
