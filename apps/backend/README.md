# Backend

Hexagonal Python backend template.

## Layout

- `src/bootstrap_app/domain`: pure business logic.
- `src/bootstrap_app/application`: use-cases and ports.
- `src/bootstrap_app/adapters`: IO implementations.
- `src/bootstrap_app/contracts`: transport DTOs.
- `src/bootstrap_app/api`: HTTP layer.
- `src/bootstrap_app/cli`: CLI layer.

## Commands

```bash
uv sync --project apps/backend --extra dev
uv run --project apps/backend ruff check apps/backend
uv run --project apps/backend mypy apps/backend/src
uv run --project apps/backend pytest
uv run --project apps/backend uvicorn bootstrap_app.api.main:app --reload
```
