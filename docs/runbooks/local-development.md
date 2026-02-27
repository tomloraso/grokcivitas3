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

## Dependency services

```bash
docker compose up -d postgres redis
```
