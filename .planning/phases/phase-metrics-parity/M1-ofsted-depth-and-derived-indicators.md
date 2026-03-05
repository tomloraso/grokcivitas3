# M1 - Ofsted Depth and Derived Indicators

## Status

- Implemented on 2026-03-04.

## Goal

Close Ofsted quality gaps by exposing sub-judgements and a derived "time since last inspection" metric.

## Gap Coverage

- Ofsted sub-judgements (behaviour, leadership, quality of education) with dates.
- Time since last inspection.

## Source Strategy

- Existing sources only:
  - `ofsted_latest` CSV
  - `ofsted_timeline` inspection assets
- Live schema inspection captured from direct endpoint fetch of:
  - `https://www.gov.uk/government/statistical-data-sets/monthly-management-information-ofsteds-school-inspections-outcomes`
  - latest asset `Management_information_-_state-funded_schools_-_latest_inspections_as_at_31_Jan_2026.csv`
- Observed source headers used for implementation:
  - `Latest OEIF quality of education`
  - `Latest OEIF behaviour and attitudes`
  - `Latest OEIF personal development`
  - `Latest OEIF effectiveness of leadership and management`
  - `Inspection start date of latest OEIF graded inspection`
  - `Date of latest ungraded inspection`
  - `Ungraded inspection publication date`

## Bronze -> Silver -> Gold Plan

1. Bronze: no new source; persist current files/manifests unchanged.
2. Silver: extend normalization contracts in `contracts/ofsted_latest.py` and `contracts/ofsted_timeline.py` for sub-judgement fields when present.
3. Gold:
   - add new columns to `school_ofsted_latest` and/or `ofsted_inspections` for sub-judgements and judgement dates.
   - backfill migration from latest bronze snapshots.

## API Plan

1. Extend school profile schema with structured sub-judgements.
2. Add derived `days_since_last_inspection` and `last_inspection_date` fields.
3. Keep completeness semantics explicit when sub-judgements are not published.

## Frontend Plan

1. Add sub-judgement cards in the Ofsted section.
2. Add "Last inspected X days ago" indicator near current headline.
3. Display clear unavailable messaging when sub-judgements are absent upstream.

## Validation and Gates

- Contract tests for sub-judgement parsing on representative graded/ungraded rows.
- Integration tests for profile payload and timeline rendering.
- No regression in existing Ofsted headline/timeline behavior.

## Implementation Notes

1. Pipeline contract extended to `ofsted_latest.v2` with new sub-judgement and inspection-date fields.
2. Gold schema extended with migration `20260304_14_phase_m1_ofsted_subjudgements.py`.
3. API now exposes:
   - sub-judgement codes/labels,
   - `most_recent_inspection_date`,
   - `days_since_most_recent_inspection`.
4. Frontend now renders:
   - sub-judgement cards in profile header,
   - "Most recent inspection" age indicator.
