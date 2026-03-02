# Phase 2 Source Verification Snapshot (2026-03-02)

## Purpose

Evidence snapshot for the Phase 2 source contract gate (`2A-source-contract-gate.md`).

## Ofsted Timeline Checks

| Method | Endpoint | Result | Notes |
|---|---|---|---|
| GET | `https://www.gov.uk/government/statistical-data-sets/monthly-management-information-ofsteds-school-inspections-outcomes` | `200` | Landing page callable. |
| GET | `https://assets.publishing.service.gov.uk/media/698b20be235b57593bc1be33/Management_information_-_state-funded_schools_-_all_inspections_-_year_to_date_published_by_31_Jan_2026.csv` | `200` | Latest YTD all-inspections asset callable. |
| GET | `https://assets.publishing.service.gov.uk/media/698b20be95285e721cd7127d/Management_information_-_state-funded_schools_-_latest_inspections_as_at_31_Jan_2026.csv` | `200` | Latest latest-inspections asset callable. |
| GET | `https://assets.publishing.service.gov.uk/media/5f6b4b76d3bf7f72337b6ef7/Management_information_-_state-funded_schools_1_September_2015_to_31_August_2019.csv` | `200` | Historical baseline asset callable. |

Validated `all_inspections` YTD header includes:

- `URN`
- `Inspection number`
- `Inspection type`
- `Inspection start date`
- `Publication date`
- `Category of concern`
- `Leadership and governance`

Observed latest YTD asset coverage (Jan 2026 file):

- rows: `132`
- unique URN: `132`
- inspection date range: `2025-11-11` to `2026-01-15`

Validated 2015-2019 historical file nuance:

- line 1 is metadata text (not header),
- line 2 is CSV header beginning with:
  - `Academic year`
  - `URN`
  - `Inspection number`
  - `Inspection start date`
  - `Publication date`
  - `Overall effectiveness`

Observed 2015-2019 historical coverage after preamble skip:

- rows: `23109`
- unique URN: `18172`
- inspection date range: `2015-09-14` to `2019-07-18`

## ONS IMD Checks

| Method | Endpoint | Result | Notes |
|---|---|---|---|
| GET | `https://www.gov.uk/government/statistics/english-indices-of-deprivation-2025` | `200` | IoD2025 release page callable. |
| GET | `https://assets.publishing.service.gov.uk/media/691ded56d140bbbaa59a2a7d/File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv` | `200` | IoD2025 File 7 CSV callable. |
| GET | `https://www.gov.uk/government/statistics/english-indices-of-deprivation-2019` | `200` | IoD2019 release page callable. |
| GET | `https://assets.publishing.service.gov.uk/media/5dc407b440f0b6379a7acc8d/File_7_-_All_IoD2019_Scores__Ranks__Deciles_and_Population_Denominators_3.csv` | `200` | IoD2019 File 7 CSV callable fallback. |

Validated IoD2025 File 7 required columns include:

- `LSOA code (2021)`
- `LSOA name (2021)`
- `Index of Multiple Deprivation (IMD) Decile (where 1 is most deprived 10% of LSOAs)`
- `Income Deprivation Affecting Children Index (IDACI) Score (rate)`
- `Income Deprivation Affecting Children Index (IDACI) Decile (where 1 is most deprived 10% of LSOAs)`

Observed IoD2025 File 7 row count:

- `33755`

Validated IoD2019 fallback File 7 has corresponding legacy columns:

- `LSOA code (2011)`
- IMD decile field
- IDACI score field
- IDACI decile field

## Police UK Checks

| Method | Endpoint | Result | Notes |
|---|---|---|---|
| GET | `https://data.police.uk/data/archive/` | `200` | Archive index callable. |
| GET | `https://data.police.uk/data/archive/2026-01.zip` | `302` -> `200` | Monthly archive asset callable, `application/zip`. |
| GET | `https://data.police.uk/about/#columns` | `200` | Archive URL pattern + CSV column definitions. |
| GET | `https://data.police.uk/api/crime-last-updated` | `200` | Returns latest month marker. |
| GET | `https://data.police.uk/api/crimes-street-dates` | `200` | Returns available month list. |
| GET | `https://data.police.uk/api/crime-categories?date=2026-01` | `200` | Returns categories list for month. |
| GET | `https://data.police.uk/api/crimes-street/all-crime?lat=51.5072&lng=-0.1276&date=2026-01` | `200` | Returns street-level JSON records. |

Validated archive-pattern evidence:

- archive page lists links through `2026-01`:
  - `/data/archive/2025-12.zip`
  - `/data/archive/2026-01.zip`
- `2026-01.zip` response metadata:
  - `Content-Type: application/zip`
  - `Content-Length: 1746908436`
  - `Accept-Ranges: bytes`

Validated API sample response keys from `crimes-street/all-crime`:

- top-level keys:
  - `category`
  - `location_type`
  - `location`
  - `context`
  - `outcome_status`
  - `persistent_id`
  - `id`
  - `location_subtype`
  - `month`
- nested location keys:
  - `latitude`
  - `longitude`
  - `street.id`
  - `street.name`

Validated API limits reference:

- `https://data.police.uk/docs/api-call-limits/` documents:
  - `15 requests per second with a burst of 30`,
  - `429` response when limit exceeded.

## Supporting Postcode Geography Check

| Method | Endpoint | Result | Notes |
|---|---|---|---|
| GET | `https://api.postcodes.io/postcodes/SW1A2AA` | `200` | Verified LSOA code availability for deprivation joins. |

Validated fields include:

- `result.lsoa`
- `result.codes.lsoa`
- `result.latitude`
- `result.longitude`

Sample values:

- `result.lsoa`: `Westminster 018C`
- `result.codes.lsoa`: `E01004736`

## Summary

Phase 2 source families are callable with verified contracts.

Important implementation implications from this snapshot:

1. Ofsted full history cannot come from a single latest YTD file; it requires historical backfill assets.
2. IMD 2025 File 7 provides both deprivation and child-poverty proxy fields (IDACI) in one CSV.
3. Police monthly archive is available and suitable for reproducible Bronze ingest, but file sizes are large.
4. Postcodes.io exposes LSOA codes needed for robust deprivation joins.
