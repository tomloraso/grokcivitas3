.PHONY: setup lint test run run-backend run-web

setup:
	uv sync --project apps/backend --extra dev
	cd apps/web && npm install

lint:
	uv run --project apps/backend ruff check apps/backend
	uv run --project apps/backend ruff format --check apps/backend
	uv run --project apps/backend mypy apps/backend/src
	cd apps/web && npm run lint && npm run typecheck

test:
	uv run --project apps/backend pytest
	cd apps/web && npm run test

run:
	@echo "Run backend and web in separate terminals:"
	@echo "  make run-backend"
	@echo "  make run-web"

run-backend:
	uv run --project apps/backend uvicorn civitas.api.main:app --reload --host 0.0.0.0 --port 8000

run-web:
	cd apps/web && npm run dev

