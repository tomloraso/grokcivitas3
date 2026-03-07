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

## Why The Unlock Scope Is Capability-Based

The premium model is now account-level. Users do not buy access to one postcode or one search area. They buy access to premium features on their account.

That means backend enforcement should answer questions like:

- does this user have access to premium profile section `X`?
- does this user have access to premium compare feature `Y`?
- does this user have access to premium AI artifact `Z`?

The access model should therefore operate on named capabilities or access requirements, not geography-derived scope.

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

`locked` means the premium artifact exists conceptually but the current viewer lacks access. `unavailable` means the artifact does not exist yet, is not supported, or has not been published.

## Policy Source For MVP

- `10G-premium-access-matrix.md` remains the product source of truth.
- For the Phase 10 launch, that matrix should compile into a backend-owned policy registry in code, not a database-managed or admin-managed rules engine.
- The registry should map surface requirements such as `school_profile.analyst` or `school_trends.dashboard` to capability keys such as `premium_school_analyst` and `premium_benchmark_dashboard`.
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
- If any search enhancement is premium, evaluate the named capability for that enhancement and return access metadata accordingly.

### Profile And Trends

- Evaluate requested premium sections against named capabilities such as premium analysis, deeper benchmark layers, or advanced detail sections.
- Return free baseline content plus locked metadata when the user lacks the required capability.

### Compare

- Core compare can remain free while advanced compare features, richer metric packs, or premium analysis are capability-gated.
- The response should express which compare features are locked rather than collapsing the entire route into a binary premium or free decision.

### AI Artifacts

- AI overview may stay free.
- Premium AI artifacts such as analyst views or other future commentary should be gated by named capabilities rather than by route-wide checks.

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
- `artifact_not_published`
- `artifact_not_supported`
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
- When the decision is `locked`, return a typed analyst section payload with `state=locked` and paywall metadata rather than a nullable `analyst_text`.
- Add a lightweight summary metadata lookup or equivalent repository method so the use case can distinguish `locked` from `unavailable` without loading premium text for unauthorized viewers.

### Trends And Benchmark Dashboard

- Keep the main trends response free unless later planning changes the matrix.
- Evaluate `premium_benchmark_dashboard` inside the dashboard use case before loading the full drill-down payload.
- When locked, return a typed dashboard response with `state=locked` and no premium metric sections.
- The free profile route should keep using the benchmark snapshot already embedded in the profile payload; it should not require dashboard access to render inline benchmark cues.

### Compare

- Phase 9 compare remains free.
- When future compare-plus capabilities are added, the compare use case should compose additional premium sections behind access decisions rather than forking into a separate premium route.

## Recommended Launch Seed Data

- Seed one launch product code such as `premium_launch`.
- Map that product to both launch capabilities:
  - `premium_school_analyst`
  - `premium_benchmark_dashboard`
- Keep the schema able to support additional product rows later without changing access-evaluation code.

## Guardrails

- Expired entitlements must stop returning premium-only data immediately.
- Entitlement queries must work without depending on redirect state or cached frontend assumptions.
- The entitlement model must support multiple premium features without forcing a new schema for every premium section.
- Access evaluation belongs in backend domain or application code, not in API route handlers.
- `10G-premium-access-matrix.md` must remain the product source of truth for which capabilities each surface requires.
- Locked premium state must never be represented by silently dropping a field that also means "not published yet."

## Acceptance Criteria

- Backend has a stable feature-tier entitlement model and persistence contract.
- Unlock state can be queried independently of web-session concerns and independently of payment-provider payloads.
- Search, profile, trends, compare, and premium AI access can be evaluated through named access requirements instead of route-specific special cases.
- The data model is sufficient for later payment reconciliation and basic support workflows.
- Existing profile and trends use cases have a clear, testable integration path for access-aware outputs.
