# Pipeline Guide

Read this guide before touching pipeline operations, data hydration, or sign-off evidence.

## Primary references

1. `docs/runbooks/pipelines.md` (user-facing operating model and zone flow)
2. `docs/runbooks/local-development.md` (canonical commands and env settings)
3. `.planning/phases/phase-hardening/*` (hardening acceptance criteria and sign-off)

## Non-negotiable flow

All pipeline runs must pass through:

1. Bronze (`data/bronze/<source>/<YYYY-MM-DD>`)
2. Silver (`staging` run-scoped normalized tables)
3. Gold (serving tables used by API/UI)

Do not bypass Silver and write raw assets directly into Gold.

## Canonical root

- Default and expected Bronze root: `data/bronze`
- Keep alternate roots for isolated experiments only.
- Before final sign-off, ensure production-like runs use canonical root unless explicitly documented otherwise.

## Data behavior expectations

- Bronze stores raw assets + metadata/manifests.
- Silver performs contract normalization and captures rejected records.
- Gold promotions are upserts on table keys (no key-level duplicates from reruns).

## Agent checklist (pipeline sessions)

1. Confirm current `CIVITAS_BRONZE_ROOT` and source overrides.
2. Run source pipelines in documented sequence.
3. Validate run statuses and quality SLO output.
4. Verify `running=0` and no stale source locks before handoff.
