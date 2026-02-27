# Civitas

Civitas is a production-oriented full-stack monorepo for a UK public-data research platform.

Start with the product brief:
- `.planning/project-brief.md`

## Stack

- Backend: FastAPI + Python with layered architecture (`domain`, `application`, `infrastructure`, `api`, `cli`, `bootstrap`)
- Frontend: React + TypeScript
- Tooling: `uv`, npm, Makefile, pre-commit, Docker Compose
- Quality gates: lint, format, typecheck, unit/integration tests

## Repository layout

```text
apps/backend  # Python API + CLI service
apps/web      # Public-facing web app
docs          # Architecture, ADRs, runbooks
.planning     # Product/planning documents
.agents       # Agent execution guides
agents        # Prompt/eval scaffolding
tools         # Repo scripts
```

## Scaffold baseline

The repository currently includes a small `tasks` flow end-to-end as an architectural baseline.
It exists to validate wiring and quality gates and will be replaced by Civitas domain features.

## Quickstart

```bash
make setup
make lint
make test
make run
```

If `make` is unavailable (common on Windows shells), run the equivalent commands:

```bash
uv sync --project apps/backend --extra dev
cd apps/web && npm install
uv run --project apps/backend pytest
cd apps/web && npm run test
```

