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

## Dependency services

```bash
docker compose up -d postgres redis
```
