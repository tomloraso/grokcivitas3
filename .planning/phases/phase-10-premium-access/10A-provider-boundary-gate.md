# 10A - Provider Boundary And Product Gate

## Goal

Freeze the commercial and provider assumptions that every later deliverable depends on:

- what premium is
- how identity is established
- how sessions are carried
- how checkout is created
- how payment confirmation becomes account-level premium access

This gate exists so implementation does not drift into provider-specific logic inside domain, application, or web feature layers.

## Product Decisions To Freeze

### Premium Unit

- Launch premium should be account-level, not postcode-level or geography-level.
- The launch SKU may be one premium plan or a small number of premium plans, but each plan must resolve to a defined capability bundle.
- The exact free versus premium split belongs in `10G-premium-access-matrix.md` and must be frozen before Stage 10B starts.
- Packaging remains open, but the backend model should support time-bound access windows and future plan variation without redesign.

### Free Versus Premium Boundary

- Search, profile, trends, and compare remain available in the free product.
- Premium should unlock higher-value sections, deeper analysis, richer compare behavior, premium AI artifacts, or other advanced workflow features.
- Premium boundaries should be explained section-by-section, not inferred from whether a route is public or private.
- The matrix must define whether premium affects:
  - additional sections
  - deeper history or benchmark views
  - advanced compare features
  - premium AI artifacts
  - future export or saved-workflow features

### Identity And Checkout Preconditions

- Checkout requires a signed-in user because premium is account-bound.
- Anonymous users can browse and hit premium boundaries, but sign-in must happen before checkout session creation.
- Redirect-only payment success is insufficient; only signed provider events or verified provider queries can activate premium access.

## Recommended Provider Pattern

### Authentication

- Use a managed email-based identity provider for MVP.
- Civitas should own the app session after provider verification.
- The provider is responsible for email challenge delivery and identity proof.
- Civitas is responsible for internal user records, session persistence, and session cookie issuance.

Why this pattern:

- keeps the frontend provider-agnostic
- avoids storing auth tokens in `localStorage`
- lets backend routes resolve user context without reaching into frontend state
- makes a future provider swap mostly an infrastructure concern

### Payments

- Use a hosted checkout provider with signed webhook support and stable session identifiers.
- Civitas should own the internal product catalog, capability mapping, and entitlement grants.
- Provider price IDs or product IDs should map to Civitas product codes in infrastructure configuration or persistence, not in UI code.

Why this pattern:

- reduces PCI surface area
- gives deterministic, replayable payment events
- supports staging and production parity
- keeps purchase fulfillment backend-owned

## Current Auth Provider Shortlist

Pricing snapshot date: 2026-03-07. Re-check before any commercial commitment.

