# 9C - Entitlements Domain And Persistence

## Goal

Model premium access in the backend domain so unlock state, expiry, and purchase history are first-class concepts.

## Domain Scope

- entitlement entity or value model
- unlock scope definition
- expiry and active-state rules
- purchase or payment reconciliation record

## Persistence Scope

- tables or records for user accounts, entitlement state, and payment history
- idempotent writes for payment-confirmed unlocks
- audit-friendly timestamps and provider reference fields

## Product Rules

- Initial unlock scope should remain postcode-level unless `9A` chooses otherwise.
- Expired entitlements must stop returning premium-only data immediately.
- Entitlement checks must be reusable by all protected endpoints.

## Acceptance Criteria

- Backend has a stable entitlement model and persistence contract.
- Unlock state can be queried independently of web-session concerns.
- Data model is sufficient for payment reconciliation and support workflows.
