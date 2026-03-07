# 10F - Premium Quality Gates And Release Readiness

## Goal

Close both Phase 10 stages with evidence that identity, feature-tier entitlement evaluation, payment fulfillment, and premium enforcement work together safely.

This phase changes authentication state, billing state, API contracts, and web rendering. Quality gates must therefore prove behavior across anonymous, authenticated, entitled, expired, and revoked states.

## Stage 10A Exit Gates

### Backend

- unit tests for identity domain models and session lifecycle rules
- application tests for sign-in callback, session lookup, and sign-out flows
- integration tests for session cookie behavior and anonymous fallback
- persistence tests for `users`, `auth_identities`, `app_sessions`, `premium_products`, `product_capabilities`, and `entitlements`
- access-evaluation tests proving named capabilities resolve into the expected access decisions

### Frontend

- typed session client tests
- app-shell tests for anonymous versus authenticated state
- locked-state rendering tests for free-baseline versus premium-only sections

### Architecture And Contracts

- updated OpenAPI contract export
- regenerated frontend types
- boundary checks confirming provider payloads do not leak into API schemas or frontend models

## Stage 10B Exit Gates

### Backend

- unit and integration coverage for checkout creation and webhook verification
- reconciliation tests covering duplicate, out-of-order, and replayed payment events
- expiry and revocation tests proving access changes take effect immediately
- access-evaluation tests for premium sections, compare features, and premium AI surfaces

### Frontend

- checkout CTA and post-purchase refresh tests
- cache-invalidation or access-aware-cache tests
- locked-to-unlocked journey tests for representative premium surfaces

### End-To-End

- sign in
- hit a premium boundary
- start checkout
- simulate success and webhook completion
- refresh into unlocked state
- sign out and confirm premium response is no longer reused

## Required Repository Checks

- backend lint and type checks
- backend test suite
- frontend lint
- frontend typecheck
- frontend unit or component tests
- frontend build
- repository `make lint`
- repository `make test`

## Staging Rehearsal Requirements

- verify real callback and cookie behavior over production-like domains
- verify signed webhook delivery and replay handling
- verify refund or revoke path in a non-production payment environment
- verify support recovery path for a checkout that succeeded at provider side but arrived late to the app
- verify the premium access matrix behaves as documented for at least one free baseline surface, one locked premium section, and one unlocked premium flow

## Acceptance Evidence

- premium-only data and features are blocked without entitlement
- premium state is granted, expired, and revoked correctly
- checkout and webhook flows are idempotent
- web UI reflects the real backend session and entitlement state
- no provider-specific payload types leak across architecture boundaries

## Sign-Off Condition

Phase 10 is complete only when:

1. Stage 10A quality gates pass
2. Stage 10B quality gates pass
3. staging validation proves real callback, cookie, and webhook behavior
4. the release plan includes a rollback path for billing or session regressions
