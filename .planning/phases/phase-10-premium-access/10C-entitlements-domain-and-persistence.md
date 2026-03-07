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
    ports/
      entitlement_repository.py
      product_repository.py
      access_policy_repository.py
```

Recommended domain concepts:

- `PremiumProduct`
- `CapabilityKey`
- `EntitlementGrant`
- `EntitlementStatus`
- `AccessDecision`
- `AccessRequirement`

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

## Guardrails

- Expired entitlements must stop returning premium-only data immediately.
- Entitlement queries must work without depending on redirect state or cached frontend assumptions.
- The entitlement model must support multiple premium features without forcing a new schema for every premium section.
- Access evaluation belongs in backend domain or application code, not in API route handlers.
- `10G-premium-access-matrix.md` must remain the product source of truth for which capabilities each surface requires.

## Acceptance Criteria

- Backend has a stable feature-tier entitlement model and persistence contract.
- Unlock state can be queried independently of web-session concerns and independently of payment-provider payloads.
- Search, profile, trends, compare, and premium AI access can be evaluated through named access requirements instead of route-specific special cases.
- The data model is sufficient for later payment reconciliation and basic support workflows.
