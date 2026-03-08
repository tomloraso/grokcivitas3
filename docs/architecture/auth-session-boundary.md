# Auth Session Boundary

## Purpose

This page describes the implemented Phase 10 auth/session slice as it exists in the codebase today.
Use it as the architecture-level source of truth for how provider identity, Civitas sessions, public callback URLs, and web integration fit together.

Detailed setup and operator steps still live in:

- [Development Auth Provider Runbook](../runbooks/auth-development-provider.md)
- [Auth0 Managed Provider Runbook](../runbooks/auth0-managed-provider.md)
- [Local Development Runbook](../runbooks/local-development.md)

## Boundary

- The external provider verifies the upstream user identity.
- Civitas owns `UserAccount`, `AuthIdentity`, `AuthAttempt`, and `AppSession`.
- The browser talks only to Civitas auth routes.
- The web app does not import provider SDKs or store provider session state.
- Provider-specific behavior stays in backend infrastructure, bootstrap, and configuration.

## Public Route Contract

The current browser-facing auth contract is:

- `POST /api/v1/auth/start`
- `GET /api/v1/auth/callback`
- `GET /api/v1/session`
- `POST /api/v1/auth/signout`

The frontend calls these routes through relative `/api/v1/*` paths.

## Public Origin Model

The current slice assumes the browser reaches the API on the same public origin path space as the web app:

- Local development uses the Vite dev server on `http://localhost:5173` with `/api` proxied to the backend on `http://localhost:8000`.
- Managed environments may still run the backend on a separate upstream host, but the public browser-facing surface should proxy `/api/v1/*` through the web origin or an equivalent shared public origin.
- Auth0 callback configuration must use the public callback URL the browser can reach, not an internal upstream backend hostname that the frontend never calls directly.

Because of that:

- `CIVITAS_AUTH_ALLOWED_ORIGINS` must list browser origins exactly, such as `https://app.example.test`.
- It should not be treated as a list of internal backend upstream hosts.

## Request Flow

### 1. Start sign-in

- The web app submits email plus optional `return_to` to `POST /api/v1/auth/start`.
- The backend normalizes the email and sanitizes `return_to` to an internal path.
- Civitas generates a PKCE `code_verifier`, derives the S256 `code_challenge`, and stores the verifier in a short-lived `auth_attempts` record.
- Civitas issues a signed opaque auth `state` that contains only the auth-attempt identifier.
- The configured provider adapter returns the provider redirect URL.

### 2. Provider callback

- The browser returns to `GET /api/v1/auth/callback`.
- Civitas validates and decodes the signed `state`.
- Civitas consumes the matching auth attempt exactly once and rejects missing, expired, or replayed attempts.
- The provider adapter completes identity verification using the stored PKCE `code_verifier` when needed.
- Civitas upserts the internal user and auth identity mapping, creates a new app session, sets the first-party cookie, and redirects to the stored safe `return_to` path.

### 3. Session resolution

- The app shell loads `GET /api/v1/session`.
- The backend resolves the current user from the Civitas session cookie only.
- Missing, invalid, expired, revoked, or signed-out sessions resolve to the anonymous contract.

### 4. Sign-out

- The web app calls `POST /api/v1/auth/signout`.
- If a Civitas session cookie is present, the backend requires an exact trusted `Origin` match before revoking the session and clearing the cookie.
- Auth0 logout is not part of this slice; sign-out is Civitas-session-first.

## Provider Modes

### `development`

- Local/test-only scaffolding.
- Accepts any email address.
- Issues a signed development callback ticket locally.
- Must remain fenced to `local` or `test` runtime environments with loopback-only allowed origins.

### `auth0`

- Managed provider path for staging, production, and non-local rehearsals.
- Uses Auth0 Universal Login and the authorization-code flow with PKCE hardening.
- Civitas still owns the internal session and cookie lifecycle.

## Persistence

Current auth persistence is:

- `users`
- `auth_identities`
- `app_sessions`
- `auth_attempts`

`auth_attempts` is intentionally short-lived and consume-once. It exists to keep the PKCE verifier off the browser.

## Security Controls

- Civitas session cookie is `HttpOnly`.
- Cookie `Secure` and `SameSite` are environment-configured and validated at startup.
- Signed auth `state` is integrity-protected and time-limited.
- The PKCE verifier is stored server-side only.
- Callback failures fail closed for missing, expired, invalid, or replayed auth attempts.
- Cookie-authenticated POST routes validate `Origin` against the configured exact allowlist.
- The development provider is rejected outside `local` or `test`, and also rejected when any non-loopback auth origin is configured.

## Environment Variables

Core variables for this slice:

| Variable | Purpose |
|---|---|
| `CIVITAS_RUNTIME_ENVIRONMENT` | Runtime fence for `local`, `test`, `staging`, or `production` |
| `CIVITAS_AUTH_PROVIDER` | Selects `development` or `auth0` |
| `CIVITAS_AUTH_SESSION_COOKIE_NAME` | Civitas session cookie name |
| `CIVITAS_AUTH_SESSION_COOKIE_SECURE` | Controls the `Secure` cookie flag |
| `CIVITAS_AUTH_SESSION_COOKIE_SAMESITE` | Controls the `SameSite` cookie flag |
| `CIVITAS_AUTH_SESSION_TTL_HOURS` | App-session lifetime |
| `CIVITAS_AUTH_STATE_TTL_MINUTES` | Lifetime for signed auth state and short-lived auth attempts |
| `CIVITAS_AUTH_CALLBACK_ERROR_PATH` | Web route for callback failures |
| `CIVITAS_AUTH_ALLOWED_ORIGINS` | Exact browser origins allowed for cookie-authenticated POST routes |
| `CIVITAS_AUTH_SHARED_SECRET` | Signs auth state and development-provider callback tickets |
| `CIVITAS_AUTH_AUTH0_DOMAIN` | Auth0 tenant or custom domain |
| `CIVITAS_AUTH_AUTH0_CLIENT_ID` | Auth0 application client id |
| `CIVITAS_AUTH_AUTH0_CLIENT_SECRET` | Auth0 application client secret |
| `CIVITAS_AUTH_AUTH0_AUDIENCE` | Optional custom API audience |
| `CIVITAS_AUTH_AUTH0_CONNECTION` | Auth0 passwordless connection, currently `email` |

## Common Misconfiguration

`callback URL points at the wrong host`
- The browser is calling the public app origin, but the callback URL registered in Auth0 points at an upstream backend host the frontend does not use directly.
- Configure the public `/api/v1/auth/callback` URL that the browser actually reaches.

`sign-out fails with origin not allowed`
- The browser origin is not listed exactly in `CIVITAS_AUTH_ALLOWED_ORIGINS`.
- `localhost` and `127.0.0.1` are different values.

`development provider rejected at startup`
- The runtime environment is not `local` or `test`, or a non-loopback allowed origin is configured.

`session cookie set but app still looks anonymous`
- The browser is not reaching the same public `/api/v1/*` surface used for callback and session resolution, or the cookie settings do not match the deployment shape.
