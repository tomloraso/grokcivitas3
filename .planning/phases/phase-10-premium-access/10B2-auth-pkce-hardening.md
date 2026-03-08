# 10B2 - Auth PKCE Hardening

## Goal

Add PKCE to the existing Auth0-backed authorization-code flow without changing the Phase 10 boundary:

- Auth0 still verifies identity
- Civitas still owns the internal user, auth-identity mapping, and app session
- the web app still starts sign-in through Civitas routes only
- provider concerns stay inside infrastructure, bootstrap, and configuration

This is a security-hardening slice, not a product-flow redesign.

## Why This Is A Follow-Up

The current Auth0 slice uses a backend-owned confidential authorization-code flow with:

- a server-side client secret
- Civitas-owned signed `state`
- a backend callback that completes code exchange and issues the Civitas session

That is a valid baseline for a regular web application. However, current OAuth security guidance recommends PKCE for confidential clients as defense in depth, not only for SPAs or native apps.
PKCE in this slice supplements the existing confidential-client token exchange; it does not replace client-secret authentication or turn Civitas into a public client.

The current auth foundation does **not** yet persist a per-attempt PKCE `code_verifier`, so PKCE was intentionally deferred rather than approximated unsafely.

## Non-Goals

- no frontend Auth0 SDK adoption
- no provider-owned session state in the web app
- no change to the public auth route family
- no switch to SPA-style token handling
- no account-linking or MFA redesign

## Core Design Requirement

Do **not** place the PKCE `code_verifier` in the current signed `state` token unless the state format becomes encrypted as well as integrity-protected.

Reason:

- the existing state codec signs payloads but does not encrypt them
- PKCE requires the verifier to remain secret from the browser and intermediaries
- embedding the verifier in a readable state payload would defeat the point of PKCE

So the follow-up should introduce a short-lived server-side auth-attempt store keyed by an opaque state or attempt identifier.

## Recommended Technical Approach

### 1. Introduce A Short-Lived Auth Attempt Boundary

Add an application-facing port for ephemeral auth attempts, for example:

```text
application/identity/ports/
  auth_attempt_repository.py
```

Stored per auth attempt:

- opaque attempt id
- normalized safe `return_to`
- PKCE `code_verifier`
- issued-at and expires-at
- optional provider metadata needed for the callback exchange

The browser should receive only the opaque state or attempt identifier, not the verifier itself.

### 2. Update Start-Sign-In Flow

`StartSignInUseCase` should:

- generate the PKCE `code_verifier`
- derive the S256 `code_challenge`
- persist the auth attempt server-side with TTL aligned to auth state lifetime
- call the Auth0 adapter with:
  - opaque `state`
  - `code_challenge`
  - `code_challenge_method=S256`

### 3. Update Callback Completion

`CompleteAuthCallbackUseCase` should:

- resolve the auth attempt from the opaque `state`
- fail closed if the attempt is missing, expired, or already consumed
- pass the stored `code_verifier` into the Auth0 token exchange
- delete or mark consumed the auth attempt after successful or terminal callback handling

### 4. Keep Current Session Semantics Stable

After successful Auth0 verification:

- keep the same `UserAccount` and `AuthIdentity` mapping logic
- keep the same `AppSession` persistence
- keep the same first-party session cookie issuance
- keep the same sign-out behavior

### 5. Preserve The Development Provider

The `development` provider must continue to work.

Acceptable options:

- support the same auth-attempt persistence path for both providers
- or allow the development provider to ignore PKCE-specific fields while still honoring the same Civitas callback contract

Do not weaken existing runtime or origin fences around `development`.

## Infrastructure Notes

- Auth0 authorize requests should add `code_challenge` and `code_challenge_method=S256`.
- Auth0 token exchange should send the stored `code_verifier`.
- Keep Auth0-specific parameter mapping in the infrastructure adapter only.
- The app should continue to treat Auth0 as a standards-based OIDC provider rather than moving route or session ownership into an SDK.

## Persistence Guidance

Prefer ephemeral storage over durable tables if existing infrastructure makes that easy.

Good options:

- Redis with TTL
- a short-lived SQL table only if Redis is unavailable and the operational tradeoff is acceptable

Repo-specific implementation decision:

- Civitas does not currently have a Redis-backed auth or ephemeral-state adapter.
- For this repo, the default implementation should therefore be a short-lived SQL `auth_attempts` table plus repository, with explicit consume-once semantics and expiry checks in application logic.

If SQL is used:

- keep it clearly scoped to auth attempts
- add TTL cleanup or consumption semantics
- do not mix it into durable session or user tables

## Testing Strategy

### Backend

- unit tests for PKCE verifier and challenge generation
- use-case tests proving:
  - start-sign-in stores an auth attempt
  - callback requires a matching live attempt
  - consumed or expired attempts fail closed
- adapter tests proving Auth0 authorize URL includes:
  - `code_challenge`
  - `code_challenge_method=S256`
- adapter tests proving token exchange sends `code_verifier`
- API integration tests for:
  - successful PKCE round-trip
  - missing state
  - expired attempt
  - reused callback

### Web

- no provider-specific UI changes expected
- verify the existing sign-in flow still starts through Civitas routes only

## Acceptance Criteria

- Auth0 sign-in still starts from Civitas routes and ends with a Civitas-owned session cookie.
- PKCE is added using S256.
- The PKCE verifier is never exposed in readable browser state.
- Expired, missing, or replayed auth attempts fail closed.
- The development provider still works for local or test-only flows.
- No Auth0 SDK or token handling is added to the frontend.

## Sequencing

- This follows `10B1-auth0-provider-plugin.md`.
- Complete this hardening before any broader security sign-off for staging or production auth.
- Do not let this slice reopen the backend-owned session boundary.
