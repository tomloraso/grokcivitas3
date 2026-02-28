# Tooling Guide

Run all commands from the repo root.

## Setup

- `uv sync --project apps/backend --extra dev`
- `cd apps/web && npm install`

## Backend

- DB migrations: `uv run --project apps/backend alembic -c apps/backend/alembic.ini upgrade head`
- Lint: `uv run --project apps/backend ruff check apps/backend`
- Format check: `uv run --project apps/backend ruff format --check apps/backend`
- Format: `uv run --project apps/backend ruff format apps/backend`
- Typecheck: `uv run --project apps/backend mypy apps/backend/src`
- Tests: `uv run --project apps/backend pytest`
- Pipeline run: `uv run --project apps/backend civitas pipeline run --source gias`
- Dev API: `uv run --project apps/backend uvicorn civitas.api.main:app --reload --host 0.0.0.0 --port 8000`

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

