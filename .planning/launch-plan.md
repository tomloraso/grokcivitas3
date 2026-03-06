# Launch Plan

## Document Control

- Status: Planning baseline
- Last updated: 2026-03-06
- Scope: Launch sequencing aligned to current product completeness

## Current Readiness Snapshot

As of 2026-03-06, Civitas already supports the core research journey for search, school profile depth, multi-year trends, benchmark dashboards, and AI-generated school overviews. Two important MVP slices are still planned:

1. school comparison
2. premium access and payments

Launch planning should therefore be staged around product completeness rather than treated as a single public launch date.

## Launch Sequence

### Stage 1 - Internal dogfood and data-confidence pass

- Use the current implementation for internal and trusted-user validation.
- Focus on data correctness, trend readability, completeness messaging, and operational repeatability.
- Exit gate: pipeline, profile, trends, and dashboard behavior are stable on canonical data hydration.

### Stage 2 - Research beta

- Open access to a small group of target users after Phase 8 compare is complete.
- Validate whether users can move from postcode search to shortlist to comparison without assistance.
- Collect structured feedback on missing metrics, unclear terminology, and willingness to pay.

### Stage 3 - Public free launch

- Public launch should follow successful Phase 8 sign-off.
- Position the product around honest, source-backed school research, not opinion or recommendations.
- Public launch scope should emphasize search, profile depth, trends, benchmarks, and comparison.

### Stage 4 - Premium launch

- Premium launch should follow successful Phase 9 sign-off.
- Position premium around deeper postcode-level research and access control clarity.
- Conversion flow must be backed by proven entitlement enforcement and payment reconciliation.

## Readiness Gates

Before public launch:

- `make lint` and `make test` are green in a stable repo state.
- Canonical source hydration succeeds on the documented source set.
- Search, profile, trends, dashboard, and compare journeys are demoable end to end.
- Completeness and source-limited messaging are user-readable.

Before premium launch:

- Authentication and session flows are stable.
- Payment and webhook flows are proven in staging.
- Backend enforcement blocks premium-only data correctly.
- Support and refund handling process is documented.

## Early Success Measures

- Search-to-profile conversion rate
- Profile-to-compare usage rate
- Compare completion rate
- Premium conversion rate after launch
- Data-refresh success rate and time-to-recover from failures

## Open Decisions

1. Whether there is one public launch or a soft public beta before premium goes live.
2. Whether premium unlocks are postcode-only, account-wide for a period, or both.
