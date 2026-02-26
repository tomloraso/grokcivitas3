# Fullstack Bootstrap Template

Production-oriented full-stack monorepo starter with:

- Hexagonal Python backend (`domain`, `application`, `adapters`, `api`, `cli`)
- React + TypeScript frontend
- Opinionated quality gates (lint, format, typecheck, tests)
- CI/CD scaffolding
- Devcontainer, pre-commit, Docker Compose, Makefile
- Agent-ready operating docs (`AGENTS.md`, `.agents/*`, `agents/*`)

## Repository layout

```text
apps/backend  # FastAPI + hexagonal backend
apps/web      # React frontend
docs          # architecture + ADRs + runbooks
.agents       # agent execution guides
agents        # prompts and eval scaffolding
```

## Golden path feature

A small `tasks` feature is implemented end-to-end:

- Domain entity: `Task`
- Application use-case: create/list tasks via repository port
- Adapter: in-memory repository
- API: `POST /api/v1/tasks`, `GET /api/v1/tasks`
- Web: task creation/listing page

## Quickstart

```bash
make setup
make lint
make test
make run
```
