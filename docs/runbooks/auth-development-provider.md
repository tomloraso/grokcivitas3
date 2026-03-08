# Development Auth Provider Runbook

## Purpose

This runbook documents the local and test-only authentication flow used in Phase 10 alongside the selected external provider path.

Use it when:

- running the Phase 10 auth/session slice locally
- validating cookie/session behavior in development
- exercising auth/session code without depending on external-provider availability
- updating auth/session foundation code, docs, or tests

Do not use it as evidence that production identity is solved. The `development` provider is scaffolding only.

See [Auth Session Boundary](../architecture/auth-session-boundary.md) for the architecture-level summary of the implemented flow.

## Relationship To Auth0

- `Auth0` is the implemented managed-provider path for staging, production, and any non-local rehearsal.
- The `development` provider remains available after Auth0 is adopted so local and test flows still have a no-provider option.
- The `development` provider must remain fenced to `local` or `test` environments with loopback-only origins.
- Staging and production must use the managed-provider path, not this runbook.

## Guardrails

- `CIVITAS_AUTH_PROVIDER=development` is allowed only in `local` or `test` runtime environments.
- The backend rejects the `development` provider if `CIVITAS_AUTH_ALLOWED_ORIGINS` contains any non-loopback origin.
- The development provider accepts any email address and issues a signed callback locally. It does not prove real user identity.
- `CIVITAS_AUTH_ALLOWED_ORIGINS` is an exact origin allowlist. `http://localhost:5173` and `http://127.0.0.1:5173` are different values.
- Cookie-authenticated POST routes such as sign-out require a trusted `Origin` header that matches the configured allowlist.

## Public Route Shape

Local development uses the browser-facing `/api/v1/*` routes on the web origin:

- Browse the app at `http://localhost:5173`
- Vite proxies `/api/*` to the backend at `http://localhost:8000`
- The backend therefore generates callback URLs on the current public web origin, for example `http://localhost:5173/api/v1/auth/callback`

If you bypass the web origin and call the backend directly from a different browser origin, update the allowed-origin list and expect callback URLs to follow the origin that reached `POST /api/v1/auth/start`.

## Required Local Configuration

Typical local values in `.env`:

```bash
CIVITAS_RUNTIME_ENVIRONMENT=local
CIVITAS_AUTH_PROVIDER=development
CIVITAS_AUTH_SESSION_COOKIE_NAME=civitas_session
CIVITAS_AUTH_SESSION_COOKIE_SECURE=false
CIVITAS_AUTH_SESSION_COOKIE_SAMESITE=lax
CIVITAS_AUTH_SESSION_TTL_HOURS=336
CIVITAS_AUTH_STATE_TTL_MINUTES=15
CIVITAS_AUTH_CALLBACK_ERROR_PATH=/sign-in
CIVITAS_AUTH_ALLOWED_ORIGINS=http://localhost:5173
CIVITAS_AUTH_SHARED_SECRET=civitas-local-dev-shared-secret
```

If the web app is running on a different origin, update `CIVITAS_AUTH_ALLOWED_ORIGINS` to match it exactly. Keep the list loopback-only while the development provider is in use.
`CIVITAS_AUTH_SHARED_SECRET` signs the auth `state` token and the development-provider callback ticket.

## Startup

Run from the repo root:

```bash
docker compose up -d postgres redis
uv run --project apps/backend alembic -c apps/backend/alembic.ini upgrade head
uv run --project apps/backend uvicorn civitas.api.main:app --reload --host 0.0.0.0 --port 8000
cd apps/web && npm run dev
```

Canonical command references live in [.agents/tooling.md](../../.agents/tooling.md).

## Manual Browser Workflow

1. Open the web app using the exact origin listed in `CIVITAS_AUTH_ALLOWED_ORIGINS`.
2. Navigate to `/sign-in`.
3. Enter any email address and submit.
4. The backend will:
   - accept the email
   - create a short-lived auth attempt plus signed opaque `state`
   - issue a signed development callback on the current public web origin via `/api/v1/auth/callback`
   - create a Civitas session
   - set the `civitas_session` cookie
5. Confirm the app returns to the requested page and the header shows the signed-in state.
6. Click `Sign out` and confirm the header returns to anonymous state.

## API Smoke Checks

Before sign-in:

```bash
curl http://localhost:8000/api/v1/session
```

Expected result: `state=anonymous`.

After sign-in in the browser, repeat the call with the browser session or inspect the app state in the UI.

Relevant endpoints:

- `POST /api/v1/auth/start`
- `GET /api/v1/auth/callback`
- `GET /api/v1/session`
- `POST /api/v1/auth/signout`

## Common Failure Modes

`origin not allowed`
- The browser origin does not exactly match `CIVITAS_AUTH_ALLOWED_ORIGINS`.
- Fix the env value or browse using the configured origin.

Backend fails to start with a development-provider validation error
- `CIVITAS_RUNTIME_ENVIRONMENT` is not `local` or `test`, or the allowlist contains a non-loopback origin.
- Reset to local/test-only values.

Session does not persist
- The backend was not restarted after `.env` changes.
- The browser is on a different origin than the allowlist.
- Cookie settings were changed away from the local defaults.

Unexpected callback error
- The signed callback state or ticket is stale or invalid, or the short-lived auth attempt has already been consumed.
- Start the sign-in flow again from `/sign-in`.

Callback lands on the wrong host or port
- The browser is not reaching the auth start route on the same public origin that should own `/api/v1/auth/callback`.
- Use the Vite web origin locally, or align your proxy setup so `/api/v1/*` is exposed on the browser-facing origin.

## Change Management

When auth/session behavior changes, update this runbook and these references together:

- [Local Development Runbook](./local-development.md)
- [Auth0 Managed Provider Runbook](./auth0-managed-provider.md)
- [docs/index.md](../index.md)
- [.agents/auth.md](../../.agents/auth.md)
- [AGENTS.md](../../AGENTS.md)

## Ongoing Role After Auth0 Adoption

This runbook remains the primary reference for the no-provider local or test-only flow after Auth0 is adopted. At that point:

- keep this runbook current for local development and automated test usage
- document Auth0 setup separately for staging or production operation
- keep agent guidance explicit that `development` is a local or test-only option, not the default managed-provider path
