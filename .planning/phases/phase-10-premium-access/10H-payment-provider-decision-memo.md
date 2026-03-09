# 10H - Payment Provider Decision Memo

## Document Control

- Status: Current recommendation for Stage 10B planning
- Last updated: 2026-03-09
- Owner: Product + Engineering
- Pricing and product snapshot date: 2026-03-09. Re-verify before procurement or contract sign-off.

## Purpose

Choose the billing provider shape for Phase 10 Stage 10B so checkout, recurring Premium billing, webhook reconciliation, and account recovery can be implemented without reopening the core access architecture.

This memo does not change the existing Phase 10 boundary:

- Civitas owns the internal product catalog, capability mapping, entitlements, and access decisions.
- The provider owns payment collection, subscription billing, and signed webhook delivery.
- The web app consumes Civitas API routes only for session, access, and checkout start.

## Fixed Inputs From The Phase 10 Plan

- Premium is account-level.
- Stage 10B currently assumes one recurring launch product that grants the three Phase 10 launch capabilities.
- Checkout requires a signed-in user.
- Redirect success is never the source of truth for entitlement activation.
- Webhook reconciliation remains backend-owned.
- Access evaluation stays capability-based and backend-owned after payment reconciliation.

## Decision Criteria

Scores below are relative to Civitas as it exists today, not a generic market ranking.

Weights:

- Architecture fit with the current backend-owned session and entitlement model: 30
- Delivery speed and implementation simplicity for Phase 10B: 25
- Tax and compliance offload for a small UK-focused team: 15
- Hosted subscription lifecycle and self-serve billing tooling: 10
- Operational clarity for support, replay, and audit: 10
- Cost predictability at early stage: 10

## Providers Considered

### Stripe

- Model: payment processor
- Best fit when Civitas wants the cleanest engineering path and is willing to remain the merchant of record
- Strongest match for hosted checkout plus backend-owned entitlements

### Paddle

- Model: merchant of record
- Best fit when Civitas wants to offload more tax, invoicing, and subscription-compliance work
- Strongest alternative if commercial operations simplicity matters more than keeping the billing flow maximally neutral

### Lemon Squeezy

- Model: merchant of record
- Worth considering for a smaller, simpler SaaS-style launch
- Less conservative default than Paddle for a production-first, support-heavy product

### FastSpring

- Model: merchant of record
- Worth considering only if merchant-of-record is mandatory and a more sales-led commercial stack is acceptable
- Weaker fit for the current repo's developer-first workflow

### Chargebee Plus Stripe

- Model: subscription-management layer plus payment processor
- Worth considering only if Civitas already knew it needed enterprise-grade catalog, dunning, invoicing, and rev-rec style billing operations
- Overbuilt for the current Phase 10 launch shape

## Decision Matrix

| Provider | Billing model | Architecture fit (30) | Delivery speed (25) | Tax/compliance offload (15) | Lifecycle tooling (10) | Operational fit (10) | Cost predictability (10) | Weighted total / 500 | Notes |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| Stripe | Payment processor | 5 | 5 | 3 | 5 | 4 | 4 | 450 | Best engineering fit for the current plan. |
| Paddle | Merchant of record | 4 | 4 | 5 | 5 | 5 | 4 | 435 | Best ops-offload alternative. |
| Lemon Squeezy | Merchant of record | 3 | 4 | 5 | 4 | 4 | 4 | 385 | Viable smaller-team option, but not the default recommendation. |
| FastSpring | Merchant of record | 2 | 3 | 5 | 4 | 4 | 2 | 310 | More commercial overhead and less developer-first fit. |
| Chargebee + Stripe | Hybrid stack | 2 | 2 | 3 | 5 | 4 | 2 | 265 | Too much surface area for Phase 10. |

## Provider Snapshot

### Stripe

- Hosted checkout, subscriptions, billing portal, webhooks, and tax tooling are all available from one platform.
- The integration shape is a very close match for the current Civitas design: provider-hosted checkout, backend webhook reconciliation, and first-party entitlement projection.
- Public pricing on the UK pricing page is processor-style pricing rather than merchant-of-record pricing. That usually means lower direct payment fees than merchant-of-record vendors, but Civitas keeps more tax and merchant responsibility.

### Paddle

