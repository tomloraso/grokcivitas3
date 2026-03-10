# Tooling Guide

Run all commands from the repo root.

## Setup

- `uv sync --project apps/backend --extra dev`
- `cd apps/web && npm install`
- Backend API, CLI, and pytest read env-backed settings from the repo-root `.env` through the
  shared settings module. Keep `CIVITAS_DATABASE_URL` and `CIVITAS_TEST_DATABASE_URL` there for
  normal local work.

## Backend

- DB migrations: `uv run --project apps/backend alembic -c apps/backend/alembic.ini upgrade head`
- Lint: `uv run --project apps/backend ruff check apps/backend`
- Format check: `uv run --project apps/backend ruff format --check apps/backend`
- Format: `uv run --project apps/backend ruff format apps/backend`
- Typecheck: `uv run --project apps/backend mypy apps/backend/src`
- Tests: `uv run --project apps/backend pytest`
- Pipeline run: `uv run --project apps/backend civitas pipeline run --source gias`
- Dev API: `uv run --project apps/backend uvicorn civitas.api.main:app --reload --host 0.0.0.0 --port 8000`
- Do not add per-command dotenv parsing or shell-only exports to work around broken settings
  resolution. Fix `AppSettings` or shared test bootstrap instead.

## Web

- Lint: `cd apps/web && npm run lint`
- Typecheck: `cd apps/web && npm run typecheck`
- Unit tests: `cd apps/web && npm run test`
- Build: `cd apps/web && npm run build`
- Dev app: `cd apps/web && npm run dev`

## Combined

- `make setup`
- `make lint`
- `make test`
- `make run`

## Pipelines

- Canonical Bronze root is `data/bronze` (`CIVITAS_BRONZE_ROOT`).
- Pipeline operational guidance: `docs/runbooks/pipelines.md`.

