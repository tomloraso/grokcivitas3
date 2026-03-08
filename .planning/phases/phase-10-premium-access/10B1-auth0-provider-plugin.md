# 10B1 - Auth0 Provider Plugin

## Goal

Implement the first real external identity-provider adapter using `Auth0` without changing the Phase 10 boundary:

- Auth0 verifies identity
- Civitas owns the internal user, auth-identity mapping, and app session
- the web app continues to integrate with Civitas auth routes only
- the `development` provider remains available for local or test-only use

## Fixed Inputs

- `10A-provider-boundary-gate.md` now freezes `Auth0` as the selected external provider.
- `10B-auth-session-foundation.md` defines the provider-agnostic session and callback flow that must remain intact.
- The current `development` provider is scaffolding for local or test-only verification and must not become a staging or production fallback.
- No frontend route, component, or cache policy should become provider-owned.

## Provider Model To Implement

### Auth0 Tenant Shape

- Configure Auth0 as a `Regular Web Application`.
- Use a backend callback URL that resolves to Civitas `GET /api/v1/auth/callback`.
- Keep Allowed Callback URLs, Allowed Logout URLs, and Allowed Web Origins explicit per environment.
- Prefer Auth0 Universal Login for hosted sign-in UX.
- Prefer passwordless email OTP for the first implementation. Current Auth0 docs explicitly note that Universal Login supports passwordless OTP and that email magic links are not supported on Universal Login, so do not build the MVP around Classic Login magic links unless product explicitly reopens that choice.

### Python Integration Assumption

- Treat Auth0 as a standards-based OIDC provider first, not as a framework-defining SDK.
- Auth0’s current Python documentation includes both Auth0-managed SDK quickstarts and Authlib-based examples. For Civitas, keep route ownership, session persistence, and cookie issuance inside the existing backend foundation rather than handing those concerns to an opinionated provider SDK.
- The adapter should own authorize, token-exchange, and user-info calls behind the existing `IdentityProvider` port.
- Official Auth0 Python packages can be used selectively for management or token-verification tasks, but Civitas should not couple application flow or contracts to vendor SDK object shapes.

## Scope

### In Scope

- Auth0-backed infrastructure adapter behind the current provider boundary
- backend configuration and startup validation for Auth0 environments
- provider-start and callback-completion wiring for Auth0
- identity mapping from Auth0 subject and email claims into existing `UserAccount` and `AuthIdentity` records
- explicit provider error handling and audit-friendly logging
- tests for start, callback, failure, and sign-out behavior with Auth0 configuration
- docs and runbooks needed to operate Auth0 in staging or production

### Out Of Scope

- social login providers
- MFA rollout beyond what Auth0 may enforce externally
- frontend Auth0 SDK adoption
- account-linking UX beyond preserving backend compatibility
- premium entitlement, checkout, or billing behavior

## Architecture Constraints

- Domain and application layers remain provider-agnostic.
- `IdentityProvider` remains the only application-facing auth-provider port.
- API routes stay thin and continue to expose Civitas session state only.
- The web app must not import Auth0 SDKs or parse Auth0 tokens.
- The adapter must not persist provider access tokens in long-lived application storage unless a later, separately approved requirement needs them.

## Recommended Delivery Plan

### 1. Freeze Configuration Surface

Add or confirm backend settings for:

- Auth0 domain
- client ID
- client secret
- audience, only if a later Auth0 configuration requires it
- allowed callback URL base or public app base URL
- provider connection or prompt settings only if the chosen passwordless UX needs them

Validation rules:

- `CIVITAS_AUTH_PROVIDER=auth0` must reject incomplete Auth0 configuration.
- Non-local environments must continue to require secure cookies and explicit allowed origins.
- `development` remains valid only in `local` or `test` with loopback-only origins.

### 2. Implement The Auth0 Adapter

Adapter responsibilities:

- build the Auth0 authorize URL from Civitas start-sign-in inputs
- include Civitas-controlled state and return-target protection
- exchange the callback code for verified identity data
- normalize Auth0 identity payloads into the existing provider result contract
- translate provider failures into existing application-level errors such as invalid callback versus provider unavailable

Security expectations:

- keep Civitas state validation mandatory before any code exchange
- use the Regular Web App authorization-code flow with confidential-client token exchange as the baseline. PKCE remains optional hardening for this adapter, but it is not a prerequisite for the first implementation because the current Auth0 Regular Web App guidance is still centered on the confidential authorization-code flow and the current Civitas foundation does not yet persist provider-side code verifiers.
- validate required claims before creating a Civitas session
- fail closed on missing or unverified identity data needed for MVP sign-in policy

### 3. Keep Persistence And Session Semantics Stable

- Continue mapping one `(provider_name, provider_subject)` pair to one `AuthIdentity`.
- Do not redesign `users`, `auth_identities`, or `app_sessions` around Auth0 data models.
- Keep sign-out local-session-first: revoke the Civitas session and clear the cookie even if provider logout is unavailable or skipped.
- Treat provider logout as an optional redirect enhancement, not a prerequisite for correct Civitas sign-out.

### 4. Preserve The Web Boundary

- `POST /api/v1/auth/start` remains the only sign-in entry point from the web app.
- The browser may be redirected to Auth0-hosted UI, but callback completion still terminates at Civitas backend.
- `GET /api/v1/session` and `POST /api/v1/auth/signout` contracts remain unchanged from the web app's perspective.
- Header, shell, and cache invalidation behavior should require no provider-specific branching.

### 5. Keep The Development Provider

- Retain the `development` provider for local or test-only workflows after Auth0 is implemented.
- Keep the existing runtime and origin fences intact.
- Continue using the development provider in fast local tests where real provider round-trips add no value.
- Add integration coverage that proves both provider modes honor the same Civitas session contract.

### 6. Add Docs And Operational Evidence

- Update local-development and auth runbooks to describe when to use `development` versus Auth0.
- Add staging or production setup notes only after the Auth0 adapter exists and the exact environment contract is known.
- Record callback URL, logout URL, and passwordless-mode assumptions in repo docs so tenant setup stays reproducible.

## Testing Strategy

### Backend

- unit tests for Auth0 settings validation
- adapter tests for authorize URL construction and callback payload mapping
- use-case tests proving Auth0 provider results still create the same `UserAccount`, `AuthIdentity`, and `AppSession` outcomes
- API integration tests for redirect start, callback success, callback failure, and sign-out

### Web

- verify the existing sign-in screen still calls Civitas start-sign-in and handles callback errors
- verify authenticated shell behavior remains unchanged after Auth0 redirect completion
- verify sign-out still clears session-dependent cache and shell state

### Manual Rehearsal

- staging sign-in round-trip with Auth0-hosted UX
- expired or reused callback state handling
- provider outage or misconfiguration behavior
- sign-out from an active Civitas session

## Acceptance Criteria

- Auth0 sign-in starts from Civitas routes and ends with a Civitas-owned session cookie.
- No Auth0 SDK or token handling is added to the frontend session model.
- The `development` provider still works for local or test-only session verification.
- Staging and production reject the `development` provider and require valid Auth0 configuration.
- Auth0-specific concerns stay inside infrastructure, bootstrap, and environment configuration.
- Existing session, sign-out, CSRF, and cache-invalidation guarantees remain intact.

## Sequencing Note

- Complete this plan before `10C-entitlements-domain-and-persistence.md`.
- Follow with `10B2-auth-pkce-hardening.md` to add PKCE without changing the current Civitas-owned session boundary.
- Do not let Auth0-specific implementation reopen the already-frozen boundary that premium access remains backend-enforced and session-driven.
