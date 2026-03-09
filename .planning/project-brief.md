# Civitas Project Brief (v2)

## Purpose

Civitas is a UK public-data research platform that helps people make high-stakes, location-based decisions using raw, unfiltered government datapoints presented clearly and comparably.

The first vertical is school research for ages 4-16. The platform is intentionally designed to extend to other public datasets over time, including deprivation, crime, house prices, health, and public services.

## Product Vision

- Facts-only, decision-grade research experience.
- Fast, mobile-first discovery and comparison.
- Location-first navigation built around postcode and map.
- Extensible data and application architecture beyond schools.

## Primary Users

- Parents and guardians researching schools by location.
- House movers or renters evaluating school context before relocation.
- Education-focused professionals who need quick side-by-side comparisons.

## MVP Objectives

1. Make fragmented public school data usable in one interface.
2. Provide clear signal with trends and risk flags without editorial commentary.
3. Enable confident comparison across nearby schools.
4. Support a freemium model with backend-enforced access control.

## MVP User Journeys

1. Postcode search
   - User enters a UK postcode.
   - System resolves the postcode to latitude and longitude.
   - System returns nearby schools in a configurable radius sorted by straight-line distance.
2. Browse nearby results
   - User sees a mobile-friendly ranked results view: a desktop decision table with headline stats and stacked result cards on mobile.
   - User uses a linked map and shortlist-friendly compare entry points.
   - User can sort and filter the result set, with straight-line distance as the default postcode-search order.
3. School profile
   - User sees core identifiers, headline indicators, and multi-year trends.
   - User sees Ofsted history and benchmark context where available, including inline benchmark cues and the benchmark dashboard drill-down, with neighbourhood context unlocked through premium access.
   - User may also see two pre-generated AI summaries with explicit disclaimer and provenance: a factual overview and an evidence-grounded analyst view.
4. Compare schools
   - Premium users can compare up to four schools side by side using a consistent metric set.
5. Paywall and purchase
   - Free users can complete the core research journey across search, school profiles, and baseline trends.
   - Paid users unlock side-by-side comparison, neighbourhood context, and premium analysis on the same account.
   - Benchmark context remains free in Phase 10, including inline benchmark cues and the benchmark dashboard drill-down.

## Schools Data Scope (v1)

Minimum indicator groups:

- Demographics and need: ethnicity, FSM/FSM6, EHCP/SEN, SEND primary need, EAL, gender where published, and top non-English languages where school-level data exists.
- Attendance and behaviour: attendance, persistent absence, suspensions, and exclusions.
- Performance: KS2, KS4, Attainment 8, Progress 8, EBacc, and disadvantaged gap where published.
- Staffing signals: pupil-to-teacher ratio, supply share, QTS coverage, teacher turnover and related workforce metrics where school-level data exists.
- Leadership and inspection: headteacher and tenure signals, Ofsted latest rating, sub-judgements, and timeline.
- Area context: local crime context, IMD and IDACI, and house-price context.
- Trends and benchmarks: multi-year coverage, year-on-year deltas, dashboard views, and benchmark context.

## Data Pipeline Requirements

- Scheduled ingestion for GIAS, DfE release-file and API datasets, Ofsted assets, and area-context sources.
- Bronze -> Silver -> Gold flow with reproducible raw asset retention.
- Upsert model supporting current snapshot plus historical yearly records per school.
- Explicit completeness metadata for source-limited or partially available fields.
- Extensible schema and module model for future datasets without breaking existing experiences.

## Application And UX Requirements

- Mobile-first responsive web app with PWA readiness.
- Dashboard-style presentation with high visual signal and clear trend behavior.
- Map interactions including markers, radius context, and marker-to-detail navigation.
- User-selectable dark and light display mode with persistent preference.
- Backend-generated OpenAPI contracts as the source of truth for frontend integration.

## AI Summary Guardrails

- At most two AI-generated school summaries are in MVP scope: `overview` and `analyst`.
- The overview must be pre-generated, factual, provenance-backed, and never advice-like.
- The analyst summary may describe patterns or signals in the published evidence, but it must remain evidence-grounded and never advice-like.
- The exact free versus premium placement of any second AI artifact is a product-tier decision, not a model-behavior decision.
- Both summaries must display a clear disclaimer and must not replace primary source data.

## Security, Privacy, And Access

- Email-based authentication for MVP.
- Backend-enforced feature-tier entitlements for premium access.
- GDPR-conscious posture with minimal personal data and limited tracking.

## Non-Functional Targets

- Performance: typical page loads under roughly two seconds on broadband or mobile.
- Reliability: target 99.9% availability.
- SEO-ready architecture for later static or indexable location pages.

## Operations (MVP)

- Basic admin control to trigger and monitor data refresh runs.
- Health indicators for row counts, last refresh timestamps, and ingestion error visibility.

## Explicit Non-Goals (MVP)

- Editorial rankings, recommendations, or subjective scoring.
- Full coverage of every UK public dataset in the initial release.
- Complex enterprise admin tooling.
- Conversational AI, live-generated summaries, or free-form assistant features.
- PDF report export.

## Business Model (Initial)

- Free tier for core school research.
- Paid account-level premium tier for side-by-side comparison, neighbourhood context, and richer analysis.

## Success Criteria (Initial)

- Users can search by postcode and assess nearby schools in minutes.
- Users can open school profiles and understand baseline evidence and multi-year trends without paying.
- Premium users can compare nearby schools and unlock neighbourhood context without friction.
- Premium users can unlock richer analysis and advanced features without disrupting the free research experience.
- Data refreshes are reliable, auditable, and trend history is maintained.

## Open Decisions

- Final premium packaging: monthly, annual, one-time, or hybrid.
- Whether neighbourhood context should remain premium after launch learning or move back into the free baseline.
- Exact metric thresholds for risk flags.
- Whether post-launch capacity should pull favourites forward ahead of broader post-MVP slices.
