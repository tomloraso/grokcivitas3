# Core Page Performance Plan

## Purpose

Turn the measured latency findings for the two core school journeys into an implementation plan ordered by impact:

- `/schools/:urn`
- `/compare?urns=...`

This supplements `.planning/phases/phase-12-post-mvp/11E-performance-and-cache-optimization.md` with a near-term, evidence-based plan for the current product.

## Status (2026-03-08)

- Priority 1 is complete.
- Request-time benchmark materialization has been removed from the web request path.
- `metric_benchmarks_yearly` is now rebuilt through post-promote pipeline materialization for benchmark-affecting sources or via the manual CLI command:
  - `uv run --project apps/backend civitas pipeline materialize-benchmarks --all`
- Local verification showed the old cold-path benchmark materialization work taking about `26.6s` for a single-school rebuild and about `31.2s` for a full rebuild, while the updated request path stayed sub-second on the target profile and compare journeys with an empty benchmark cache.

## Baseline (2026-03-08)

Measured locally against the current app and API:

- Browser first paint is acceptable; time-to-data is not.
- `/api/v1/schools/105448` took about `26s` on a cold browser navigation.
- `/api/v1/schools/compare?urns=106015,105384,106021` took about `52s` on a cold browser navigation.
- Direct backend use-case timings showed the same pattern:
  - profile: about `39.5s` cold, then low hundreds of milliseconds once warm
  - trends: about `41.6s` cold, then low hundreds of milliseconds once warm
  - compare: about `82.3s` cold, then low hundreds of milliseconds once warm
- The dominant cold-path cost is synchronous benchmark materialization in `apps/backend/src/civitas/infrastructure/persistence/postgres_school_trends_repository.py`.

## Success Criteria

Production targets for first anonymous visits to these pages:

- school profile API p95 under `750ms`
- compare API p95 under `1000ms` for 3-school compare sets
- profile page data-ready under `1.5s`
- compare page data-ready under `1.75s`
- no request path should depend on on-demand benchmark recomputation

## Priority 1: Remove Request-Time Benchmark Materialization (Completed 2026-03-08)

### Why

This is the main source of the 40-80 second cold path. The request path currently falls back to `_compute_metric_benchmark_rows(...)` on cache miss inside `get_metric_benchmark_series(...)`.

Relevant code:

- `apps/backend/src/civitas/infrastructure/persistence/postgres_school_trends_repository.py`
- `apps/backend/src/civitas/application/school_profiles/use_cases.py`
- `apps/backend/src/civitas/application/school_compare/use_cases.py`

### Work

1. Extract benchmark materialization into an explicit pipeline-side operation.
2. Run that operation after data promotion completes, using the same data version boundary already tracked for cache invalidation.
3. Add a backfill command to recompute benchmark rows for all schools, plus a scoped command for specific URNs when needed.
4. Change the API request path to read precomputed benchmark rows only.
5. On benchmark miss, return stale or partial data and emit telemetry; do not compute benchmarks inline during the request.

### Done When

- `get_metric_benchmark_series(...)` is read-only on the request path.
- cold profile and compare requests no longer trigger benchmark recomputation.
- first-hit latency is bounded by normal DB reads, not long-running aggregation.

### Outcome

- Implemented in `apps/backend/src/civitas/infrastructure/persistence/postgres_school_trends_repository.py`.
- Requests now return cached, partial, or empty benchmark data without recomputing inline.
- Benchmark materialization now runs after successful Gold promotes for benchmark-affecting pipeline sources.
- A manual backfill command exists for full or scoped rebuilds.
- Integration and unit coverage were added for request-path reads, pipeline callback execution, and CLI materialization flows.

## Priority 2: Batch Compare Data Loading

### Why

Compare currently loops requested URNs and loads profile plus benchmark data sequentially. That multiplies the cold path and keeps warm-path latency higher than necessary.

### Work

1. Add bulk repository methods for:
   - school profiles by URN set
   - latest benchmark rows by URN set
2. Refactor the compare use case to fetch all schools in one pass and preserve requested order in the response.
3. Avoid repeated benchmark-series lookups when only latest compare rows are needed.
4. Add tests for 2-school, 3-school, and 4-school compare latency-sensitive paths.

### Done When

- compare no longer performs `N` benchmark loads for `N` URNs.
- adding a third or fourth school increases latency modestly rather than multiplicatively.

## Priority 3: Stop Blocking Profile Response On Benchmark Enrichment

### Why

The profile endpoint builds benchmark data before returning, even though the web page already hydrates trends and dashboard data separately. That keeps the core profile blocked on a secondary payload.

### Work

1. Make profile benchmarks optional at the use-case boundary.
2. Return the core profile payload as soon as the cached school profile is available.
3. If benchmark snapshot data is available cheaply, include it; otherwise omit it and let the page continue with the separate trend/dashboard requests.
4. Ensure the frontend treats missing benchmark data as a valid partial-success state.

