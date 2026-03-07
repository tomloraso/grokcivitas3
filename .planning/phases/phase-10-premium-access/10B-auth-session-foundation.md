# 10B - Auth Session Foundation

## Goal

Introduce authenticated user context and stable Civitas-managed sessions without leaking provider concerns into application logic or frontend state management.

Stage 10A is not complete until the backend can answer one question on every request: who is the current Civitas user, if any?

## Scope

### Backend

- add identity-focused feature modules following repo architecture conventions
- create internal user, auth-identity, and app-session models
- expose the minimum API surface for sign-in start, callback completion, sign-out, and session introspection
- make current-user resolution available to later access and billing use cases

### Frontend

- add auth-aware app-shell session loading
- provide sign-in and sign-out entry points through Civitas routes only
- expose session state to premium-entry flows without moving access logic into the UI

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
- Frontend request caching must be invalidated when session state changes.

## Acceptance Criteria

- Users can sign in and sign out reliably through Civitas-owned routes.
- Session state is available to the web app through typed API integration.
- Protected backend use cases can resolve current-user context without importing provider SDKs.
- Anonymous, expired-session, and provider-failure cases are handled explicitly.