| Provider | Public pricing snapshot | Pros | Cons | Fit for Civitas |
|---|---|---|---|---|
| [Auth0](https://auth0.com/pricing) | Free tier supports up to 25,000 external active users. Public self-serve tiers start at Essentials `$35/month` and Professional `$240/month`. | Mature customer-identity platform, passwordless support, custom domains, account linking, user import, broad extensibility. Strong choice for a backend-first callback flow that ends in a Civitas session. | Pricing becomes harder to reason about above the free tier, and the platform is broader and heavier than the MVP strictly needs. | Best default fit if we want a conservative, production-grade external provider without reshaping the app around vendor-owned sessions. |
| [Clerk](https://clerk.com/pricing) | Hobby is free with `50,000 MRUs` per app. Pro is `$25/month` or `$20/month` billed annually, with `50,000 MRUs` included and overage starting at `$0.02` per MRU. | Fastest path to polished email-code or magic-link auth, automatic account linking, custom templates, passkeys on paid plans, strong DX. | Pricing metric is MRU rather than plain MAU. Clerk is strongest when you lean into Clerk-managed sessions and UI components, so some value is lost if Civitas insists on a strict first-party session boundary. | Best speed-to-MVP option if we are willing to accept more provider convention in the web and auth layers. |
| [Supabase Auth](https://supabase.com/docs/guides/auth) + [billing](https://supabase.com/docs/guides/platform/billing-on-supabase) | Free includes `50,000 MAU`. Paid Pro or Team includes `100,000 MAU`, then `$0.00325` per MAU. Supabase Pro is `$25/month`, and paid projects also incur platform or compute costs. | Low nominal auth cost, magic links or OTP, identity linking, custom SMTP support, spend-cap controls, straightforward email auth. | Auth is tied to the Supabase project model, JWT conventions, and platform billing. Using it only for auth introduces another platform and the true cost is not just the MAU line item. | Best cost-led option if we are comfortable adopting more of the Supabase platform rather than treating auth as a narrow external service. |
| [Firebase Authentication / Identity Platform](https://firebase.google.com/docs/auth) + [pricing](https://cloud.google.com/identity-platform/pricing) | Pay-as-you-go includes `0-49,999` free MAU for email, social, anonymous, and custom auth. Then `50,000-99,999` is `$0.0055` per MAU and `100,000-999,999` is `$0.0046` per MAU. SAML or OIDC is `$0.015` per MAU after the first `49`. | Mature global platform, email-link auth, provider linking, optional multi-tenancy, audit logging, and enterprise support through Identity Platform. Cost is attractive at mid-scale. | More token and client-SDK centric than the Civitas plan. Introduces Google Cloud billing and operational shape that the rest of the repo does not currently use. | Good low-cost alternative if we are comfortable with Google Cloud and do not mind adapting the boundary around a more token-oriented ecosystem. |

## Provider Selection Criteria

The auth decision should be signed off against these criteria, not headline price alone:

1. Email-based sign-in support for magic link, email code, or equivalent low-friction UX
2. Clean backend callback or server SDK support for Python so Civitas can still own the app session
3. Custom-domain and email-template support for production polish
4. Account linking support to prevent duplicate users if more than one auth method is added later
5. Auditability, support tooling, and operational maturity for login failures and abuse handling
6. Cost predictability from launch through early growth, especially between 10,000 and 100,000 active users
7. Contract, DPA, and UK or EU privacy review before procurement

## Recommendation

### Recommended Default

- Shortlist `Auth0` as the default recommendation for implementation planning.

Reasoning:

- It is the cleanest match for the current Civitas architecture plan: external identity proof plus first-party Civitas session.
- It offers mature passwordless support, custom domains, and account-linking controls without forcing the frontend to become provider-owned.
- It is more expensive than some alternatives, but the operational model is conservative and well understood.

### Strong Alternatives

- `Clerk` if shipping speed and polished auth UX matter more than maintaining a strict first-party session boundary.
- `Supabase Auth` if minimizing auth spend is the top priority and we accept additional platform coupling.
- `Firebase Authentication with Identity Platform` if we are comfortable taking on Google Cloud as a parallel platform and want low MAU cost at moderate scale.

### Deferred Option

- Do not add a self-hosted auth path to the MVP shortlist unless the team explicitly decides to own passwordless delivery, abuse protection, account recovery, and auth compliance in-house.

## Required Architecture Boundaries

- Domain models must not import auth or payment SDKs.
- Application use cases consume role-based ports such as `IdentityProvider`, `SessionRepository`, `CheckoutGateway`, `PaymentEventStore`, and `AccessPolicyRepository`.
- Infrastructure adapters own provider payload mapping, signature verification, retry semantics, and external customer or checkout identifiers.
- API routes remain thin and translate use-case outputs into Civitas schemas.
- The web app consumes Civitas API routes only for session, account access, and checkout initiation.

## Reserved Backend Surface

These route families should be treated as the minimum contract surface for the phase:

- `GET /api/v1/session`
- `POST /api/v1/auth/start`
- `GET /api/v1/auth/callback`
- `POST /api/v1/auth/signout`
- `GET /api/v1/me/access`
- `POST /api/v1/billing/checkout-sessions`
- `POST /api/v1/billing/webhooks`

Exact path names may change, but the shape should remain:

- session introspection
- sign-in bootstrap
- callback completion
- sign-out
- account access or plan introspection
- checkout creation
- webhook ingestion

## Security And Compliance Decisions

- App session cookie must be `HttpOnly`, `Secure`, and same-site constrained.
- Mutating cookie-authenticated endpoints should validate `Origin` or equivalent anti-CSRF protections.
- Webhook handlers must verify provider signatures before persisting or reconciling any event.
- Provider secrets belong in managed secret storage and never in frontend code.
- Audit fields must record provider reference IDs, timestamps, and reconciliation outcomes for support and refund handling.

## Outputs Required From This Gate

1. Chosen auth-provider pattern and callback flow
2. Chosen payment-provider pattern and webhook flow
3. Agreed internal premium product, capability, and entitlement names
4. Reserved API route families
5. `10G-premium-access-matrix.md` frozen as the free-baseline versus premium-feature source of truth
6. Documented fallback behavior for provider outage, expired session, and duplicate webhook delivery

## Acceptance Criteria

- Product and provider choices are documented with enough specificity for implementation without reopening core flow questions.
- Premium is explicitly defined as account-level feature access rather than geography access.
- Security-sensitive decisions for cookies, callbacks, and webhooks are defined.
- The remaining Phase 10 documents can reference stable boundaries without ambiguity.
