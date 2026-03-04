# Local Development Runbook

## Prerequisites

- Python 3.11+
- uv
- Node.js 20+
- Docker Desktop (optional)

## First setup

```bash
make setup
```

## Configuration setup

Create a local `.env` from the committed baseline:

```bash
cp .env.example .env
```

PowerShell:

```powershell
Copy-Item .env.example .env
```

Backend runtime configuration is loaded from `.env` via the shared settings module.

Frontend (Vite) optional map tile configuration lives in `apps/web/.env.example`:

```bash
# apps/web/.env
VITE_MAP_TILE_PROVIDER=cartodb-dark-matter
# Optional: enables Stadia dark fallback
# VITE_STADIA_MAPS_API_KEY=...
```

## Daily commands

```bash
make lint
make test
make run
```

If `make` is not installed in your shell, run commands directly:

```bash
uv run --project apps/backend ruff check apps/backend
uv run --project apps/backend mypy apps/backend/src
uv run --project apps/backend pytest
cd apps/web && npm run lint && npm run typecheck && npm run test
```

## Web quality rails

Run these before signing off web foundation or layout changes:

```bash
cd apps/web && npm run build
cd apps/web && npm run budget:check
cd apps/web && npm run lighthouse:check
```

The latest Lighthouse snapshot is stored at `apps/web/artifacts/lighthouse/latest.json`.

## Map tile provider governance

Before production release:

1. Confirm primary provider attribution text is visible in map attribution UI.
2. Verify fallback provider behavior by forcing a primary tile error and ensuring failover occurs.
3. Validate current terms/usage limits for the selected providers and record any changes in release notes.

## Dependency services

```bash
docker compose up -d postgres redis
```

## Database migrations

Run migrations after starting Postgres:

```bash
uv run --project apps/backend alembic -c apps/backend/alembic.ini upgrade head
```

Set `CIVITAS_DATABASE_URL` in `.env` to target a different database.

## Pipeline baseline commands

```bash
uv run --project apps/backend python tools/scripts/verify_phase1_sources.py
uv run --project apps/backend python tools/scripts/verify_phase2_sources.py
uv run --project apps/backend python tools/scripts/verify_source_contracts_runtime.py
uv run --project apps/backend python tools/scripts/discover_dfe_characteristics_history.py
uv run --project apps/backend civitas pipeline run --source gias
uv run --project apps/backend civitas pipeline run --source dfe_characteristics
uv run --project apps/backend civitas pipeline backfill --source dfe_characteristics --lookback-years 5
uv run --project apps/backend civitas pipeline run --source ons_imd
uv run --project apps/backend civitas pipeline run --source police_crime_context
uv run --project apps/backend civitas pipeline run --source ofsted_latest
uv run --project apps/backend civitas pipeline run --source ofsted_timeline
uv run --project apps/backend civitas pipeline run --source gias --resume
uv run --project apps/backend civitas pipeline resume --run-id <pipeline-run-id>
uv run --project apps/backend civitas pipeline run --all
uv run --project apps/backend civitas ops data-quality snapshot
uv run --project apps/backend python tools/scripts/check_data_quality_slo.py --strict
uv run --project apps/backend python tools/scripts/run_pipeline_recovery_drill.py --strict
uv run --project apps/backend python tools/scripts/benchmark_pipeline_throughput.py --strict
```

For GIAS runs, set one of these optional source inputs in `.env` when automatic site download is unavailable:

```bash
# Local CSV file
CIVITAS_GIAS_SOURCE_CSV=C:\path\to\edubasealldata.csv

# Local ZIP file (must contain edubasealldata*.csv)
CIVITAS_GIAS_SOURCE_ZIP=C:\path\to\extract.zip

# Or HTTP URL for CSV/ZIP
CIVITAS_GIAS_SOURCE_CSV=https://example.com/edubasealldata.csv
```