### Done When

- `/schools/:urn` returns core profile data without waiting on benchmark enrichment.
- header, overview, Ofsted, and area context can render independently of benchmark readiness.

## Priority 4: Deduplicate Trend And Dashboard Benchmark Work

### Why

The dashboard use case currently builds trends and then fetches benchmark series again. That duplicates backend work during a single navigation.

### Work

1. Introduce a shared application-level read model for trend data plus benchmark series.
2. Refactor `GetSchoolTrendDashboardUseCase` to reuse the same repository data already needed by `GetSchoolTrendsUseCase`.
3. Avoid double-fetching benchmark series for the same URN inside the same request chain.

### Done When

- dashboard generation does not re-read benchmark series after trends already loaded it.
- trends and dashboard requests remain independently callable but share a common internal data builder.

## Priority 5: Add Shared HTTP Caching With Versioned Invalidation

### Why

Current caching is mostly in-process and browser-memory only. That helps warm SPA navigations but does not help the first production user behind a CDN or reverse proxy.

### Work

1. Add `ETag` or equivalent versioned validators to:
   - `/api/v1/schools/{urn}`
   - `/api/v1/schools/{urn}/trends`
   - `/api/v1/schools/{urn}/trends/dashboard`
   - `/api/v1/schools/compare`
2. Add `Cache-Control` headers with `s-maxage` and `stale-while-revalidate` for anonymous-safe responses.
3. Key validators from pipeline/cache version state so invalidation remains deterministic.
4. Add `Vary` rules where auth or user-specific behavior could affect caching.

### Done When

- repeated anonymous requests can be served from shared cache layers.
- cache invalidation is tied to dataset version changes, not arbitrary TTL expiry alone.

## Priority 6: Warm Critical Data After Deploy And After Pipeline Runs

### Why

Even with the request path fixed, users should not be the first actor to pay for cold object creation, connection churn, or cache population.

### Work

1. Add a warm-up job after deploy for a curated set of high-traffic URNs and compare sets.
2. Add a warm-up job after pipeline completion for:
   - recently viewed or editorially important schools
   - top compare cohorts
   - benchmark snapshot readers
3. Record warm-up success and duration in operations telemetry.

### Done When

- production cold starts are mostly hidden behind automated warm-up.
- hot profile and compare pages land near warm-path latency from the first user visit.

## Priority 7: Frontend Delivery Refinements

### Why

Frontend work is not the main bottleneck, but there are still a few targeted wins that improve perceived speed and reduce unnecessary work on direct profile/compare entry.

### Work

1. Lazy-load the search/home route for direct entry into profile or compare pages so those pages do not pull search-only code upfront.
2. Extend existing intent prefetch to include:
   - route chunks for school profile
   - dashboard request where it improves real navigation
3. Keep compare/profile loading skeletons lightweight and stable so they do not remount excessively during staged hydration.
4. Confirm whether duplicate session fetches are production-visible or just local `StrictMode` noise before changing auth bootstrap behavior.

### Done When

- direct profile and compare entry avoids unnecessary search-route payload.
- hover/focus/tap intent prefetch materially improves in-app navigations from search results.

## Priority 8: Observability And Regression Gates

### Why

The optimization work needs production validation. This area already has warm/cold divergence, so measurements must distinguish between them.

### Work

1. Add backend histograms for:
   - `GetSchoolProfileUseCase`
   - `GetSchoolTrendsUseCase`
   - `GetSchoolTrendDashboardUseCase`
   - `GetSchoolCompareUseCase`
   - benchmark repository reads
2. Emit explicit cache-hit and cache-miss counters for benchmark data.
3. Add frontend marks for:
   - route shell visible
   - profile data ready
   - compare data ready
4. Add synthetic probes for the two target URLs after deploy.
5. Add page-specific performance checks to CI or scheduled monitoring using production-like builds.

### Done When

- p50 and p95 cold vs warm behavior is visible.
- regressions on the two target pages are detected before users report them.

## Recommended Delivery Sequence

### Wave 1

- Priority 8 instrumentation for the current hot path
- Priority 1 completed on 2026-03-08; keep instrumentation focused on validating the new read-only request path

### Wave 2

- Priority 2 compare batching
- Priority 3 profile response unblocking
- Priority 4 trend/dashboard deduplication

### Wave 3

- Priority 5 shared HTTP caching
- Priority 6 warm-up jobs

### Wave 4

- Priority 7 frontend refinements

## Risks To Manage

- Cache invalidation must stay aligned with pipeline promotion boundaries.
- Returning partial benchmark data must not silently degrade UX; the UI needs explicit partial-data handling.
- Compare bulk-loading must preserve response ordering and existing error semantics.
- CDN/shared caching must not leak authenticated or tiered responses across users.
