# Phase 10 Design Index - Premium Access Program

## Document Control

- Status: Planned
- Last updated: 2026-03-07
- Phase owner: Product + Engineering
- Source phase: `.planning/phased-delivery.md`

## Purpose

This folder contains the implementation-ready plan for turning Civitas from a free research product into a paid, backend-enforced local-research product.

The original Phase 10 scope bundled identity, session transport, entitlement modelling, payment orchestration, and paywall UX into one milestone. That is too much for one engineering sign-off. This folder now treats Phase 10 as a two-stage program:

1. foundation: authenticated user context and entitlement evaluation
2. monetization: checkout, fulfillment, and premium surface enforcement

Top-level numbering stays as Phase 10 to avoid unnecessary churn in the rest of the planning set, but execution should happen as two gated mini-phases.

## Product Baseline For Planning

- Premium unlocks are sold as a research area, not as a raw postcode string.
- A research area is defined by normalized postcode plus configured search radius and resolved center point.
- Launch packaging remains time-boxed. Planning assumes one default SKU at launch, but the data model should allow future duration or radius variants.
- Anonymous browsing remains available.
- Free users retain a useful preview experience; premium users unlock the full research-area dataset and premium-only API fields.
- Access decisions remain backend-owned. The frontend renders the result and sends user intent.

## Why Research Area Is The Core Access Unit

Using a raw postcode string as the entitlement key breaks down on profile and compare routes because those routes do not naturally carry the original search context. The internal model should therefore store a reusable research-area scope:

- `research_area`: canonical postcode, radius, latitude, longitude
- `entitlement`: who has access to that area, for which product, during which period
- `access decision`: whether a request for a postcode search, school profile, trends view, or compare set is covered by at least one active entitlement

This keeps the product language postcode-first while giving the backend a deterministic enforcement model for search, profile, trends, and compare.

## Delivery Stages

### Stage 10A - Identity And Access Foundation

Deliverables:

1. `10A-provider-boundary-gate.md`
2. `10B-auth-session-foundation.md`
3. `10C-entitlements-domain-and-persistence.md`

Stage 10A exit outcome:

- Civitas can create and resolve an authenticated app session.
- The backend can model users, research areas, and entitlement grants.
- API and web layers can render locked versus unlocked state without payment integration being live yet.

### Stage 10B - Monetization And Premium Enforcement

Deliverables:

1. `10D-payment-checkout-and-webhooks.md`
2. `10E-premium-api-and-web-paywall.md`
3. `10F-premium-quality-gates.md`

Stage 10B exit outcome:

- Hosted checkout creates paid unlock intent for a research area.
- Signed provider webhooks reconcile into active or revoked entitlements.
- Search, profile, trends, and compare surfaces consistently enforce premium boundaries.

## Technical Approach Summary

### Backend

- Add new backend feature modules for `identity`, `access`, and `billing`, following the standard domain -> application -> infrastructure -> api layering.
- Keep provider SDKs in infrastructure adapters only.
- Use backend-owned app sessions so the web app never needs to hold provider tokens.
- Evaluate premium access through a reusable access service that accepts user context plus requested resource scope.

### Data And Persistence

- Introduce first-class tables for users, auth identities, sessions, research areas, entitlements, checkout sessions, and payment events.
- Keep payment events append-only and idempotent so webhook retries are safe.
- Expiry and revocation must take effect immediately in access evaluation.

### API

- Extend OpenAPI contracts with session, entitlement, and paywall metadata.
- Keep public read routes as typed Civitas API endpoints; do not expose provider payload shapes beyond infrastructure.
- Prefer `200` responses with access metadata and locked sections for public read journeys rather than using `403` as the primary paywall transport.

### Web

- Add dedicated `auth` and `premium-access` feature ownership inside `apps/web/src/features`.
- The app shell reads typed session state from Civitas API endpoints only.
- Existing cached profile and trends requests must become access-aware so free responses are not reused after purchase and paid responses are not reused after sign-out.

## Key Domain Concepts

| Concept | Purpose |
|---|---|
| `UserAccount` | Internal user record owned by Civitas |
| `AuthIdentity` | External-provider identity mapped to one user account |
| `AppSession` | Backend-owned authenticated session bound to a user |
| `ResearchArea` | Canonical unlock scope defined by postcode and radius |
| `PremiumProduct` | Sellable package that determines duration and coverage rules |
| `EntitlementGrant` | Active, expired, pending, or revoked right to access a research area |
| `CheckoutSession` | Pending commercial intent before payment confirmation |
| `PaymentEvent` | Signed provider event used for deterministic reconciliation |
| `AccessDecision` | Backend output explaining whether requested data is free, preview-only, or fully unlocked |

## Explicit Out Of Scope

- Recurring subscriptions for MVP
- Household or shared-account access
- Saved compares or saved searches as part of the paid launch
- Full support CRM or finance-ops tooling beyond basic auditability and replay safety
- Public release of future premium-only AI summaries until access boundaries are proven stable

## Execution Sequence

1. Complete `10A` first to freeze product-unit, provider-boundary, and callback decisions.
2. Complete `10B` to establish internal account and session handling.
3. Complete `10C` to model research areas and entitlement evaluation before any payment wiring exists.
4. Complete `10D` to add checkout, provider callbacks, and idempotent fulfillment.
5. Complete `10E` to wire premium boundaries into search, profile, trends, and compare contracts plus web paywall UX.
6. Complete `10F` to close both stages with architecture, security, staging, and acceptance evidence.

## Definition Of Done

- Users can authenticate with a stable Civitas-managed session.
- Research-area entitlements are first-class backend concepts independent of provider payloads.
- Payment confirmation reconciles deterministically into entitlement state.
- All premium boundaries are enforced server-side and exposed through typed Civitas contracts.
- Existing web caching and route flows behave correctly across anonymous, signed-in, expired, and newly paid states.
- Repository lint, tests, and staging rehearsal all pass.