GIAS staging accepts `OpenDate` / `CloseDate` values in both `DD/MM/YYYY` and
`DD-MM-YYYY` formats (with optional time components) to match current upstream extracts.

For DfE characteristics runs, these optional `.env` values control dataset selection and manual CSV override:

```bash
# Local CSV file or HTTP URL override
CIVITAS_DFE_CHARACTERISTICS_SOURCE_CSV=C:\path\to\school_characteristics.csv

# Defaults to validated Phase 1 dataset id when not set
CIVITAS_DFE_CHARACTERISTICS_DATASET_ID=019afee4-ba17-73cb-85e0-f88c101bb734

# Default historical lookback used by `pipeline backfill` when --lookback-years is omitted
CIVITAS_DFE_CHARACTERISTICS_LOOKBACK_YEARS=5

# Guardrail: must be true to run backfill mode
CIVITAS_DFE_CHARACTERISTICS_BACKFILL_ENABLED=false

# Optional explicit historical dataset id catalog (comma-separated)
# CIVITAS_DFE_CHARACTERISTICS_DATASET_CATALOG=dataset-id-2023,dataset-id-2024,dataset-id-2025
```

Historical backfill safety notes:
- Keep daily incremental and historical backfill separate: use `pipeline run` for daily and `pipeline backfill` for historical hydration only.
- Use `tools/scripts/discover_dfe_characteristics_history.py` to generate a candidate inventory before setting `CIVITAS_DFE_CHARACTERISTICS_DATASET_CATALOG`.
- Backfill writes per-asset provenance (`source_dataset_id`, `source_dataset_version`) into `school_demographics_yearly` by academic year.

For ONS IMD runs, these optional `.env` values control release selection and manual source override:

```bash
# Local CSV file or HTTP URL override
CIVITAS_IMD_SOURCE_CSV=C:\path\to\File_7_IoD2025.csv

# Release selector used when source override is unset (iod2025 or iod2019)
CIVITAS_IMD_RELEASE=iod2025
```

For Police crime context runs, these optional `.env` values control archive source and aggregation behavior:

```bash
# Explicit archive URL or local ZIP override
CIVITAS_POLICE_CRIME_SOURCE_ARCHIVE_URL=https://data.police.uk/data/archive/2026-01.zip

# Source mode: archive (default) or api (explicit fail-fast for bulk runs)
CIVITAS_POLICE_CRIME_SOURCE_MODE=archive

# Radius used by ST_DWithin aggregation into area_crime_context
CIVITAS_POLICE_CRIME_RADIUS_METERS=1609.344
```

For Ofsted latest runs, this optional `.env` value overrides landing-page auto-resolution with a local file or URL:

```bash
CIVITAS_OFSTED_LATEST_SOURCE_CSV=C:\path\to\latest_inspections.csv
```

For Ofsted timeline runs, these optional `.env` values control source resolution:

```bash
# Override landing page source
CIVITAS_OFSTED_TIMELINE_SOURCE_INDEX_URL=https://www.gov.uk/government/statistical-data-sets/monthly-management-information-ofsteds-school-inspections-outcomes

# Rolling academic-year window used when selecting all_inspections assets
# (default 10 years; set to 5 for lighter local runs)
CIVITAS_OFSTED_TIMELINE_YEARS=10

# Comma-separated explicit asset list (local paths and/or URLs) for emergency pinning
# CIVITAS_OFSTED_TIMELINE_SOURCE_ASSETS=C:\path\to\all_inspections_2024.csv,C:\path\to\all_inspections_2025.csv

# Include 2015-2019 baseline during landing-page resolution
CIVITAS_OFSTED_TIMELINE_INCLUDE_HISTORICAL_BASELINE=true
```

For postcode search API behavior, these optional `.env` values control resolver and cache behavior:

```bash
CIVITAS_POSTCODES_IO_BASE_URL=https://api.postcodes.io
CIVITAS_POSTCODE_CACHE_TTL_DAYS=30
```

