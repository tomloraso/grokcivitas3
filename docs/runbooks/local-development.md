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
uv run --project apps/backend civitas pipeline run --source gias
uv run --project apps/backend civitas pipeline run --all
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

For postcode search API behavior, these optional `.env` values control resolver and cache behavior:

```bash
CIVITAS_POSTCODES_IO_BASE_URL=https://api.postcodes.io
CIVITAS_POSTCODE_CACHE_TTL_DAYS=30
```
