# Pipeline Guide

Read this guide before touching pipeline operations, data hydration, or sign-off evidence.

## Primary references

1. `docs/runbooks/pipelines.md` (user-facing operating model and zone flow)
2. `docs/runbooks/local-development.md` (canonical commands and env settings)
3. `.planning/phases/phase-3-hardening/*` (hardening acceptance criteria and sign-off)

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
- `metric_benchmarks_yearly` is a derived cache populated after successful Gold promotes for
  benchmark-affecting sources. Web requests must read it as a cache and must not rebuild
  benchmarks inline on the request path.

## Agent checklist (pipeline sessions)

1. Confirm current `CIVITAS_BRONZE_ROOT` and source overrides.
2. Run source pipelines in documented sequence.
3. For benchmark-affecting sources, confirm benchmark materialization ran after Gold promote or
   run `uv run --project apps/backend civitas pipeline materialize-benchmarks --all` before
   handoff if the cache needs a manual rebuild.
4. Validate run statuses and quality SLO output.
5. Verify `running=0` and no stale source locks before handoff.
