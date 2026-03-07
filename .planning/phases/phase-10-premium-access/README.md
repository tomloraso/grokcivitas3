# Phase 10 Design Index - Premium Access Program

## Document Control

- Status: Planned
- Last updated: 2026-03-07
- Phase owner: Product + Engineering
- Source phase: `.planning/phased-delivery.md`

## Purpose

This folder contains the implementation-ready plan for turning Civitas from a fully free research product into a freemium product with:

- stable authenticated identity
- account-level premium plans
- backend-enforced feature-tier access
- payment-backed premium activation

The original Phase 10 plan treated premium as a postcode-area unlock. That model has been retired. Phase 10 now assumes the free product remains broadly usable and premium adds higher-value data layers, analysis, and workflow features on the user account. The exact free versus premium split is defined in `10G-premium-access-matrix.md`.

## Product Baseline For Planning

- Premium is account-level, not geography-level.
- Core search, profile, trends, and compare journeys remain available in the free product.
- Premium unlocks additional sections, deeper analysis, premium AI artifacts, and other advanced workflow features defined in `10G-premium-access-matrix.md`.
- The exact free versus premium split is a prerequisite planning artifact for Stage 10B and should not be inferred ad hoc during implementation.
- Access decisions remain backend-owned. The frontend renders the result and sends user intent.
- The launch premium bundle remains limited to the two capabilities frozen in `10G`; do not expand Stage 10 scope by implicitly monetizing other surfaces.
- The premium benchmark surface is the dedicated drill-down dashboard, not the inline benchmark cues already embedded in the free profile experience.
- Premium-sensitive contracts must distinguish `locked` from `unavailable` or `not_published`; missing JSON alone is not an acceptable paywall signal.

## Delivery Stages

### Stage 10A - Identity And Access Foundation

Deliverables:

1. `10G-premium-access-matrix.md` (freeze before backend access modelling)
2. `10A-provider-boundary-gate.md`
3. `10B-auth-session-foundation.md`
4. `10C-entitlements-domain-and-persistence.md`

Stage 10A exit outcome:

- Civitas can create and resolve an authenticated app session.
- The backend can model users, premium products, capability grants, and access decisions.
- The system can evaluate whether a user has access to a named premium feature even before payment wiring is live.

### Stage 10B - Monetization And Premium Enforcement

Deliverables:

1. `10D-payment-checkout-and-webhooks.md`
2. `10E-premium-api-and-web-paywall.md`
3. `10F-premium-quality-gates.md`

Stage 10B exit outcome:

- Hosted checkout creates paid account-level premium access.
- Signed provider webhooks reconcile into active or revoked premium entitlements.
- Search, profile, trends, compare, and premium AI surfaces consistently enforce feature-tier premium boundaries.

## Technical Approach Summary

### Backend

- Add backend feature modules for `identity`, `access`, and `billing`, following the standard domain -> application -> infrastructure -> api layering.
- Keep provider SDKs in infrastructure adapters only.
- Use backend-owned app sessions so the web app never needs to hold provider tokens.
- Evaluate premium access through a reusable access service that accepts user context plus requested capability or surface requirement.
- Keep the MVP surface-to-capability policy in backend code derived from `10G`; do not introduce an admin-managed or provider-managed rules engine for the first launch.

### Data And Persistence

- Introduce first-class tables for users, auth identities, sessions, premium products, product capabilities, entitlement grants, checkout sessions, and payment events.
- Keep payment events append-only and idempotent so webhook retries are safe.
- Entitlement expiry and revocation must take effect immediately in access evaluation.
- Persist commercial product data separately from access policy mapping so later plan or pricing changes do not require redesign of profile or trends contracts.

### API

- Extend OpenAPI contracts with session, access, plan, and paywall metadata.
- Keep public read routes as typed Civitas API endpoints; do not expose provider payload shapes beyond infrastructure.
- Prefer `200` responses with access metadata and locked sections for public read journeys rather than using `403` as the primary paywall transport.
- For premium-sensitive sections, return explicit section-state wrappers such as `available`, `locked`, or `unavailable` rather than nullable premium fields with ambiguous meaning.

### Web

- Add dedicated `auth` and `premium-access` feature ownership inside `apps/web/src/features`.
- The app shell reads typed session state from Civitas API endpoints only.
- Existing cached profile and trends requests must become access-aware so free responses are not reused after upgrade and premium responses are not reused after sign-out.
- The profile page should stop depending on the premium dashboard route for its free baseline render path; free inline benchmark cues stay available from the main profile payload.

## Key Domain Concepts

| Concept | Purpose |
|---|---|
| `UserAccount` | Internal user record owned by Civitas |
| `AuthIdentity` | External-provider identity mapped to one user account |
| `AppSession` | Backend-owned authenticated session bound to a user |
| `PremiumProduct` | Sellable plan or package for account-level premium access |
| `CapabilityKey` | Named premium feature or section requirement |
| `EntitlementGrant` | Active, expired, pending, or revoked right to a premium product or capability set |
| `CheckoutSession` | Pending commercial intent before payment confirmation |
| `PaymentEvent` | Signed provider event used for deterministic reconciliation |
| `AccessDecision` | Backend output explaining whether requested data is free, preview-only, or premium-unlocked |

## Explicit Out Of Scope

- Per-postcode or per-area purchases
- Household or shared-account access
- Full support CRM or finance-ops tooling beyond basic auditability and replay safety
- Fine-grained free versus premium field mapping without an agreed access matrix
- Public release of future premium-only AI summaries until access boundaries are proven stable

## Execution Sequence

1. Freeze `10G` first so product boundaries are explicit before architecture or billing work starts.
2. Complete `10A` to freeze provider, packaging, and callback decisions.
3. Complete `10B` to establish internal account and session handling.
4. Complete `10C` to model premium products, capability grants, and access evaluation before any payment wiring exists.
5. Complete `10D` to add checkout, provider callbacks, and idempotent fulfillment.
6. Complete `10E` to wire premium boundaries into search, profile, trends, compare, and premium AI contracts plus web paywall UX.
7. Complete `10F` to close both stages with architecture, security, staging, and acceptance evidence.

## Definition Of Done

- Users can authenticate with a stable Civitas-managed session.
- Premium products and feature entitlements are first-class backend concepts independent of provider payloads.
- Payment confirmation reconciles deterministically into account-level premium access state.
- All premium boundaries are enforced server-side and exposed through typed Civitas contracts.
- Existing web caching and route flows behave correctly across anonymous, signed-in, expired, and newly upgraded states.
- Repository lint, tests, and staging rehearsal all pass.
