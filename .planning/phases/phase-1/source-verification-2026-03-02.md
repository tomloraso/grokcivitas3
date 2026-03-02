# Phase 1 Source Verification Snapshot (2026-03-02)

## Purpose

Evidence snapshot for the Phase 1 source contract gate (`1A-source-contract-gate.md`).

## DfE Statistics API Checks

Base URL: `https://api.education.gov.uk/statistics/v1`

| Method | Endpoint | Result | Notes |
|---|---|---|---|
| GET | `/publications?page=1&pageSize=20` | `200` | Publications endpoint callable. |
| GET | `/publications/{publicationId}/data-sets?page=1&pageSize=20` | `200` | Dataset discovery callable. |
| GET | `/data-sets/{dataSetId}` | `200` | Dataset summary callable. |
| GET | `/data-sets/{dataSetId}/meta` | `200` | Filter/indicator metadata callable. |
| GET | `/data-sets/{dataSetId}/query?page=1&pageSize=1` | `200` | Row-level query callable. |
| GET | `/data-sets/{dataSetId}/csv` | `200` | CSV export callable. |

Validated dataset candidate for school-level demographics:

- publication: `Key stage 2 attainment`
- dataset: `Key stage 2 institution level - Schools (School information)`
- data set id: `019afee4-ba17-73cb-85e0-f88c101bb734`

Validated CSV header includes:

- `school_urn`
- `time_period`
- `ptfsm6cla1a`
- `psenelek`
- `psenelk`
- `psenele`
- `ptealgrp2`
- `ptealgrp1`
- `ptealgrp3`

Observed constraints:

1. No school-level ethnicity fields found in currently validated DfE endpoint set.
2. Current validated school-level demographic dataset exposes one academic year (`2024/25`) in metadata.

## Ofsted Latest Checks

Landing page:

- `GET https://www.gov.uk/government/statistical-data-sets/monthly-management-information-ofsteds-school-inspections-outcomes` -> `200`

Resolved latest asset link on 2026-03-02:

- `https://assets.publishing.service.gov.uk/media/698b20be95285e721cd7127d/Management_information_-_state-funded_schools_-_latest_inspections_as_at_31_Jan_2026.csv` -> `200`

Validated CSV headers include:

- `URN`
- `Inspection start date`
- `Publication date`
- `Latest OEIF overall effectiveness`
- `Ungraded inspection overall outcome`

Observed value set for `Latest OEIF overall effectiveness` in sampled run:

- `1`
- `2`
- `3`
- `4`
- `Not judged`

## Summary

Phase 1 source families are callable with verified contracts.

Known source coverage gaps and depth limits are explicit and must be represented in Phase 1 data/API/UI behavior:

- school-level ethnicity not currently available in validated DfE endpoint set,
- demographic history depth currently limited for validated school-level dataset.
