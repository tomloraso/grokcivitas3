# Deployment Strategy (MVP Baseline)

## Document Control

- Status: Draft
- Last updated: 2026-02-27
- Scope: Planning baseline for production hosting assumptions

## Purpose

Define minimum deployment assumptions early so architecture and pipeline decisions are grounded in a realistic runtime model.

## Environment Model

1. **Local development**
   - Docker Compose services for PostGIS and supporting dependencies.
   - Bronze storage on local filesystem.
2. **Staging**
   - Cloud-managed Postgres with PostGIS enabled.
   - Bronze storage in cloud object storage.
   - API and pipeline worker deployed as separate services.
3. **Production**
   - Same topology as staging with production scale, backups, and alerting.

## Locked Decisions

1. **Serving database**
   - Managed PostgreSQL with PostGIS extension in staging/production.
2. **Bronze storage**
   - Immutable raw files in object storage (local filesystem only for local dev).
3. **Pipeline execution**
   - CLI-triggered pipelines run from a scheduled job/worker service.
   - No Airflow/Dagster requirement for MVP.
4. **Migration execution**
   - Alembic migrations run as part of deployment workflow before API rollout.
5. **Secrets and config**
   - Runtime config via environment variables.
   - Secrets stored in managed secret store (provider-specific selection deferred).

## Operational Baseline

1. **Backups**
   - Daily database backups with restore validation in non-production.
2. **Observability**
   - Capture API health, pipeline run status, and ingestion failures.
3. **Release safety**
   - Deploy API and pipeline services independently.
   - Keep rollback path for DB migrations and application revisions.

## Deferred Decisions

1. Cloud provider and exact managed service SKUs.
2. Scheduler implementation details (managed cron/job runner vs container-native scheduler).
3. IaC stack choice details beyond repo baseline (Bicep vs Terraform per environment).

## Related Documents

- `.planning/overview.md`
- `.planning/data-architecture.md`
- `.planning/phased-delivery.md`
