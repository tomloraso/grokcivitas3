# 10C - Feature-Tier Entitlements And Persistence

## Goal

Model premium access in the backend so account-level premium products, capability grants, expiry, and audit history are first-class concepts before payment integration is wired in.

This document is the core of the phase. If the entitlement model is vague, every later paywall and payment decision becomes brittle.

## Scope

### Domain Scope

- premium product definition
- capability bundle definition
- entitlement grant lifecycle
- reusable access-evaluation rules
- audit events needed for billing reconciliation and support

### Persistence Scope

- tables for premium products, product capabilities, entitlements, and entitlement events
- query paths that work independently of web-session transport
- deterministic expiry and revocation handling

## Launch Inputs From 10G

Phase 10 launch now freezes three premium capabilities:

1. `premium_ai_analyst`
2. `premium_comparison`
3. `premium_neighbourhood`

School favourites are explicitly deferred to a later phase and must not be pulled into this slice by accident.
Benchmark context is explicitly outside the paid launch bundle in this phase. Inline benchmark cues and the benchmark dashboard drill-down remain free.

## Why The Unlock Scope Is Capability-Based

The premium model is account-level. Users do not buy access to one postcode or one search area. They buy access to premium features on their account.

That means backend enforcement should answer questions like:

- does this user have access to the AI analyst section?
- does this user have access to the compare workflow?
- does this user have access to neighbourhood context on the profile?

The access model should therefore operate on named capabilities or access requirements, not geography-derived scope or route-specific booleans.

## Intended Backend Model

### Domain

Create an access-focused slice:

```text
civitas/
  domain/access/
    models.py
    value_objects.py
    services.py
  application/access/
    use_cases.py
    dto.py
    policies.py
    ports/
      entitlement_repository.py
      product_repository.py
```

Recommended domain concepts:

- `PremiumProduct`
- `CapabilityKey`
- `EntitlementGrant`
- `EntitlementStatus`
- `AccessDecision`
- `AccessRequirement`

Recommended application use cases:

- `GetCurrentAccountAccessUseCase`
- `EvaluateAccessUseCase`
- `ListAvailablePremiumProductsUseCase`
- `ListUserEntitlementsUseCase`

### Access Rules

- `active`: current time is within grant window and grant is not revoked
- `expired`: entitlement end time has passed
- `revoked`: support or refund action removed access before expiry
- `pending`: commercial flow started but payment not yet confirmed

Recommended access outputs:

- `free`
- `preview_only`
- `premium_unlocked`
- `requires_auth`
- `requires_purchase`

Recommended section states carried by access-aware feature DTOs:

- `available`
- `locked`
- `unavailable`

`locked` means the premium artefact exists conceptually but the current viewer lacks access. `unavailable` means the artefact does not exist yet, is not supported, or has not been published.

## Policy Source For MVP

- `10G-premium-access-matrix.md` remains the product source of truth.
- For the Phase 10 launch, that matrix should compile into a backend-owned policy registry in code, not a database-managed or admin-managed rules engine.
- The registry should map surface requirements such as:
  - `school_profile.ai_analyst` -> `premium_ai_analyst`
  - `school_profile.neighbourhood` -> `premium_neighbourhood`
  - `school_compare.core` -> `premium_comparison`
- `premium_products` and `product_capabilities` remain persistence concerns for commercial packaging. They do not replace the backend policy registry that decides which product surface requires which capability.

This keeps the launch policy explicit, testable, and aligned with the current repo architecture. A later admin-editable access policy system can be added only if product needs justify the extra complexity.

## Persistence Design

Minimum table set:

| Table | Purpose |
|---|---|
| `premium_products` | Internal SKU catalog for plans or packages |
| `product_capabilities` | Mapping from product to named feature capabilities |
| `entitlements` | User-owned premium access grants |
| `entitlement_events` | Append-only audit trail for grant, expiry, revoke, and reconcile events |

Related tables from `10B`:

- `users`
- `auth_identities`
- `app_sessions`

Recommended fields:

- internal product code and human-readable display name
- billing interval or duration fields where applicable
- capability key and optional access-scope or section key
- `starts_at`, `ends_at`, `revoked_at`
- optional provider price mapping field
- reason codes for revoke or expiry transitions

Recommended constraints and indexes:

- unique product code on `premium_products`
- unique `(product_code, capability_key)` on `product_capabilities`
- index on `entitlements(user_id, status, ends_at)`
- index on `entitlements(user_id, product_code)`
- append-only `entitlement_events` keyed by internal event ID plus reference fields for provider event correlation

## Access-Evaluation Strategy

The exact section-by-section rules come from `10G-premium-access-matrix.md`, but the technical model should work like this:

### Search

