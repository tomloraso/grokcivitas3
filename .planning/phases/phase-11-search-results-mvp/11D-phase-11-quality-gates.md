# 11D - Phase 11 Quality Gates

## Goal

Freeze the MVP cutline for the postcode-results-table phase and define the sign-off evidence required before implementation is considered complete.

## MVP In Scope

- postcode input on the main page
- fixed radius options `1`, `3`, `5`, `10`
- primary and secondary phase filtering
- server-side `closest`, `ofsted`, and `academic` sorts
- desktop results table and mobile stacked cards
- row fields for school identity, distance, phase, type, Ofsted, one academic metric, and pupil count
- compare entry and school detail navigation
- pipeline-maintained search summary projection

## Explicitly Out Of Scope

- blended proximity-plus-quality ranking
- custom weighting controls
- saved searches or saved preferences
- catchment probability
- travel-time search
- advanced demographic or admissions filters
- analytics expansion beyond whatever baseline search tracking already exists elsewhere

## Verification Requirements

- backend unit or integration coverage for:
  - projection mapping
  - phase-family bucketing
  - sort ordering
  - missing-metric handling
- API contract regeneration and frontend type sync
- frontend component coverage for:
  - desktop table states
  - mobile card states
  - sort explanation copy
  - compare interaction from results
- end-to-end coverage for:
  - postcode search success path
  - no-results path
  - phase filter plus sort change
  - add-to-compare from search and open compare route

## Performance Gates

- no request should trigger projection refresh or benchmark materialization inline
- postcode search should remain dominated by geo query cost, not multi-endpoint hydration
- sign-off should include measured evidence for the postcode search route under an MVP-sized radius query

## Acceptance Criteria

- Phase 11 ships only the narrowed MVP discussed in planning.
- The main search route becomes faster to interpret for shortlist building without adding opaque ranking behavior.
- Quality evidence includes repository lint, repository tests, and the agreed critical web journey coverage.
