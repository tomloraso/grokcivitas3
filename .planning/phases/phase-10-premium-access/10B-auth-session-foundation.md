# 10B - Auth Session Foundation

## Goal

Introduce authenticated user context and stable Civitas-managed sessions without leaking provider concerns into application logic or frontend state management.

Stage 10A is not complete until the backend can answer one question on every request: who is the current Civitas user, if any?

## Sequencing Note

- This document can be implemented before `10G-premium-access-matrix.md` when the active scope is identity and session handling only.
- `10G` is not required to ship the login foundation itself because this slice does not yet evaluate premium capabilities or paywall states.
- Once session state starts driving entitlement checks or premium-aware responses, `10G` becomes an input again.

## Scope

### Backend

- add identity-focused feature modules following repo architecture conventions
- create internal user, auth-identity, and app-session models
- expose the minimum API surface for sign-in start, callback completion, sign-out, and session introspection
- make current-user resolution available to later access and billing use cases

### Frontend

- add auth-aware app-shell session loading
- provide sign-in and sign-out entry points through Civitas routes only
- expose session state to upgrade and premium-feature flows without moving access logic into the UI

## Intended Technical Approach

### Domain And Application

Create a backend feature slice for identity:

```text
civitas/
  domain/identity/
    models.py
    services.py
  application/identity/
    use_cases.py
    dto.py
    ports/
      identity_provider.py
      user_repository.py
      session_repository.py
```

Core concepts:

- `UserAccount`: internal Civitas user record
- `AuthIdentity`: one external provider subject mapped to one user
- `AppSession`: Civitas-owned session with issued, last-seen, and expiry timestamps

Recommended use cases:

- `StartSignInUseCase`
- `CompleteAuthCallbackUseCase`
- `GetCurrentSessionUseCase`
- `SignOutUseCase`

### Infrastructure

Add provider-specific adapters under infrastructure:

```text
infrastructure/
  auth/
    <provider>_identity_provider.py
  persistence/
    postgres_user_repository.py
    postgres_session_repository.py
```

Infrastructure responsibilities:

- exchange callback codes or tokens with the auth provider
- map provider payloads into internal `AuthIdentity` records
- persist and revoke app sessions
- set or clear session cookies at the API boundary
- keep the `development` adapter available as a permanent local or test-only fallback for callback and session verification
- fail fast in staging or production configuration if the `development` adapter is selected

Provider note:

- Auth0-specific adapter work is planned separately so this document can stay focused on provider-agnostic session foundations and current-user resolution.

### API

Keep routes thin and contract-owned by backend:

- `POST /api/v1/auth/start`
- `GET /api/v1/auth/callback`
- `GET /api/v1/session`
- `POST /api/v1/auth/signout`

The API response contract should expose Civitas session state only:

- authenticated or anonymous
- stable user identifier
- session expiry timestamp
- optionally lightweight account metadata needed for the shell

Do not expose provider token formats or raw provider user payloads through OpenAPI.

### Concrete Callback And Session Flow

1. `POST /api/v1/auth/start`
   - accepts a Civitas-owned `return_to` target or equivalent safe post-auth destination
   - creates a signed and time-limited auth state payload, or stores a short-lived auth-attempt record if the chosen provider flow requires server-side nonce persistence
   - returns a provider redirect URL or completes an immediate redirect response
2. `GET /api/v1/auth/callback`
   - validates the returned auth state before exchanging any provider code or token
   - upserts `UserAccount` and `AuthIdentity`
   - creates a fresh `AppSession`
   - sets the Civitas session cookie
   - redirects the browser to the original safe `return_to` route
3. `GET /api/v1/session`
   - resolves the current Civitas session from the session cookie only
   - returns anonymous state when the cookie is missing, expired, revoked, or invalid
4. `POST /api/v1/auth/signout`
   - revokes the current session server-side
   - clears the cookie
   - returns anonymous session state or an empty success response

The backend callback endpoint, not the frontend, completes provider verification and issues the app session. This keeps the provider boundary inside infrastructure plus the API entrypoint.

### Web

Add a dedicated feature boundary:

```text
apps/web/src/features/auth/
```

Recommended responsibilities:

- session loader or provider for app boot
- sign-in CTA component
- sign-out mutation
- expired-session refresh handling

The web app should call typed Civitas API functions only. It should not import provider SDKs for session resolution.

## Session Transport Rules

- Store the app session in an `HttpOnly` cookie.
- Do not store auth tokens in `localStorage` or URL state after callback completion.
- Expired or revoked sessions must resolve cleanly to anonymous state.
- Session resolution should be cheap enough to run during initial app-shell load.
- Prefer a same-site web plus API deployment model. If production or staging uses separate subdomains, define cookie domain, allowed origins, and `credentials: include` behavior up front instead of treating it as a late deployment concern.

## Persistence Requirements

Minimum persistence set:

- `users`
- `auth_identities`
- `app_sessions`

Required fields:

- internal IDs separate from provider subject IDs
- issued, last-used, and expires-at timestamps
- revoked-at and reason fields for auditability
- unique constraint preventing one provider subject from mapping to multiple users

## Guardrails

- No premium gating may depend on client-only state.
- Anonymous users must retain access to the free research surface.
- Session expiration and provider-error states must be explicit in API contracts and UI rendering.
- Frontend request caching must be invalidated when session or account-access state changes.
- Backend feature use cases that need user context should accept the internal Civitas user ID or session principal produced by this slice, never raw provider subject IDs.
- The root web shell should load session state once through typed Civitas API calls and fan that state out to premium-aware features from a dedicated `features/auth` boundary.

## Acceptance Criteria

- Users can sign in and sign out reliably through Civitas-owned routes.
- Session state is available to the web app through typed API integration.
- Protected backend use cases can resolve current-user context without importing provider SDKs.
- Anonymous, expired-session, and provider-failure cases are handled explicitly.
