# 10D - Payment Checkout, Fulfillment, And Webhooks

## Goal

Implement the payment flow that converts a signed-in user's purchase intent into reconciled account-level premium access.

Phase 10D builds on the identity and feature-entitlement foundations from `10B` and `10C`. Payment work must reuse those seams, not bypass them.

## Scope

- checkout-session creation for a chosen premium product
- success and cancellation redirects
- signed webhook ingestion
- idempotent fulfillment into premium entitlement state
- provider-hosted billing management handoff for cancellation and payment-method updates
- audit-safe storage of commercial events and reconciliation results

## Intended Technical Approach

### Backend Feature Layout

```text
civitas/
  domain/billing/
    models.py
    value_objects.py          # optional
    services.py
  application/billing/
    use_cases.py
    dto.py
    errors.py
    ports/
      billing_provider_gateway.py
      billing_state_repository.py
  api/
    schemas/
      billing.py
    billing_routes.py
```

Infrastructure adapters should live under:

```text
infrastructure/
  payments/
    stripe_billing_provider_gateway.py
  persistence/
    postgres_billing_state_repository.py
```

`ListAvailablePremiumProductsUseCase` already exists in the 10C `access` slice and should remain the product-catalog read path for MVP. 10D should reuse it rather than creating a second catalog source.

The billing persistence port should be explicit about transaction ownership:

- checkout creation and status reads may use narrower repository methods
- webhook reconciliation must not fan out across multiple independently transactional repositories
- one dedicated billing-state repository or equivalent unit-of-work must own the single database transaction that updates payment events, checkout state, subscription state, entitlement state, and entitlement audit events together

Recommended application use cases:

- `CreateCheckoutSessionUseCase`
- `CreateBillingPortalSessionUseCase` if self-serve billing management is in MVP
- `GetCheckoutStatusUseCase`
- `ReconcilePaymentEventUseCase`
- `ListAccountBillingHistoryUseCase` if a basic account page needs audit visibility in MVP

## Launch Billing Defaults For Implementation Planning

- Reuse the existing 10C launch product `premium_launch`.
- Keep that launch product mapped to exactly these three Phase 10 capabilities:
  - `premium_ai_analyst`
  - `premium_comparison`
  - `premium_neighbourhood`
- Populate `premium_products.provider_price_lookup_key` for `premium_launch` rather than creating a parallel billing catalog.
- For 10D implementation, assume one recurring provider price mapped to that launch product in each environment.
- Keep the data model flexible enough for later annual or fixed-term products, but do not block Phase 10 on designing a multi-plan catalog.
- If product later changes the launch interval, the intended goal is that only seed data and provider configuration move, not the entitlement or paywall architecture.
- Benchmark context is not part of the paid launch product in this phase. Inline benchmark cues and the benchmark dashboard drill-down remain free.

### Checkout Flow

1. User is authenticated.
2. Web app sends a typed Civitas API request with a premium product code.
3. Backend validates whether the user already has equivalent active coverage.
4. Backend creates an internal pending checkout record before calling the external provider.
5. Infrastructure adapter creates the provider checkout session and stores provider reference IDs.
6. API returns a redirect URL or hosted checkout token to the web app.

Correlation rules for the provider session:

- include internal `checkout_id`, `product_code`, and `user_id` in provider metadata where the provider supports it
- store the provider checkout-session identifier on the internal checkout row
- build success and cancel redirect URLs from the current public request origin plus sanitized internal paths, not from hardcoded upstream backend hosts

If the user already has equivalent active coverage, checkout creation should not create a duplicate open purchase flow. The API should return current access state or an explicit "already covered" checkout status instead.

### Fulfillment Flow

1. Provider sends signed webhook events.
2. API verifies the signature before any business processing.
3. Infrastructure maps the provider payload to an internal payment-event DTO.
4. Application reconciliation use case records the event idempotently.
5. Successful payment events create or activate the premium entitlement grant.
6. Refund, chargeback, or cancel-after-auth events update entitlement state according to product policy.

## Launch Entitlement Lifecycle Rules

To keep implementation deterministic, 10D should use the following default lifecycle rules unless product explicitly signs off a different policy before coding starts:

- checkout created: no entitlement yet; persist only the pending checkout session
- redirect success before webhook: account remains in `processing_payment` or equivalent non-entitled state until reconciliation completes
- successful payment or subscription activation event: create or activate the entitlement using provider period boundaries when available
- recurring cancellation at period end: keep access active until the confirmed period end, then expire naturally
- recurring payment failure: do not invent an indefinite grace state in MVP; keep access only while the confirmed paid period remains active
- full refund or chargeback: revoke access immediately and record a revoke reason unless a future support override flow is added
- duplicate or replayed provider events: record once and no-op on entitlement state if already reconciled

## Persistence Requirements

Minimum additional table set:

