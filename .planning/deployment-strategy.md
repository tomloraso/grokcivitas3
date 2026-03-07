# Deployment Strategy

## Document Control

- Status: Current MVP baseline
- Last updated: 2026-03-06
- Scope: Runtime assumptions for web, backend, pipelines, and AI summary generation

## Purpose

Define the minimum deployment assumptions that the current Civitas implementation and remaining MVP phases should target.

## Runtime Components

### Web app

- React frontend served as a static web application or equivalent CDN-backed artifact.
- Consumes backend OpenAPI-derived contracts only.

### Backend API

- FastAPI application serving search, profile, trends, dashboard, and AI overview reads.
- Connects to PostgreSQL with PostGIS enabled.

### Pipeline worker

- Runs Bronze -> Silver -> Gold pipeline commands on a schedule or through operator-triggered jobs.
- Must be deployable independently from the API.

### AI summary execution

- Runs post-pipeline or on-demand summary generation jobs.
- May share the pipeline runtime or run as a separate worker depending on operational needs.
- Must not run inline with profile requests.

### Data and storage

- Managed PostgreSQL with PostGIS for serving and staging tables.
- Object storage for Bronze raw assets outside local development.
- Managed secret storage for runtime credentials and provider keys.

## Environment Model

### Local development

- Docker Compose for PostgreSQL and supporting services.
- Bronze root on local filesystem.
- API, web, and pipelines run directly from the repo.

### Staging

- Production-like topology with managed Postgres and object storage.
- Web, API, pipeline worker, and AI job execution validated before promotion.
- Used for provider integration tests and premium-access rehearsal.

### Production

- Same logical topology as staging.
- Backups, observability, and rollback paths are mandatory.
- API, web, and worker deployments remain independently releasable.

## Deployment Workflow

1. Apply database migrations before application rollout.
2. Deploy backend API and web app independently.
3. Keep pipeline worker deployment decoupled from the API so source refresh work is operationally isolated.
4. Trigger AI summary refresh only after the underlying data refresh has succeeded.

## Operational Baseline

- Daily database backups with restore rehearsal in non-production.
- Centralized logging for API, pipelines, and AI generation runs.
- Health checks for API availability and job-run visibility.
- Alerting for pipeline freshness, coverage drift, and repeated hard failures.

## Deferred Decisions

1. Final cloud provider and concrete managed service SKUs.
2. Exact scheduler or job-runner product.
3. Whether AI summary execution should use the same worker image as pipelines or split into a dedicated queue-backed service.
4. Whether Phase 11 optimization work introduces read replicas, materialized views, or CDN caching beyond the current baseline.

## Related Documents

- `overview.md`
- `data-architecture.md`
- `phased-delivery.md`
- `ai-features.md`
