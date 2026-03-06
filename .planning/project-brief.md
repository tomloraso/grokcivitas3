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
   - User sees school cards with headline stats and quick flags.
   - User uses a linked map and list view.
   - User can sort and filter the result set.
3. School profile
   - User sees core identifiers, headline indicators, and multi-year trends.
   - User sees Ofsted history, deprivation, crime, and benchmark context where available.
   - User may also see one pre-generated AI factual overview with explicit disclaimer and provenance.
4. Compare schools
   - User compares up to four schools side by side using a consistent metric set.
5. Paywall and purchase
   - Free users see headline data and limited ranking.
   - Paid users unlock the full postcode dataset for a time-boxed period.

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

## AI Overview Guardrails

- At most one AI-generated school overview in MVP scope.
- The overview must be pre-generated, factual, provenance-backed, and never advice-like.
- The overview must display a clear disclaimer and must not replace primary source data.

## Security, Privacy, And Access

- Email-based authentication for MVP.
- Backend-enforced entitlements for premium access.
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

- Free tier for headline insights.
- Paid postcode-level unlock for deeper local research.

## Success Criteria (Initial)

- Users can search by postcode and compare nearby schools in minutes.
- Users can open school profiles and understand local context and multi-year trends.
- Premium users can unlock full local data for postcode-level research.
- Data refreshes are reliable, auditable, and trend history is maintained.

## Open Decisions

- Final premium packaging: time-boxed unlock only, or time-boxed plus lifetime.
- Exact metric thresholds for risk flags.
- Which post-MVP expanders, such as report export or deeper house-price context, move up in priority after MVP.