| Table | Purpose |
|---|---|
| `payment_customers` | Optional mapping between Civitas user and provider customer record |
| `billing_subscriptions` | Current provider subscription agreement and period state for a user and product |
| `checkout_sessions` | Internal checkout intents and provider references |
| `payment_events` | Append-only provider event log with unique provider event IDs |

Relationship to access model:

- `checkout_sessions` reference `users` and `premium_products`
- successful reconciliation creates or updates `billing_subscriptions` and writes to `entitlements`
- product-to-capability mapping remains in `product_capabilities`
- replayed or duplicate events must not create duplicate entitlements

Recommended additional fields:

- `checkout_sessions`: internal checkout ID, user ID, product code, provider name, provider checkout/session ID, provider customer ID, provider subscription ID when known, status, requested_at, completed_at, canceled_at, expires_at, success path, cancel path
- `billing_subscriptions`: internal subscription ID, user ID, product code, provider name, provider subscription ID, provider customer ID, status, current_period_starts_at, current_period_ends_at, cancel_at_period_end, canceled_at, latest_checkout_session_id, linked entitlement ID, updated_at
- `payment_events`: provider name, provider event ID, event type, occurred_at, received_at, payload JSON, signature verification result, reconciliation status, reconciled_at
- `payment_customers`: user ID, provider name, provider customer ID, created_at, updated_at

Recommended constraints:

- unique `(provider_name, provider_event_id)` on `payment_events`
- unique `(provider_name, provider_checkout_session_id)` on `checkout_sessions`
- unique `(provider_name, provider_subscription_id)` on `billing_subscriptions`
- unique `(provider_name, provider_customer_id)` plus unique `(provider_name, user_id)` on `payment_customers`

## Idempotency And Retry Rules

- Webhook processing must be safe to retry.
- Provider event IDs must be uniquely stored.
- Fulfillment writes must run inside a transaction that updates both billing state and entitlement state together.
- Redirect pages must never be the sole source of truth for premium activation.
- Support tooling must be able to replay a stored event or retry reconciliation from persisted payloads.

Reconciliation should run inside one transaction that:

1. inserts or no-ops the provider event row
2. updates checkout-session state if relevant
3. creates or updates the subscription record if the provider event represents recurring coverage
4. creates or updates the entitlement grant
5. appends the corresponding entitlement event

## Failure And Recovery Cases

- checkout created but provider redirect abandoned
- success redirect received before webhook delivery
- webhook delivered before redirect
- duplicate webhook delivery
- temporary provider API outage during checkout creation
- refund or dispute after premium activation

The implementation plan must treat these as normal paths, not edge-case cleanup work.

## API Surface

10D should expose typed billing routes through backend OpenAPI rather than relying on frontend constants or opaque provider URLs alone.

Recommended MVP route set:

- `GET /api/v1/billing/products`
- `POST /api/v1/billing/checkout-sessions`
- `GET /api/v1/billing/checkout-sessions/{checkout_id}`
- `POST /api/v1/billing/portal-sessions`
- `POST /api/v1/billing/webhooks/stripe`

Session and auth rules:

- billing checkout and portal routes require a valid Civitas session
- cookie-authenticated billing `POST` routes should use the same trusted-origin guard as sign-out
- webhook routes are provider-authenticated by signature, not by browser session
- 10D must not expand `/api/v1/session`; access metadata stays deferred to `10E`

## Guardrails

- Provider payload shapes stay in infrastructure code.
- Billing use cases consume internal DTOs and repositories only.
- The web app should show "processing payment" states, but unlock should only occur after backend reconciliation.
- Product catalog mapping must not live in frontend constants.
- The billing slice should not depend on route-specific profile or trends logic; it grants commercial coverage only, while the access slice decides which premium surfaces that coverage unlocks.
- The Phase 10 launch product must stay aligned to the three-capability bundle frozen in `10G`; do not silently add benchmark or favourites coverage in billing configuration.
- Reconciliation tests must cover overlapping entitlements or duplicate purchase attempts for the same product so support behavior is explicit.
- `billing_subscriptions` should remain the billing system of record for recurring provider state, while `entitlements` remain the access system of record.
- Prefer the provider's hosted customer portal or equivalent for cancellation and payment-method management in MVP rather than building custom billing-management screens.
- The reconciliation write path must remain atomic even though existing 10C repositories open their own transactions today; 10D should introduce an explicit shared transaction seam rather than assuming per-repository writes are sufficient.
- Product pricing configuration belongs on the existing `premium_products` row for `premium_launch`; do not create a second hardcoded product map inside Stripe adapters or the frontend.

## Acceptance Criteria

- Successful purchase results in active premium access for the expected product.
- Failed, canceled, duplicate, or replayed events do not create inconsistent premium state.
- Refund or revoke paths can remove premium access deterministically.
- Staging can verify end-to-end checkout, callback, and webhook behavior with realistic provider flows.
