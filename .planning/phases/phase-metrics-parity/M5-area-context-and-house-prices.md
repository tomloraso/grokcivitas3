# M5 - Area Context and House Prices

## Goal

Close remaining area-context gaps by adding IMD domain scores, crime rates, and house-price trends.

## Gap Coverage

- IMD domain scores (income, employment, education, crime, etc.)
- Crime rate per 1,000 with multi-year context
- House prices within configurable radius/time window with trend

## Source Strategy

1. Existing source extension:
   - extend `ons_imd` mapping for additional published domain columns.
2. Additional source required:
   - population denominator dataset for crime-rate normalization;
   - HM Land Registry / UK HPI dataset for house-price metrics.
3. Mandatory schema validation for each new endpoint/file before integration.

## Bronze -> Silver -> Gold Plan

1. Bronze:
   - keep current IMD ingest;
   - add population and house-price source ingests with manifest checksums.
2. Silver:
   - normalize IMD domains by LSOA;
   - normalize population by geography/year;
   - normalize property transactions/indices by geography/month.
3. Gold:
   - extend `area_deprivation` for domain scores;
   - add `area_crime_rate_context` (or extend existing crime table with denominator/rate fields);
   - add `area_house_price_context` with monthly/annual aggregates.

## API Plan

1. Extend area context payload with IMD domain score object.
2. Add crime-rate fields alongside incident counts.
3. Add house-price summary/trend fields and completeness metadata.

## Frontend Plan

1. Add IMD domain mini-grid and house-price cards.
2. Render crime counts and per-1,000 rates together.
3. Add trend visuals for house prices and crime rates.

## Validation and Gates

- Join-quality tests for postcode -> LSOA -> denominator alignment.
- Statistical sanity checks for rate calculations.
- Regression tests for existing area context cards.