- Search remains free at the route level.
- Premium compare entry points stay visible in search, but the actual compare workflow is gated by `premium_comparison`.

### Profile

- Load the free baseline profile exactly as today.
- Evaluate the AI analyst section through `premium_ai_analyst`.
- Evaluate neighbourhood context through `premium_neighbourhood`.
- Return free baseline content plus locked metadata when the user lacks the required capability.

### Compare

- Compare is a premium workflow in the launch bundle.
- Evaluate `premium_comparison` before loading the full compare payload.
- Return a typed locked response when the user lacks access rather than a generic route failure.

### Trends And Benchmark Dashboard

- Baseline trends and benchmark cues remain free in the Phase 10 launch bundle.
- Do not add premium access rules to the benchmark dashboard route in this slice unless product reopens the launch bundle later.

### AI Artefacts

- AI overview stays free.
- The AI analyst view is gated by `premium_ai_analyst`.

## Access Decision Contract Shape

The internal `AccessDecision` returned by the access slice should be expressive enough to drive both API schema mapping and future non-HTTP use cases.

Recommended fields:

- `access_level`
- `section_state`
- `capability_key`
- `reason_code`
- `available_product_codes`
- `requires_auth`
- `requires_purchase`

Recommended reason-code categories:

- `free_baseline`
- `premium_capability_missing`
- `anonymous_user`
- `artefact_not_published`
- `artefact_not_supported`
- `entitlement_expired`
- `entitlement_revoked`

The API layer can then translate `AccessDecision` into transport-safe schema types without leaking domain internals directly.

## Integration With Existing Read Features

Phase 10 should extend existing feature use cases instead of pushing access checks down into route handlers.

### Profile

- Extend `GetSchoolProfileUseCase.execute(...)` to accept the current viewer context such as `viewer_user_id: UUID | None`.
- Load the free baseline profile exactly as today.
- Evaluate the analyst section requirement through the access slice.
- Only load premium-only analyst text when the decision is `premium_unlocked`.
- When the decision is `locked`, return a typed analyst section payload with `state=locked`, `teaser_text` (first 2-3 sentences of the analyst text), the school name for contextual CTA rendering, and paywall metadata rather than a nullable `analyst_text`.
- Add a lightweight summary metadata lookup or equivalent repository method so the use case can retrieve the teaser excerpt and distinguish `locked` from `unavailable` without loading the full premium text for unauthorized viewers.

### Profile Neighbourhood Context

- Evaluate `premium_neighbourhood` inside the profile use case before mapping deprivation, crime, and house-price data into the response.
- When unlocked, return the full neighbourhood payload through a typed `available` wrapper.
- When locked, return a typed neighbourhood section payload with `state=locked`, a short teaser line or teaser payload, the school name for contextual CTA rendering, and paywall metadata but no raw deprivation, crime, or house-price values.
- `unavailable` must continue to mean the underlying artefact is absent or unsupported, not merely paywalled.

### Compare

- Evaluate `premium_comparison` before loading or returning the full compare dataset.
- When locked, return a typed compare response or locked route state that includes requested school context plus paywall metadata so the web app can support both a teaser modal and a direct-route locked state.
- Do not rely on client-side button disablement as the only comparison guard.

## Recommended Launch Seed Data

- Seed one launch product code such as `premium_launch`.
- Map that product to all three launch capabilities:
  - `premium_ai_analyst`
  - `premium_comparison`
  - `premium_neighbourhood`
- Keep the schema able to support additional product rows later without changing access-evaluation code.

## Guardrails

- Expired entitlements must stop returning premium-only data immediately.
- Entitlement queries must work without depending on redirect state or cached frontend assumptions.
- The entitlement model must support multiple premium features without forcing a new schema for every premium section.
- Access evaluation belongs in backend domain or application code, not in API route handlers.
- `10G-premium-access-matrix.md` must remain the product source of truth for which capabilities each surface requires.
- Locked premium state must never be represented by silently dropping a field that also means "not published yet."
- Locked premium responses must include teaser content and the school name so the frontend can render contextual CTAs.
- Compare entry points may stay visible for conversion, but compare access itself must still be enforced server-side.
- All user-facing product display names must use `Premium`, never `Pro`. `Pro` is reserved for a future B2B tier.

## Acceptance Criteria

- Backend has a stable feature-tier entitlement model and persistence contract.
- Unlock state can be queried independently of web-session concerns and independently of payment-provider payloads.
- Profile AI analyst, profile neighbourhood context, and compare access can be evaluated through named access requirements instead of route-specific special cases.
- The data model is sufficient for later payment reconciliation and basic support workflows.
- Existing profile and compare use cases have a clear, testable integration path for access-aware outputs.