- Paddle positions itself as merchant of record and bundles checkout, subscription billing, tax handling, invoicing, and customer portal capability into one commercial layer.
- That reduces non-engineering operational burden, especially if Civitas expects UK or EU consumer billing from day one.
- The tradeoff is more provider-shaped billing concepts and a somewhat less neutral integration surface than Stripe.

### Lemon Squeezy

- Similar headline commercial posture to Paddle for small software teams: merchant of record, subscriptions, customer portal, and webhook flows.
- Strong indie-SaaS fit, but a weaker default than Paddle or Stripe for a conservative first payment launch where long-term tooling maturity matters.

### FastSpring

- FastSpring is also merchant of record and can handle subscriptions, global payments, and tax handling.
- It is worth knowing about, but it is not the cleanest first choice for the current Civitas stack.

### Chargebee Plus Stripe

- Chargebee is strongest when billing operations become a product area of their own.
- That is not the current Phase 10 need. Adding Chargebee now would likely slow delivery and complicate the data model for little launch benefit.

## Recommendation

Recommend `Stripe` for the Phase 10 Stage 10B implementation.

Reasoning:

1. It is the closest fit to the Phase 10 architecture already documented in `10A`, `10C`, `10D`, and `10E`.
2. It lets Civitas keep the clean provider boundary already planned: hosted checkout outside the app, signed webhooks into backend infrastructure, first-party entitlement projection inside Civitas.
3. It minimizes design churn in the current codebase and avoids introducing a second strong set of provider-owned concepts into the web app.
4. It still gives the required hosted primitives for MVP: checkout, subscriptions, customer portal, webhook verification, and tax tooling.

Recommended implementation posture if Stripe is chosen:

- Use Stripe Checkout for the initial Premium purchase flow.
- Use Stripe's billing portal for self-serve cancellation, payment-method updates, and recovery instead of building custom billing management pages in Phase 10.
- Use signed webhook events as the sole activation path for entitlements.
- Add a first-class `billing_subscriptions` table in Civitas so entitlements remain the access projection rather than the billing source of truth.
- If Civitas remains merchant of record, evaluate Stripe Tax during implementation rather than bolting tax handling on later.

## When To Choose Paddle Instead

Choose `Paddle` instead of Stripe if these become the dominant requirements before Stage 10B starts:

- merchant-of-record from day one
- reduced VAT and sales-tax operations burden
- provider-owned invoicing and customer-billing admin as a stronger priority than neutral billing boundaries
- a very small operating team where commercial-support simplification matters more than raw integration cleanliness

If those requirements dominate, Paddle becomes the best alternative and is fully compatible with the rest of the planned Civitas entitlement architecture.

## Providers Worth Knowing About But Not Recommending By Default

- `Lemon Squeezy`: good smaller-team merchant-of-record option, but weaker default than Paddle or Stripe for the current repo and launch seriousness.
- `FastSpring`: legitimate merchant-of-record option, but not the strongest fit for a first implementation in this codebase.
- `Chargebee + Stripe`: not recommended unless the billing roadmap already justifies a dedicated subscription-operations platform.

## Required Architecture Consequences Regardless Of Provider

These changes should happen even if the final provider choice changes:

- Keep `premium_products` and `product_capabilities` as Civitas-owned commercial mapping.
- Keep access policy in backend code derived from `10G-premium-access-matrix.md`.
- Add `billing_subscriptions` or equivalent first-class recurring-billing table.
- Keep provider IDs and webhook payload mapping in infrastructure adapters only.
- Keep entitlements as the backend access projection, not the billing system of record.
- Prefer provider-hosted customer-portal flows for subscription management in MVP.

## Source Snapshot

Official sources reviewed on 2026-03-09:

- Stripe Checkout: <https://docs.stripe.com/payments/checkout>
- Stripe subscriptions with Checkout: <https://docs.stripe.com/payments/checkout/build-subscriptions>
- Stripe Tax: <https://docs.stripe.com/payments/checkout/taxes>
- Stripe pricing: <https://stripe.com/gb/pricing>
- Paddle overview: <https://developer.paddle.com/>
- Paddle customer portal: <https://developer.paddle.com/concepts/customer-portal>
- Paddle webhook verification: <https://developer.paddle.com/webhooks/signature-verification>
- Paddle pricing: <https://www.paddle.com/pricing>
- Lemon Squeezy pricing: <https://www.lemonsqueezy.com/pricing>
- FastSpring pricing: <https://fastspring.com/pricing/>
- Chargebee pricing: <https://www.chargebee.com/pricing/>
