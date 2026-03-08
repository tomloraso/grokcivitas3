# Auth0 Managed Provider Runbook

## Purpose

This runbook documents the managed Auth0 configuration that now backs the Phase 10 login slice outside the local or test-only `development` provider.

Use it when:

- configuring staging or production login
- rehearsing the managed-provider callback flow on a non-local environment
- rotating Auth0 tenant or application settings
- validating the Auth0 round-trip without changing the Civitas session boundary

See [Auth Session Boundary](../architecture/auth-session-boundary.md) for the architecture-level summary of the implemented flow.

## Boundary

- Auth0 verifies the upstream user identity.
- Civitas owns the internal `UserAccount`, `AuthIdentity`, and `AppSession` records.
- The browser still starts sign-in through `POST /api/v1/auth/start`.
- The backend callback at `GET /api/v1/auth/callback` completes the Auth0 code exchange, creates the Civitas session, and sets the first-party session cookie.
- The web app must not import Auth0 SDKs or hold Auth0 session state.

## Public Routing Assumption

The current web app calls relative `/api/v1/*` paths.
That means the browser-facing auth routes should be exposed on the same public origin path space as the web app, even if the backend runs on a separate upstream host behind a reverse proxy.

Examples:

- Good: browser uses `https://app.example.test`, and `/api/v1/*` on that origin proxies to the backend upstream.
- Not supported by the current web slice: browser uses `https://app.example.test`, but the public auth API lives only on `https://api.example.test` with no shared browser-facing `/api` proxy.

## Auth0 Tenant Setup

Configure the Auth0 application as:

- Application type: `Regular Web Application`
- Hosted UX: `Universal Login`
- Passwordless mode: email OTP via the `email` connection

Required application settings per environment:

- Allowed Callback URLs: the exact public Civitas callback URL, for example `https://app.example.test/api/v1/auth/callback`
- Allowed Logout URLs: the exact web origin or sign-in page origin you may return to later, for example `https://app.example.test/sign-in`
- Allowed Web Origins: the exact public web origin, for example `https://app.example.test`

Operational notes:

- Keep callback and logout URLs exact. Auth0 matches them strictly per environment.
- Use the public callback URL the browser reaches, not an internal backend upstream hostname.
- Keep Web Origins explicit even though the current Civitas login flow is redirect-based and does not use a frontend Auth0 SDK.
- Universal Login magic links are not part of this slice. Use email OTP.

## Required Civitas Configuration

Example managed-provider values:

```bash
CIVITAS_RUNTIME_ENVIRONMENT=staging
CIVITAS_AUTH_PROVIDER=auth0
CIVITAS_AUTH_SESSION_COOKIE_NAME=civitas_session
CIVITAS_AUTH_SESSION_COOKIE_SECURE=true
CIVITAS_AUTH_SESSION_COOKIE_SAMESITE=lax
CIVITAS_AUTH_SESSION_TTL_HOURS=336
CIVITAS_AUTH_STATE_TTL_MINUTES=15
CIVITAS_AUTH_CALLBACK_ERROR_PATH=/sign-in
CIVITAS_AUTH_ALLOWED_ORIGINS=https://app.example.test
CIVITAS_AUTH_SHARED_SECRET=<override-me>
CIVITAS_AUTH_AUTH0_DOMAIN=tenant.eu.auth0.com
CIVITAS_AUTH_AUTH0_CLIENT_ID=<client-id>
CIVITAS_AUTH_AUTH0_CLIENT_SECRET=<client-secret>
CIVITAS_AUTH_AUTH0_CONNECTION=email
# Optional when your tenant requires a custom API audience
# CIVITAS_AUTH_AUTH0_AUDIENCE=https://api.example.test
```

Guardrails:

- `CIVITAS_AUTH_SHARED_SECRET` signs the auth `state` token and must be rotated away from the local default outside `local` or `test`.
- Staging and production must use secure cookies.
- `CIVITAS_AUTH_ALLOWED_ORIGINS` must list the exact browser origins allowed to call cookie-authenticated POST routes such as sign-out.

## Request Flow

1. The web app calls `POST /api/v1/auth/start` with the user email and optional `return_to`.
2. Civitas creates a short-lived auth attempt server-side containing the safe `return_to` and PKCE `code_verifier`, then issues a signed opaque auth `state`.
3. Civitas redirects the browser to Auth0 Universal Login with:
   - `response_type=code`
   - `scope=openid profile email`
   - `login_hint=<email>`
   - `connection=email`
   - `code_challenge=<derived from the stored verifier>`
   - `code_challenge_method=S256`
4. Auth0 completes the hosted challenge and redirects back to `GET /api/v1/auth/callback`.
5. Civitas consumes the live auth attempt, exchanges the authorization code at Auth0 with the stored PKCE `code_verifier`, loads `/userinfo`, upserts `users` and `auth_identities`, creates `app_sessions`, and sets the `civitas_session` cookie.
6. The browser is redirected back to the original safe `return_to` route.

## Sign-Out Behavior

- `POST /api/v1/auth/signout` revokes the Civitas session and clears the first-party cookie.
- Auth0 logout is not required for correct Civitas sign-out in this slice.
- A future provider-logout redirect can be added later without changing the current API contract.

## Failure Modes

`503 provider unavailable`
- Civitas could not reach Auth0 during code exchange or user-info lookup.
- Check Auth0 domain configuration, tenant availability, outbound network, and client credentials.

`/sign-in?error=callback_failed`
- Auth0 returned an invalid callback payload, the PKCE/auth-attempt state was missing, expired, or already consumed, or the code exchange failed validation.
- Start a fresh sign-in flow and inspect backend logs for token or user-info errors.

Callback URL mismatch or wrong host
- Auth0 is redirecting to a URL that does not match the public `/api/v1/auth/callback` surface the browser uses.
- Align the Auth0 callback setting with the browser-facing Civitas origin and proxy configuration.

`/sign-in?error=unverified_email`
- Auth0 returned an identity without `email_verified=true`.
- Confirm the configured Auth0 connection and tenant policy are producing verified email identities.

## Account Linking Note

- This slice maps one `(provider_name, provider_subject)` pair to one Civitas `AuthIdentity`.
- Auth0 account linking is not implemented in Civitas yet.
- If product later adds multiple Auth0 connections or social providers, plan explicit account-linking behavior before enabling them to avoid duplicate internal users.

## Manual Verification

1. Confirm the Auth0 application settings match the exact Civitas web and API URLs for the target environment.
   The callback URL should be the public `/api/v1/auth/callback` URL reached by the browser.
2. Open the web app on an allowed origin and navigate to `/sign-in`.
3. Enter an email address and complete the Auth0 hosted challenge.
4. Confirm the browser returns to the requested page and the header shows the authenticated email address.
5. Call `GET /api/v1/session` and confirm `state=authenticated`.
6. Click `Sign out` and confirm the header and `GET /api/v1/session` return to anonymous state.

## Change Management

When Auth0 configuration, callback handling, or session behavior changes, update these docs together:

- [Local Development Runbook](./local-development.md)
- [Development Auth Provider Runbook](./auth-development-provider.md)
- [docs/index.md](../index.md)
- [.planning/phases/phase-10-premium-access/10B1-auth0-provider-plugin.md](../../.planning/phases/phase-10-premium-access/10B1-auth0-provider-plugin.md)