For pipeline run quality gates, these optional `.env` values set per-source maximum reject ratios
(`rejected_rows / downloaded_rows`). Defaults are `1.0` for all sources. Hard gates for
`downloaded_rows`, `staged_rows`, and `promoted_rows` are always enforced.

```bash
CIVITAS_PIPELINE_MAX_REJECT_RATIO_GIAS=1.0
CIVITAS_PIPELINE_MAX_REJECT_RATIO_DFE_CHARACTERISTICS=1.0
CIVITAS_PIPELINE_MAX_REJECT_RATIO_OFSTED_LATEST=1.0
CIVITAS_PIPELINE_MAX_REJECT_RATIO_OFSTED_TIMELINE=1.0
CIVITAS_PIPELINE_MAX_REJECT_RATIO_ONS_IMD=1.0
CIVITAS_PIPELINE_MAX_REJECT_RATIO_POLICE_CRIME_CONTEXT=1.0
```

For H6 pipeline resilience controls, these optional `.env` values tune retry, chunking, resume,
and source concurrency behavior:

```bash
CIVITAS_PIPELINE_HTTP_TIMEOUT_SECONDS=60
CIVITAS_PIPELINE_MAX_RETRIES=2
CIVITAS_PIPELINE_RETRY_BACKOFF_SECONDS=0.5
CIVITAS_PIPELINE_STAGE_CHUNK_SIZE=1000
CIVITAS_PIPELINE_PROMOTE_CHUNK_SIZE=1000
CIVITAS_PIPELINE_MAX_CONCURRENT_SOURCES=1
CIVITAS_PIPELINE_RESUME_ENABLED=true
```

For H5 operational observability checks, these optional `.env` values tune strict SLO evaluation:

```bash
# Per-source freshness SLA (hours).
CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_GIAS=720
CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_DFE_CHARACTERISTICS=720
CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_OFSTED_LATEST=720
CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_OFSTED_TIMELINE=720
CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_ONS_IMD=720
CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_POLICE_CRIME_CONTEXT=720

# Day-over-day coverage drop threshold (absolute ratio delta).
CIVITAS_DATA_QUALITY_COVERAGE_DRIFT_THRESHOLD=0.05

# Trigger when consecutive hard failures are greater than this value.
CIVITAS_DATA_QUALITY_MAX_CONSECUTIVE_HARD_FAILURES=2

# Trigger sparse-trend warning when (zero-year + one-year schools) / total exceeds this ratio.
CIVITAS_DATA_QUALITY_SPARSE_TREND_RATIO_THRESHOLD=0.7
```

## Data quality triage flow

1. Capture a daily observability snapshot:
   `uv run --project apps/backend civitas ops data-quality snapshot`
2. Evaluate strict SLO state:
   `uv run --project apps/backend python tools/scripts/check_data_quality_slo.py --strict`
   - `--strict` exits non-zero for `critical` alerts and still prints `warning` alerts.
3. If freshness alerts fire:
   - inspect `pipeline_run_events` and `pipeline_runs` for the source status history and latest `finished_at`.
4. If coverage drift alerts fire:
   - compare `data_quality_snapshots` day-over-day for the section and source.
   - check same-day `pipeline_run_events` for `failed_quality_gate` / `failed_source_unavailable`.
5. If sparse-trend risk alerts fire:
   - review demographics trend-year distribution from the snapshot (`0`, `1`, `2+` year counts).
   - confirm whether source coverage changed or joins/regressions reduced promoted records.

`postcode_cache` stores both `lsoa` (name) and `lsoa_code`. If a cached row predates
`lsoa_code` backfill, the resolver automatically refreshes it from Postcodes.io on the next
postcode search.

`GET /api/v1/schools/{urn}` also performs a best-effort postcode context refresh when
deprivation is missing for a school postcode, so profile area context does not depend on
whether a user has run postcode search first.
