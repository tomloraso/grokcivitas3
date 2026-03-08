# Auth Guide

Use this guide for Phase 10 auth/session work.

## Required reference

- Read `docs/runbooks/auth-development-provider.md` before changing the local/test auth workflow.
- Read `docs/architecture/auth-session-boundary.md` when changing callback flow, provider routing, or public auth setup.

## Rules

- Treat the `development` provider as local/test-only scaffolding, not real identity proof.
- The current web auth slice assumes browser-facing `/api/v1/*` routes live on the same public origin path space as the web app. Local dev uses the Vite proxy; managed environments should preserve that browser-facing shape through a reverse proxy if needed.
- Keep `CIVITAS_AUTH_ALLOWED_ORIGINS` loopback-only while the development provider is enabled.
- `CIVITAS_AUTH_ALLOWED_ORIGINS` is a browser-origin allowlist, not a list of internal backend upstream hosts.
- Remember that origin matching is exact. `localhost` and `127.0.0.1` are not interchangeable.
- Keep cookie-authenticated POST routes behind origin validation.
- `CIVITAS_AUTH_SHARED_SECRET` signs auth state and development-provider tickets. Civitas sessions remain server-side records.
- When auth env vars, cookie behavior, callback behavior, or session lifecycle changes, update the runbook in `docs/runbooks/auth-development-provider.md`.

## Verification

Run from the repo root:

- `uv run --project apps/backend alembic -c apps/backend/alembic.ini upgrade head`
- `uv run --project apps/backend pytest`
- `uv run --project apps/backend ruff check apps/backend`
- `uv run --project apps/backend mypy apps/backend/src`
- `cd apps/web && npm run lint`
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run test`
