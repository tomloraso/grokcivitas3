# 9D - Payment Checkout And Webhooks

## Goal

Implement the payment flow that creates, confirms, and reconciles premium unlocks.

## Scope

- checkout session creation
- payment success and cancellation handling
- webhook verification
- idempotent entitlement fulfillment

## Operational Rules

- Webhook processing must be safe to retry.
- Payment success should not rely solely on frontend redirect state.
- Provider event payloads must be mapped into internal application contracts in infrastructure code.

## Acceptance Criteria

- Successful purchase results in an active entitlement.
- Failed, canceled, or duplicated events do not create inconsistent unlock state.
- Staging can verify end-to-end payment and webhook behavior with realistic provider flows.
