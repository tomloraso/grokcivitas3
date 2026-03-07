# 10C - Research-Area Entitlements And Persistence

## Goal

Model premium access in the backend so unlock scope, entitlement status, expiry, and audit history are first-class concepts before payment integration is wired in.

This document is the core of the phase. If the entitlement model is vague, every later paywall and payment decision becomes brittle.

## Scope

### Domain Scope

- research-area unlock scope
- premium product definition
- entitlement grant lifecycle
- reusable access-evaluation rules
- audit events needed for billing reconciliation and support

### Persistence Scope

- tables for research areas, products, entitlements, and entitlement events
- query paths that work independently of web-session transport
- deterministic expiry and revocation handling

## Why The Unlock Scope Is A Research Area

The product language is postcode-level unlock, but backend enforcement must also work for:

- `GET /schools?postcode=...`
- `GET /schools/{urn}`
- `GET /schools/{urn}/trends`
- compare payloads that include multiple URNs

A raw postcode string is not sufficient on profile or compare routes. The backend should therefore model a research area with:

- normalized postcode
- configured radius
- resolved latitude and longitude
- optional descriptive label for UI

Access evaluation can then answer:

- does this search request match an active research-area entitlement?
- does this school fall inside any active research area for this user?
- do all schools in this compare set fall inside at least one active research area?

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
      research_area_repository.py
      school_access_scope_repository.py
```

Recommended domain concepts:

- `ResearchArea`
- `PremiumProduct`
- `EntitlementGrant`
- `EntitlementStatus`
- `AccessDecision`
- `AccessReason`

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
| `research_areas` | Canonical postcode-plus-radius unlock scope |
| `premium_products` | Internal SKU catalog with duration and rules |
| `entitlements` | User-owned entitlement grants |
| `entitlement_events` | Append-only audit trail for grant, expiry, revoke, and reconcile events |

Related tables from `10B`:

- `users`
- `auth_identities`
- `app_sessions`

Recommended fields:

- canonical postcode and display postcode
- radius miles or meters
- center latitude and longitude
- `starts_at`, `ends_at`, `revoked_at`
- internal product code and optional provider price mapping field
- reason codes for revoke or expiry transitions

## Access-Evaluation Strategy

### Search

- Normalize the incoming postcode and radius to a research-area lookup key.
- If the user has an active entitlement for that exact scope, return the premium search response.
- Otherwise return preview data plus paywall metadata.

### Profile And Trends

- Resolve the school coordinates from the existing `schools` serving table.
- Determine whether the school falls inside any active research area owned by the user.
- Return full or preview sections based on that result.

### Compare

- Evaluate every selected school against the active research-area set.
- If any selected school is outside entitlement coverage, return a partially locked compare response with explicit metadata instead of silent omissions.

## Guardrails

- Expired entitlements must stop returning premium-only data immediately.
- Entitlement queries must work without depending on redirect state or cached frontend assumptions.
- The entitlement model must be reusable for future premium surfaces such as AI analyst views without redesigning the storage layer.
- Access evaluation belongs in backend domain or application code, not in API route handlers.

## Acceptance Criteria

- Backend has a stable research-area entitlement model and persistence contract.
- Unlock state can be queried independently of web-session concerns and independently of payment-provider payloads.
- Profile, trends, and compare access can be evaluated without carrying the original search query through the UI.
- The data model is sufficient for later payment reconciliation and basic support workflows.
