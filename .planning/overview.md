# Civitas - System Overview

## What we're building

A UK public-data research platform that consolidates fragmented government datasets into a fast, decision-grade web experience. MVP vertical: school research for ages 4-16. Designed to extend to other public datasets (crime, deprivation, house prices, health) without architectural rework.

## Key product requirements driving architecture

1. **Fast user experience.** Typical page loads under ~2 seconds; key API endpoints should target low-latency responses.
2. **Location-first navigation.** Postcode-to-radius search is the primary entry point.
3. **Trend visibility.** 3-5 years of historical data with year-on-year deltas.
4. **Extensible data model.** Adding a new dataset should not break existing experiences.
5. **Reproducible data pipeline.** Re-run from source at any time; full lineage.
6. **Freemium access control.** Backend-enforced entitlements, not UI-only gating.

## High-level architecture

```
+-----------------------------------------------------------+
| Data Sources (gov.uk CSVs, APIs, ONS downloads)          |
+-----------------------------+-----------------------------+
                              | Scheduled ingestion
                              v
+-----------------------------------------------------------+
| Pipeline (Python)                                         |
| Bronze (raw files) -> Staging (Postgres) -> Gold         |
+-----------------------------+-----------------------------+
                              | Materialized, indexed
                              v
+-----------------------------------------------------------+
| Backend API (FastAPI)                                     |
| Layered: domain -> application -> infrastructure          |
| Bootstrap composes concrete dependencies                  |
| PostGIS spatial queries, structured endpoints             |
+-----------------------------+-----------------------------+
                              | OpenAPI contract
                              v
+-----------------------------------------------------------+
| Web App (React / Vite / TypeScript)                      |
| Mobile-first, map + list, dashboard-style presentation   |
+-----------------------------------------------------------+
```

## Technology choices

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Backend runtime | Python 3.11+ / FastAPI | Aligns with current repo constraints and data pipeline needs |
| Backend architecture | Hexagonal layering (`domain`, `application`, `infrastructure`, `api`, `cli`, `bootstrap`) | Testable, clear dependency direction, explicit composition root |
| Serving database | PostgreSQL + PostGIS | Spatial indexing for radius queries, relational joins for metric lookups, proven at this scale |
| Pipeline staging | PostgreSQL staging tables | Clean, validate, type-cast within the same engine as serving; one query language end-to-end |
| Raw archive | CSV/JSON files (Bronze layer) | Immutable audit trail of every source download |
| Frontend | React + Vite + TypeScript | Fast builds, strong typing, ecosystem maturity |
| API contract | Backend-generated OpenAPI | Single source of truth; frontend consumes typed client |
| Package management | uv (Python) / npm (TypeScript) | Fast, deterministic dependency resolution |
| Monorepo structure | Apps-first (`apps/backend`, `apps/web`) | Clean ownership boundaries, shared tooling at root |

## Data sources (MVP)

| Source | Format | Refresh cadence | Primary use |
|--------|--------|-----------------|-------------|
| DfE pupil characteristics | CSV | Annual (June) | Demographics, FSM, SEN, ethnicity |
| GIAS bulk downloads | CSV | Ongoing | School identifiers, type, phase, geography |
| Ofsted | API / CSV | Ongoing | Inspection ratings, dates, timeline |
| Police UK data | Monthly bulk CSV (+ API fallback) | Monthly | Street-level crime context (1-mile radius) |
| Land Registry Price Paid | CSV | Monthly | House price snapshot (optional MVP) |
| Postcodes.io | REST API | Stable | Postcode -> lat/lng resolution |
| ONS IMD / LSOA stats | CSV | Periodic | Deprivation deciles, child poverty |

## Pipeline model

- **Bronze:** Raw files exactly as downloaded (CSV, JSON). Immutable. Timestamped.
- **Staging:** PostgreSQL staging tables. Cleaned, validated, type-cast. Per-source, per-run. Rejected rows logged.
- **Gold:** PostgreSQL + PostGIS production tables. Enriched, joined, denormalized for API access. Indexed for spatial and point queries.

Bronze is the reproducibility checkpoint. The full pipeline can be re-run from raw files at any time.

## Key architectural decisions

1. **PostgreSQL as the sole serving store** - not Parquet, not a data lake query engine. Scale is modest (tens of thousands of schools, low millions of enrichment rows). PostGIS spatial indexes solve the radius query problem directly.
2. **Pipeline runs are batch, not streaming** - source data updates daily to annually. No real-time ingestion needed.
3. **Backend enforces all access control** - premium entitlements checked server-side, never client-only.
4. **OpenAPI is the contract boundary** - frontend never depends on backend internals, only on generated/typed API clients.
5. **Monorepo with strict layering** - backend enforces import boundaries; `api`/`cli` stay thin and `bootstrap` owns composition.

## What this document does NOT cover

- Detailed data schemas and pipeline design -> see `data-architecture.md`
- Phase-by-phase delivery plan -> see `phased-delivery.md`
- Frontend component architecture -> future planning doc
- Infrastructure / deployment topology -> future planning doc
