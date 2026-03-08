# 11B - Search Summary API And Sort Contract

## Goal

Extend postcode search so the API returns enriched shortlist rows and owns ranking semantics for the MVP results surface.

## API Direction

- Extend the existing postcode search route rather than introducing client-side composition across multiple endpoints.
- Keep backend OpenAPI as the source of truth for all new result-row fields and query parameters.
- Return rows already ordered for the selected sort; the web app should render rather than re-rank.

## MVP Query Parameters

- `postcode`: required
- `radius`: limited in the web UX to `1`, `3`, `5`, or `10` miles
- `phase`: optional repeatable enum values for `primary` and `secondary`
- `sort`: optional enum
  - `closest` default
  - `ofsted`
  - `academic`

## MVP Result Fields

- `urn`
- `name`
- `type`
- `phase`
- `postcode`
- `lat`
- `lng`
- `distance_miles`
- `pupil_count`
- `latest_ofsted`
  - display label
  - sort rank
  - availability status
- `academic_metric`
  - metric key
  - label
  - display value
  - numeric sort value
  - availability status

## Sorting Rules

- `closest`
  - order by `distance_miles ASC`, then stable school key
- `ofsted`
  - order by Ofsted rank, then `distance_miles ASC`, then stable school key
- `academic`
  - valid only when the effective phase family is singular
  - primary-family ordering uses latest `ks2_combined_expected_pct DESC`
  - secondary-family ordering uses latest `progress8_average DESC`
  - tie-break by `distance_miles ASC`, then stable school key

## Phase Filter Rules

- No phase filter means show the normal postcode result set.
- `primary` includes `Primary`, `Middle deemed primary`, and `All-through` schools that publish the primary-family metric.
- `secondary` includes `Secondary`, `Middle deemed secondary`, and `All-through` schools that publish the secondary-family metric.
- If both `primary` and `secondary` are selected, the API returns the union and `academic` sort is unavailable.

## Error And Missing-Data Rules

- invalid postcode and unavailable postcode resolver behavior remain unchanged
- no-result searches stay explicit
- rows with missing Ofsted or academic values must remain present when they otherwise match the search
- the API must expose availability state so the UI can render "Not published" or equivalent copy deterministically

## Acceptance Criteria

- Frontend can render the full MVP postcode result row from one API response.
- Sort order is deterministic and tested at the API boundary.
- The contract makes mixed-phase academic sorting impossible rather than ambiguous.
