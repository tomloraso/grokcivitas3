# Premium Access Release Runbook

## Purpose

Use this runbook when rehearsing or releasing the Phase 10 premium-access slice.

It covers:

- Auth0-backed browser sign-in and Civitas session cookies
- premium entitlement evaluation through the backend access slice
- Stripe Checkout, Stripe billing portal, and Stripe webhook reconciliation
- web paywall rendering on profile, compare, and account routes

This runbook is the operational companion to:

- [Auth Session Boundary](../architecture/auth-session-boundary.md)
- [Premium Access Boundary](../architecture/premium-access-boundary.md)
- [Auth0 Managed Provider Runbook](./auth0-managed-provider.md)

## Required Configuration

Staging or production-like rehearsal must use the managed auth provider plus Stripe test-mode billing:

```bash
CIVITAS_RUNTIME_ENVIRONMENT=staging
CIVITAS_AUTH_PROVIDER=auth0
CIVITAS_AUTH_SESSION_COOKIE_SECURE=true
CIVITAS_AUTH_ALLOWED_ORIGINS=https://app.example.test
CIVITAS_AUTH_SHARED_SECRET=<override-me>
CIVITAS_AUTH_AUTH0_DOMAIN=tenant.eu.auth0.com
CIVITAS_AUTH_AUTH0_CLIENT_ID=<client-id>
CIVITAS_AUTH_AUTH0_CLIENT_SECRET=<client-secret>
CIVITAS_AUTH_AUTH0_CONNECTION=email

CIVITAS_BILLING_ENABLED=true
CIVITAS_BILLING_PROVIDER=stripe
CIVITAS_BILLING_STRIPE_SECRET_KEY=<stripe-secret>
CIVITAS_BILLING_STRIPE_WEBHOOK_SECRET=<stripe-webhook-secret>
# Optional
# CIVITAS_BILLING_STRIPE_PORTAL_CONFIGURATION_ID=<portal-config-id>
```

Guardrails:

- Do not use `CIVITAS_AUTH_PROVIDER=development` outside `local` or `test`.
- Do not use `CIVITAS_BILLING_ENABLED=true` without valid Stripe secrets.
- Keep browser-facing `/api/v1/*` routes on the same public origin path space as the web app.

## Automated Gates

Run from the repo root unless noted otherwise:

1. `uv run --project apps/backend python tools/scripts/export_openapi.py`
2. `cd apps/web && npm run generate:types`
3. `uv run --project apps/backend alembic -c apps/backend/alembic.ini upgrade head`
4. `uv run --project apps/backend pytest`
5. `cd apps/web && npm run lint`
6. `cd apps/web && npm run typecheck`
7. `cd apps/web && npm run test`
8. `cd apps/web && npm run build`
9. `cd apps/web && npm run test:e2e`
10. `make lint`
11. `make test`

Premium-specific automated evidence now lives in:

- `apps/backend/tests/unit/test_access_use_cases.py`
- `apps/backend/tests/unit/test_billing_use_cases.py`
- `apps/backend/tests/integration/test_auth_api.py`
- `apps/backend/tests/integration/test_billing_api.py`
- `apps/backend/tests/integration/test_account_api.py`
- `apps/backend/tests/integration/test_school_profile_api.py`
- `apps/backend/tests/integration/test_school_compare_api.py`
- `apps/web/src/features/auth/AuthProvider.test.tsx`
- `apps/web/src/features/school-profile/school-profile.test.tsx`
- `apps/web/src/features/school-compare/school-compare.test.tsx`
- `apps/web/e2e/premium-access.spec.ts`

## Staging Rehearsal Checklist

Record the date, environment, tester, and outcome for each item.

1. Verify managed callback and cookie behavior over the real browser-facing domain.
   Expected result: Auth0 returns to `/api/v1/auth/callback`, Civitas sets the first-party session cookie, and `GET /api/v1/session` returns `state=authenticated`.
2. Verify an anonymous user still sees the free baseline.
   Expected result: free profile sections and benchmark context remain available, while analyst, neighbourhood, and compare show locked premium states.
3. Verify a signed-in free account hits the same premium boundaries through backend access decisions.
   Expected result: `/api/v1/session` shows `account_access_state=free`, profile sections remain locked, and compare returns the locked payload instead of the matrix.
4. Start Stripe Checkout from a locked premium boundary.
   Expected result: the browser is redirected to hosted checkout and the corresponding `checkout_sessions` row is created in Civitas.
5. Complete checkout in Stripe test mode and confirm webhook reconciliation.
   Expected result: Stripe delivers `invoice.paid`, Civitas writes `payment_events`, updates `billing_subscriptions`, writes or updates `entitlements`, and `GET /api/v1/account/access` moves to `premium`.
6. Replay the same Stripe webhook event.
   Expected result: the webhook stays idempotent and does not create duplicate entitlements or duplicate access grants.
7. Verify late-arriving webhook recovery.
   Expected result: the upgrade page opened with `checkout_id` moves from `processing_payment` to `completed`, and the user can continue into the unlocked route without manual DB intervention.
8. Verify refund or revoke behavior in non-production payment mode.
   Expected result: the entitlement changes to `revoked` or `expired`, the access epoch changes, and premium routes relock immediately.
9. Verify the premium access matrix against documented behavior.
   Expected result: benchmark context remains free, analyst and neighbourhood distinguish `locked` from `unavailable`, and compare distinguishes locked state from an actually empty or invalid compare set.
10. Verify sign-out clears premium UI state.
   Expected result: `POST /api/v1/auth/signout` returns anonymous session state, the browser session no longer shows premium content, and premium cached responses are not reused.

## Release Notes Template

Capture these values before approval:

- deployed backend commit SHA
- deployed web commit SHA
- Alembic head revision after deploy
- Stripe webhook endpoint URL used for rehearsal
- Auth0 application or tenant used for rehearsal
- exact commands and test outputs for the automated gates
- links to any staging screenshots or webhook logs

## Rollback Plan

Use the smallest safe rollback that restores user trust first.

### Web paywall regression

- Roll back the web deployment to the last green Phase 10 release candidate artifact.
- The backend contract changes are additive, so older web clients can ignore the extra session access fields while you restore the previous UI.

### Billing regression

- Set `CIVITAS_BILLING_ENABLED=false` and redeploy the backend.
- Expected effect: new checkout creation, billing-portal handoff, and webhook parsing are disabled through the billing-provider factory, while the access slice and existing entitlements remain readable.
- If the UI should stop showing upgrade entry points immediately, roll back the web deployment after the backend containment step.

### Session regression

- Roll back backend and web deployments together to the last green Phase 10 release candidate artifact.
- Do not downgrade the database schema during the incident response path. Phase 10 migrations are additive and should remain at the current Alembic head unless a separate migration recovery plan is approved.
- After rollback, confirm `GET /api/v1/session`, `POST /api/v1/auth/start`, `POST /api/v1/auth/signout`, and one premium boundary route all behave as expected.

## Sign-Off

Phase 10 should only be signed off after:

1. every automated gate above is green in one repository state
2. the staging rehearsal checklist is completed against managed auth plus Stripe test mode
3. the rollback plan is recorded with the exact deployment artifact or commit references that would be used
