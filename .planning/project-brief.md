# Civitas Project Brief (v1)

## Purpose
Civitas is a UK public-data research platform that helps people make high-stakes, location-based decisions using raw, unfiltered government datapoints presented clearly and comparably.

The first vertical is school research for ages 4-16. The platform is intentionally designed to extend to other public datasets over time (for example: deprivation, crime, house prices, health, and public services).

## Product Vision
- Facts-only, decision-grade research experience.
- Fast, mobile-first discovery and comparison.
- Location-first navigation (postcode and map).
- Extensible data and application architecture beyond schools.

## Primary Users
- Parents and guardians researching schools by location.
- House movers/renters evaluating school context before relocation.
- Education-focused professionals who need quick side-by-side comparisons.

## MVP Objectives
1. Make fragmented public school data usable in one interface.
2. Provide clear signal with trends and risk flags without editorial commentary.
3. Enable confident comparison across nearby schools.
4. Support a freemium model (free headline data, paid detailed unlock).

## MVP User Journeys
1. Postcode search:
- User enters UK postcode.
- System resolves postcode to latitude/longitude.
- System returns schools in a configurable radius (default: 5 miles) sorted by straight-line distance.

2. Browse results:
- List of school cards with headline stats and quick flags.
- Interactive map with markers.
- Basic sorting/filtering (minimum: distance).

3. School profile:
- Core identifiers (name, type/phase, location).
- Headline indicators.
- 3-5 year trend summaries for key metrics.

4. Compare schools:
- Side-by-side comparison for up to 4 schools using a consistent metric set.

5. Paywall + purchase:
- Free: limited headline view and limited ranking.
- Paid: unlock full postcode dataset for 30 days.
- Optional lifetime unlock model (post-MVP if needed).

## Schools Data Scope (v1)
Minimum indicator groups:
- Demographics and need: ethnicity, FSM/FSM6, EHCP/SEN, young carers, top non-English languages.
- Attendance and behaviour: persistent/severe absence, exclusions/suspensions.
- Staffing signals: pupil-to-teacher ratio, supply-teacher percentage, teacher sickness days.
- Leadership and inspection: headteacher + tenure, leadership churn score, Ofsted rating/date/timeline.
- Area context: 1-mile crime context, IMD decile, child poverty context, optional house price snapshot.
- Trends: 3-5 year historical coverage with year-on-year deltas and trend direction.

## Data Pipeline Requirements
- Scheduled ingestion for DfE datasets, GIAS school identifiers/geography, and Ofsted timeline data.
- Enrichment joins for postcode/area datasets (crime, IMD, optional house prices).
- Upsert model supporting current snapshot + historical yearly records per school.
- Caching for expensive postcode enrichments (initial target TTL: 30 days).
- Extensible schema/module model for future datasets without breaking existing experiences.

## Application and UX Requirements
- Mobile-first responsive web app with PWA readiness.
- Dashboard-style presentation with high visual signal (big numbers, flags, small trend visuals).
- Map interactions including markers, radius context, and marker-to-detail navigation.
- User-selectable dark/light display mode with accessible contrast and persistent preference.

## Security, Privacy, and Access
- Email-based authentication for MVP.
- Backend-enforced entitlements for premium access (not UI-only).
- GDPR-conscious posture with minimal personal data and limited tracking.

## Non-Functional Targets
- Performance: typical page loads under ~2 seconds on broadband/mobile.
- Reliability: target 99.9% availability.
- SEO-ready architecture for later static/indexable location pages.

## Operations (MVP)
- Basic admin control to trigger and monitor data refresh runs.
- Health indicators: row counts, last refresh timestamps, and ingestion error visibility.

## Explicit Non-Goals (MVP)
- Editorial rankings, recommendations, or subjective scoring.
- Full coverage of every UK public dataset in initial release.
- Complex enterprise admin tooling.
- PDF report export (deferred to post-MVP).

## Business Model (Initial)
- Freemium access:
- Free tier for headline insights.
- Paid postcode-level unlock for detailed data.

## Success Criteria (Initial)
- Users can search by postcode and compare nearby schools in minutes.
- Premium users can unlock full local data for postcode-level research.
- Data refreshes are reliable, auditable, and trend history is maintained.

## Open Decisions
- Final premium packaging (30-day only vs 30-day + lifetime).
- Exact metric thresholds for risk flags.
- Which optional enrichments (for example house prices) ship in MVP vs next phase.
