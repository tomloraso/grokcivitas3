# 11A - Search Summary Projection

## Goal

Create a pipeline-maintained Gold read model that supplies postcode search with shortlist-grade summary fields without hydrating full profiles on the request path.

## Projection Direction

- Add one dedicated serving projection for postcode search, for example `school_search_summary`.
- Keep the projection keyed by `urn`.
- Treat the projection as a read model owned by pipeline promote or explicit post-promote materialization, not by API handlers.

## Required Fields

- school identity: `urn`, `name`, `type`, `phase`, `postcode`
- search geometry: `location` geography point suitable for radius search and distance calculation
- shortlist fields:
  - `pupil_count`
  - latest Ofsted label plus deterministic sort rank
  - one phase-aware academic headline metric label plus numeric sort value
  - explicit completeness or availability flags for headline metric and Ofsted
- optional trace fields for freshness and materialization versioning

## Data Sources

- `schools` for canonical identity, postcode, pupil count, and geolocation
- `school_ofsted_latest` for latest headline judgement
- `school_performance_yearly` for latest phase-appropriate academic metric

## Phase-Aware Metric Rules

- Primary-family rows use latest `ks2_combined_expected_pct`.
- Secondary-family rows use latest `progress8_average`.
- `All-through` rows may populate both families internally, but the search projection must publish the metric that matches the query-time family requested by the API contract.
- Missing or unsupported metrics must be stored explicitly rather than inferred from `NULL` alone.

## Request-Path Rules

- Do not build or refresh the projection in the web request path.
- Do not fan out into per-school profile queries after the initial postcode search.
- Distance from the searched postcode remains query-time because it depends on the user-supplied center point.

## Indexing Requirements

- spatial index on the search geometry field
- btree indexes on the common filter and sort helpers needed for postcode mode
- deterministic null ordering for Ofsted and academic sort values

## Acceptance Criteria

- One postcode search query can return all MVP table columns from a single backend read path.
- Projection rebuilds happen through the established Bronze -> Silver -> Gold workflow or an explicitly documented post-promote materialization step.
- Projection freshness is observable and does not depend on lazy web traffic.
