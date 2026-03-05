# M5 - Area Context and House Prices

## Status

- Implementation: complete
- Quality gate (tests/lint on touched scope): complete
- Post-M6 full pipeline/API end-to-end validation: complete (2026-03-05)
- Milestone handover state: ready for frontend testing

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

## Delivered Backend Scope

1. Schema + migration:
   - `area_deprivation` extended with IMD domain scores/ranks/deciles and `population_total`.
   - New `area_house_price_context` table added with monthly LAD-level price context.
2. Source contracts/pipelines:
   - `ons_imd` contract + promote path extended for IMD domain fields and population.
   - New `uk_house_prices` contract and pipeline added (`download -> stage -> promote`).
3. Runtime/config wiring:
   - `PipelineSource.UK_HOUSE_PRICES` added and registered.
   - Runner dataset/section mapping added (`area_house_price_context` / `area_house_prices`).
   - Settings + data-quality config paths added for house-price source.
4. Profile + API exposure:
   - Area deprivation payload expanded with IMD domain and LAD context fields.
   - Area crime now includes denominator + per-1,000 rates + annual rate context.
   - Area house-price block + trend + completeness/coverage exposed via use-case + API mapping.
5. Data quality:
   - New `area_house_prices` section support added in domain model and repository metrics.

## Quality Gate Evidence

- Expanded M5-focused test gate command:
  - `uv run --project apps/backend pytest apps/backend/tests/unit/test_ons_imd_transforms.py apps/backend/tests/integration/test_ons_imd_pipeline.py apps/backend/tests/unit/test_pipeline_cli.py apps/backend/tests/unit/test_pipeline_contract_metadata.py apps/backend/tests/unit/test_settings.py apps/backend/tests/integration/test_data_quality_repository.py apps/backend/tests/integration/test_school_profile_repository.py apps/backend/tests/integration/test_school_profile_api.py apps/backend/tests/unit/test_get_school_profile_use_case.py apps/backend/tests/unit/test_cached_school_profile_repository.py apps/backend/tests/unit/test_uk_house_prices_contract.py apps/backend/tests/integration/test_uk_house_prices_pipeline.py`
  - Result: `71 passed` (2026-03-05).
- Lint on changed M5 test scope:
  - `uv run --project apps/backend ruff check apps/backend/tests/unit/test_uk_house_prices_contract.py apps/backend/tests/integration/test_uk_house_prices_pipeline.py apps/backend/tests/integration/test_data_quality_repository.py apps/backend/tests/integration/test_school_profile_repository.py apps/backend/tests/integration/test_school_profile_api.py apps/backend/tests/unit/test_get_school_profile_use_case.py apps/backend/tests/unit/test_cached_school_profile_repository.py apps/backend/tests/integration/test_ons_imd_pipeline.py`
  - Result: all checks passed.

## Handover State

- M5 is validated end-to-end and ready for frontend testing.
- Post-M6 combined validation executed for M2-M6.

## Post-M6 Validation Evidence

- Command:
  - `uv run --project apps/backend pytest apps/backend/tests/unit/test_demographics_spc_contract.py apps/backend/tests/unit/test_demographics_sen_contract.py apps/backend/tests/unit/test_dfe_attendance_contract.py apps/backend/tests/unit/test_dfe_behaviour_contract.py apps/backend/tests/unit/test_dfe_workforce_contract.py apps/backend/tests/unit/test_uk_house_prices_contract.py apps/backend/tests/unit/test_ons_imd_transforms.py apps/backend/tests/unit/test_pipeline_cli.py apps/backend/tests/unit/test_pipeline_contract_metadata.py apps/backend/tests/unit/test_settings.py apps/backend/tests/integration/test_demographics_release_files_pipeline.py apps/backend/tests/integration/test_dfe_characteristics_pipeline.py apps/backend/tests/integration/test_dfe_attendance_pipeline.py apps/backend/tests/integration/test_dfe_behaviour_pipeline.py apps/backend/tests/integration/test_dfe_workforce_pipeline.py apps/backend/tests/integration/test_ons_imd_pipeline.py apps/backend/tests/integration/test_uk_house_prices_pipeline.py apps/backend/tests/integration/test_data_quality_repository.py apps/backend/tests/integration/test_school_profile_repository.py apps/backend/tests/integration/test_school_profile_api.py apps/backend/tests/unit/test_get_school_profile_use_case.py apps/backend/tests/unit/test_cached_school_profile_repository.py apps/backend/tests/integration/test_school_trends_repository.py apps/backend/tests/integration/test_school_trends_api.py apps/backend/tests/unit/test_get_school_trends_use_case.py apps/backend/tests/unit/test_api_contract_checks.py -q`
- Result:
  - `129 passed`
