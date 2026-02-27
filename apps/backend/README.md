# Backend

Hexagonal Python backend service for Civitas.

## Layout

- `src/civitas/domain`: pure business logic.
- `src/civitas/application`: use-cases and ports.
- `src/civitas/infrastructure`: IO implementations.
- `src/civitas/api`: HTTP layer.
- `src/civitas/cli`: CLI layer.
- `src/civitas/bootstrap`: dependency composition.

## Commands

```bash
uv sync --project apps/backend --extra dev
uv run --project apps/backend ruff check apps/backend
uv run --project apps/backend mypy apps/backend/src
uv run --project apps/backend pytest
uv run --project apps/backend uvicorn civitas.api.main:app --reload
```

