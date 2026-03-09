# Premium Access Boundary

## Purpose

This page describes the implemented Phase 10 premium-access and billing slices as they exist in the backend today.
Use it as the architecture-level source of truth for how products, capabilities, entitlements, billing checkout state, and access decisions are modelled before API paywall rendering is added.

Detailed product intent still lives in:

- `.planning/phases/phase-10-premium-access/10C-entitlements-domain-and-persistence.md`
- `.planning/phases/phase-10-premium-access/10D-payment-checkout-and-webhooks.md`
- `.planning/phases/phase-10-premium-access/10G-premium-access-matrix.md`

## Boundary

- Civitas owns `PremiumProduct`, `product_capabilities`, `EntitlementGrant`, `EntitlementEvent`, and the backend access-policy registry.
- Auth/session identifies the current user only. It does not decide product access directly.
- Payment-provider payloads do not participate in access evaluation. Stage 10D reconciles billing state into Civitas entitlements first.
- The web app will consume typed access outputs later in Phase 10E. 10D adds typed billing routes, but `/api/v1/session` remains auth-only in this phase.

## Backend Package Map

The implemented slice follows the standard feature layout:

```text
civitas/
  domain/access/
    models.py
    value_objects.py
    services.py
  application/access/
    dto.py
    policies.py
    use_cases.py
    ports/
      entitlement_repository.py
      product_repository.py
  domain/billing/
    models.py
    value_objects.py
    services.py
  application/billing/
    dto.py
    errors.py
    use_cases.py
    ports/
      billing_provider_gateway.py
      billing_state_repository.py
  api/
    billing_routes.py
    schemas/
      billing.py
  infrastructure/persistence/
    postgres_entitlement_repository.py
    postgres_product_repository.py
    postgres_billing_state_repository.py
  infrastructure/payments/
    provider_factory.py
    stripe_billing_provider_gateway.py
```

Bootstrap owns wiring for the new use cases and repositories.

## Policy Source Of Truth

- Product source of truth remains `.planning/phases/phase-10-premium-access/10G-premium-access-matrix.md`.
- The backend compiles the launch policy into `civitas.application.access.policies`.
- The current registry keeps premium requirements explicit in code:
  - `school_profile.ai_analyst` -> `premium_ai_analyst`
  - `school_profile.neighbourhood` -> `premium_neighbourhood`
  - `school_compare.core` -> `premium_comparison`
- The registry is intentionally code-owned for MVP. It is not a database rules engine.

## Persistence

Phase 10C and 10D add eight tables:

- `premium_products`
- `product_capabilities`
- `entitlements`
- `entitlement_events`
- `payment_customers`
- `checkout_sessions`
- `billing_subscriptions`
- `payment_events`

The migration also seeds one launch product:

- product code: `premium_launch`
- display name: `Premium`
- billing interval: `monthly`
- provider price lookup key: `premium_launch`
- capabilities:
  - `premium_ai_analyst`
  - `premium_comparison`
  - `premium_neighbourhood`

`entitlement_events` is append-only audit history for support and billing reconciliation.
`payment_events` is the append-only provider event log keyed by provider event ID.

## Billing And Fulfillment Boundary

- Stripe Checkout is the hosted purchase surface for MVP.
- Stripe's billing portal is the hosted self-serve path for cancellation and payment-method updates.
- `billing_subscriptions` is the Civitas billing-system projection for current provider state.
- `entitlements` remains the access-system projection consumed by access evaluation.
- Webhook reconciliation owns the single transaction that writes payment events, checkout state, subscription state, entitlements, and entitlement audit events together.
- Browser redirects are never the source of truth for activation.

## Access Evaluation Semantics

Entitlement status is evaluated from stored lifecycle state plus time:

- `pending`: stored as pending, or future-dated start window
- `active`: stored as active, within the grant window, and not revoked
- `expired`: active grant whose `ends_at` has passed
- `revoked`: explicit revoke state or `revoked_at` present

The access slice supports two evaluation modes:

- preview-aware: returns `preview_only` plus `locked` section state for premium surfaces that can show teaser content
- strict: returns `requires_auth` or `requires_purchase` when preview should not be used

The returned `AccessDecision` remains transport-agnostic so API and non-HTTP callers can map it independently.

## Current Scope And Deferral

Implemented in Phase 10C and 10D:

- premium product catalogue lookup
- product-to-capability mapping
- entitlement persistence and audit events
- current-account access queries
- reusable access evaluation against named requirements
- typed billing product, checkout, portal, and webhook routes
- Stripe checkout-session creation and Stripe billing-portal handoff
- idempotent webhook reconciliation into billing state plus entitlement state
- payment-customer, checkout-session, subscription, and payment-event persistence

Deferred to Phase 10E:

- session payload access metadata
- profile and compare contract changes
- locked-section API responses
- web paywall rendering and cache invalidation
