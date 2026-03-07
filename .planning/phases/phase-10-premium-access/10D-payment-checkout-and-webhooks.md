# 10D - Payment Checkout, Fulfillment, And Webhooks

## Goal

Implement the payment flow that converts a signed-in user's purchase intent into reconciled account-level premium access.

Stage 10B starts here. Payment work should build on the identity and feature-entitlement foundations from `10B` and `10C`, not bypass them.

## Scope

- checkout-session creation for a chosen premium product
- success and cancellation redirects
- signed webhook ingestion
- idempotent fulfillment into premium entitlement state
- audit-safe storage of commercial events and reconciliation results

## Intended Technical Approach

### Backend Feature Layout

```text
civitas/
  domain/billing/
    models.py
    services.py
  application/billing/
    use_cases.py
    dto.py
    ports/
      checkout_gateway.py
      billing_repository.py
      payment_event_repository.py
```

Infrastructure adapters should live under:

```text
infrastructure/
  payments/
    <provider>_checkout_gateway.py
  persistence/
    postgres_billing_repository.py
```

Recommended application use cases:

- `CreateCheckoutSessionUseCase`
- `GetCheckoutStatusUseCase`
- `ReconcilePaymentEventUseCase`
- `ListAccountBillingHistoryUseCase` if a basic account page needs audit visibility in MVP

## Launch Billing Defaults For Implementation Planning

- Seed one launch product code such as `premium_launch`.
- For Stage 10B build planning, assume one recurring provider price mapped to that launch product in each environment.
- Keep the data model flexible enough for later annual or fixed-term products, but do not block Phase 10 on designing a multi-plan catalog.
- If product later changes the launch interval, the intended goal is that only seed data and provider configuration move, not the entitlement or paywall architecture.

### Checkout Flow

1. User is authenticated.
2. Web app sends a typed Civitas API request with a premium product code.
3. Backend validates whether the user already has equivalent active coverage.
4. Backend creates an internal pending checkout record before calling the external provider.
5. Infrastructure adapter creates the provider checkout session and stores provider reference IDs.
6. API returns a redirect URL or hosted checkout token to the web app.

If the user already has equivalent active coverage, checkout creation should not create a duplicate open purchase flow. The API should return current access state or an explicit "already covered" checkout status instead.

### Fulfillment Flow

1. Provider sends signed webhook events.
2. API verifies the signature before any business processing.
3. Infrastructure maps the provider payload to an internal payment-event DTO.
4. Application reconciliation use case records the event idempotently.
5. Successful payment events create or activate the premium entitlement grant.
6. Refund, chargeback, or cancel-after-auth events update entitlement state according to product policy.

## Launch Entitlement Lifecycle Rules

To keep implementation deterministic, Stage 10B should use the following default lifecycle rules unless product explicitly signs off a different policy before coding starts:

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
| `checkout_sessions` | Internal checkout intents and provider references |
| `payment_events` | Append-only provider event log with unique provider event IDs |

Relationship to access model:

- `checkout_sessions` reference `users` and `premium_products`
- successful reconciliation writes to `entitlements`
- product-to-capability mapping remains in `product_capabilities`
- replayed or duplicate events must not create duplicate entitlements

Recommended additional fields:

- `checkout_sessions`: internal checkout ID, user ID, product code, provider checkout/session ID, provider customer ID, status, requested_at, completed_at, canceled_at, return URL, cancel URL
- `payment_events`: provider name, provider event ID, event type, occurred_at, received_at, payload JSON, signature verification result, reconciliation status, reconciled_at
- `payment_customers`: user ID, provider name, provider customer ID, created_at, updated_at

## Idempotency And Retry Rules

- Webhook processing must be safe to retry.
- Provider event IDs must be uniquely stored.
- Fulfillment writes must run inside a transaction that updates both billing state and entitlement state together.
- Redirect pages must never be the sole source of truth for premium activation.
- Support tooling must be able to replay a stored event or retry reconciliation from persisted payloads.

Reconciliation should run inside one transaction that:

1. inserts or no-ops the provider event row
2. updates checkout-session state if relevant
3. creates or updates the entitlement grant
4. appends the corresponding entitlement event

## Failure And Recovery Cases

- checkout created but provider redirect abandoned
- success redirect received before webhook delivery
- webhook delivered before redirect
- duplicate webhook delivery
- temporary provider API outage during checkout creation
- refund or dispute after premium activation

The implementation plan must treat these as normal paths, not edge-case cleanup work.

## Guardrails

- Provider payload shapes stay in infrastructure code.
- Billing use cases consume internal DTOs and repositories only.
- The web app should show "processing payment" states, but unlock should only occur after backend reconciliation.
- Product catalog mapping must not live in frontend constants.
- The billing slice should not depend on route-specific profile or trends logic; it grants commercial coverage only, while the access slice decides which premium surfaces that coverage unlocks.
- Reconciliation tests must cover overlapping entitlements or duplicate purchase attempts for the same product so support behavior is explicit.

## Acceptance Criteria

- Successful purchase results in active premium access for the expected product.
- Failed, canceled, duplicate, or replayed events do not create inconsistent premium state.
- Refund or revoke paths can remove premium access deterministically.
- Staging can verify end-to-end checkout, callback, and webhook behavior with realistic provider flows.
