# Known Issues

Living document. Remove an entry only after the fix is committed and verified in production.

---

## BUG-001 - School profile endpoint times out (benchmark query ignores persisted benchmark cache)

**Status:** FIXED
**Severity:** Critical
**Files:**
- `apps/backend/src/civitas/infrastructure/persistence/postgres_school_trends_repository.py`
- `apps/backend/tests/integration/test_school_trends_repository.py`

### Validation
Confirmed. `PostgresSchoolTrendsRepository.get_metric_benchmark_series()` always recomputed benchmark aggregates from source tables, even when `metric_benchmarks_yearly` already held the required national and local benchmark rows for the requested school context.

### Root cause
The repository persisted benchmark snapshots but had no cache-read path. Every request executed the full aggregation query, including the wide `school_geo` CTE and downstream benchmark aggregations, then wrote the results back into `metric_benchmarks_yearly`. The cache table was acting as write-only storage.

### Fix implemented
- Added a cache-first query path that resolves the target school's local benchmark context and joins the school's metric rows against persisted `metric_benchmarks_yearly` rows.
- Kept the full aggregation query only as a cache-miss fallback.
- Added `SET LOCAL work_mem = '64MB'` for the PostgreSQL fallback path to reduce disk spill risk when the expensive computation is genuinely needed.
- Added an integration test that seeds cached benchmark rows and verifies they are reused instead of recomputed.

### Verification
- `uv run --project apps/backend pytest apps/backend/tests/integration/test_school_trends_repository.py -q`
- `uv run --project apps/backend pytest`

---

## BUG-002 - Postcode resolver blocks on external HTTP after cache TTL expiry

**Status:** FIXED
**Severity:** High
**Files:**
- `apps/backend/src/civitas/infrastructure/http/postcode_resolver.py`
- `apps/backend/src/civitas/infrastructure/persistence/postgres_postcode_cache_repository.py`
- `apps/backend/tests/unit/test_cached_postcode_resolver.py`
- `apps/backend/tests/unit/test_postcode_cache_repository.py`

### Validation
Confirmed. `CachedPostcodeResolver.resolve()` only used `get_fresh()` and immediately fell back to the live Postcodes.io HTTP client on TTL expiry, even when an older cached postcode record with a valid `lsoa_code` was already present.

### Root cause
The resolver treated cache freshness as a hard requirement for lookup reuse. That makes sense for volatile data, but school postcode geography is effectively static for this use case. Once the TTL elapsed, profile hydration could block on retries to an external API instead of using already-known coordinates.

### Fix implemented
- Added `PostgresPostcodeCacheRepository.get_any(postcode)` to return cached coordinates regardless of age.
- Updated `CachedPostcodeResolver.resolve()` to use a stale-while-revalidate strategy:
  - return fresh cached data when available
  - otherwise return stale cached data when it still has an `lsoa_code`
  - call the external API only when the cache is missing or incomplete
- Added unit coverage for stale-cache reuse and repository stale reads.

### Verification
- `uv run --project apps/backend pytest apps/backend/tests/unit/test_cached_postcode_resolver.py apps/backend/tests/unit/test_postcode_cache_repository.py -q`
- `uv run --project apps/backend pytest`

---

## BUG-003 - Compare test: underfilled state not reached after school removal

**Status:** FIXED
**Severity:** Low (test-only — UI behaviour correct in browser)
**Introduced:** commit `9cd9525` (feat: add school compare flow)
**Detected:** 2026-03-08, quality-gate run following phase 7 UX overhaul commit
**Reported to:** Liam Kerrigan (colleague — authored the compare flow)
**Files:**
- `apps/web/src/features/school-compare/school-compare.test.tsx` (line 132)
- `apps/web/src/features/school-compare/SchoolCompareFeature.tsx`

### Failure

```
✗ SchoolCompareFeature > renders the compare matrix and falls back to underfilled after removing a school
→ Unable to find role="heading" and name "Add one more school to compare"
```

### Sequence

1. Test renders compare page with 2 schools (URNs `100001`, `200002`).
2. Full compare matrix loads; Demographics heading confirmed present.
3. Test clicks "Remove Primary Example from compare".
4. `handleRemoveSchool` calls `navigate(paths.compare(["200002"]))`.
5. Test expects heading "Add one more school to compare" (rendered when `effectiveUrns.length === 1`).
6. Heading not found — `effectiveUrns` still reflects 2 schools; navigation does not update URL params in the test memory router as expected.

### Root cause (hypothesis)

`effectiveUrns` is derived via `useMemo` from `urlUrns` (parsed from `location.search`). After `handleRemoveSchool` calls `navigate()`, the MemoryRouter in the test environment may not flush the URL update synchronously before the assertion. The component still reads the old 2-school URL and renders the full matrix instead of the underfilled panel.

### Resolution

Assign to Liam (owns the compare feature). Likely fix: wrap the post-click assertion in `await screen.findByRole(...)` with a longer timeout, or ensure the test's MemoryRouter initial entry and navigation are configured to flush synchronously. No production behaviour is affected — manual testing confirms the underfilled panel renders correctly in the browser.

### Verification (once fixed)

```bash
cd apps/web && npm run test -- src/features/school-compare/school-compare.test.tsx
```

---

## BUG-004 - `materialize-benchmarks` CLI does not invalidate the in-process profile cache

**Status:** FIXED
**Severity:** Low (data self-heals within 5 minutes; no incorrect data served past TTL)
**Detected:** 2026-03-10
**Assigned to:** Liam Kerrigan
**Files:**
- `apps/backend/src/civitas/application/school_trends/use_cases.py` — `MaterializeSchoolBenchmarksUseCase`
- `apps/backend/src/civitas/application/school_profiles/ports/school_profile_cache_invalidator.py`
- `apps/backend/src/civitas/infrastructure/persistence/cached_school_profile_repository.py`
- `apps/backend/src/civitas/bootstrap/container.py`
- `apps/backend/tests/unit/test_materialize_school_benchmarks_use_case.py`
- `apps/backend/tests/unit/test_cached_school_profile_repository.py`
- `apps/backend/src/civitas/infrastructure/pipelines/runner.py` — `_touch_school_profile_cache_version` (existing pattern mirrored for manual materialisation)

### Validation

Confirmed. Running `civitas pipeline materialize-benchmarks --all` rebuilds the `metric_benchmarks_yearly` table with fresh benchmark averages, but the in-process `CachedSchoolProfileRepository` (default TTL: 300 seconds) is not notified. Profile responses already held in the in-process cache continue to return the pre-rebuild benchmark values until the TTL expires naturally. This means benchmark bars on the school profile page (all sections: demographics, attendance, behaviour, workforce, results & progress) can appear stale for up to 5 minutes after a rebuild.

### Root cause

`MaterializeSchoolBenchmarksUseCase` only calls the `SchoolBenchmarkMaterializer` port — it has no reference to a cache invalidation mechanism. The pipeline runner (`PipelineRunRecorder._touch_school_profile_cache_version`) already implements the correct pattern (upsert `app_cache_versions` with `cache_key = "school_profile"`), but this is not called from the benchmark materialisation path.

### Fix implemented

- Added a `SchoolProfileCacheInvalidator` application port.
- Added `PostgresSchoolProfileCacheInvalidator`, which upserts `app_cache_versions` using the same `school_profile` cache key pattern already used after successful pipeline runs.
- Injected the invalidator into `MaterializeSchoolBenchmarksUseCase` and call it after successful full or targeted benchmark materialisation.
- Wired the invalidator through the bootstrap container for the CLI/manual rebuild path.
- Added unit coverage for successful invalidation and failure behavior, plus a repository-level test that the invalidator writes the cache token row.

### Workaround

Wait ~5 minutes for the TTL to expire, or restart the API server to clear the in-process cache immediately.

### Verification

- `uv run --project apps/backend pytest apps/backend/tests/unit/test_materialize_school_benchmarks_use_case.py apps/backend/tests/unit/test_cached_school_profile_repository.py -q`
- Isolated repro confirmed the cached profile stays stale before the fix and refreshes once the cache version token is invalidated.

---

## BUG-005 - Results & Progress section shows no sparklines or trend indicators for schools with only one year of academic data

**Status:** Open
**Severity:** Low (data gap — no incorrect data shown; section renders correctly with what is available)
**Detected:** 2026-03-10
**Assigned to:** Liam Kerrigan
**Files:**
- `apps/backend/src/civitas/infrastructure/persistence/postgres_school_profile_repository.py` — `school_performance_yearly` query (no code change needed; data fix only)
- DfE performance pipeline — needs prior-year release file ingested

### Validation

Confirmed. Querying `school_performance_yearly WHERE urn = '136655'` returns a single row (`2024/25`). The `AcademicPerformanceSection` component requires at least two history rows to compute a year-on-year delta and render the sparkline + `TrendIndicator` footer. With only one year present, `delta = null` and the footer is suppressed entirely. Verified on 2026-03-10 via direct DB query:

```
academic_year: 2024/25  attainment8_average: 44.8  progress8_average: null
```

Scope check on 2026-03-10:

- `school_performance_yearly` contains `2022/23` rows for `16,408` URNs.
- `school_performance_yearly` contains `2023/24` rows for `16,408` URNs.
- `school_performance_yearly` contains `2024/25` rows for `21,398` URNs.
- `4,990` URNs currently have only a single `2024/25` performance row.

### Root cause

The UI is behaving as designed: trend indicators only appear when there is enough history to compute a delta. The remaining issue is partial data coverage for a subset of schools, not a blanket failure to ingest the prior-year release. The current pipeline already retains up to three academic years where the source provides them. The exact reason some schools only have `2024/25` rows is still under investigation and may reflect school lineage or source-coverage gaps rather than a missing global backfill.

### Proposed fix

1. Add an explicit data-quality audit for schools with only one year of performance history.
2. Determine whether the missing history reflects genuine source coverage gaps, establishment churn, or a missing lineage model between related schools/URNs.
3. If cross-URN stitching is required, use authoritative lineage data rather than postcode/name heuristics.
4. Keep the current “no trend without two points” UI behavior; if product wants clearer UX, add explanatory copy rather than fabricating trend indicators.

### Workaround

None. The section renders correctly for available data; it simply has nothing to compare against.

### Verification (once fixed)

Confirm that `school_performance_yearly WHERE urn = '136655'` returns at least two rows, and that the Results & Progress section on `/schools/136655` shows sparklines and trend indicators for attainment/progress metrics.

---

## BUG-006 - Area deprivation absent on first profile load; appears after ~5 minutes

**Status:** FIXED
**Severity:** Medium (incorrect first impression — deprivation context silently missing until TTL expires)
**Detected:** 2026-03-10
**Assigned to:** Liam Kerrigan
**Files:**
- `apps/backend/src/civitas/application/school_profiles/use_cases.py` — `GetSchoolProfileUseCase._refresh_profile_context_if_needed`
- `apps/backend/src/civitas/infrastructure/persistence/cached_school_profile_repository.py`
- `apps/backend/src/civitas/bootstrap/container.py` — `get_school_profile_use_case`
- `apps/backend/tests/unit/test_get_school_profile_use_case.py`

### Validation

Confirmed. On a clean server start (empty `postcode_cache`), visiting a school profile page returns a profile with `area_context.coverage.has_deprivation = false`. After ~5 minutes the deprivation data appears without any user action. The 5-minute window matches the `CachedSchoolProfileRepository` TTL (300 seconds).

### Root cause

`GetSchoolProfileUseCase._refresh_profile_context_if_needed` detects missing deprivation, calls `postcode_context_resolver.resolve(postcode)` (which writes the resolved postcode with `lsoa_code` into `postcode_cache`), and then re-fetches the profile via `self._school_profile_repository`. That repository is the **cached** `CachedSchoolProfileRepository` — the re-fetch hits the in-process cache and returns the same no-deprivation result that was cached seconds earlier. The fix does not take effect until the TTL expires and the next request triggers a genuine DB read.

```python
# use_cases.py — _refresh_profile_context_if_needed (simplified)
self._postcode_context_resolver.resolve(postcode)          # populates postcode_cache ✓
refreshed = self._school_profile_repository.get_school_profile(urn)  # BUG: cache hit ✗
```

### Fix implemented

- Added an optional `refresh_school_profile_repository` dependency to `GetSchoolProfileUseCase`, typed to the existing `SchoolProfileRepository` protocol.
- Kept the primary read path on the cached repository.
- Changed `_refresh_profile_context_if_needed` to use the dedicated refresh repository for the post-resolve re-fetch when one is provided.
- Updated bootstrap wiring to inject the raw `PostgresSchoolProfileRepository` for refresh reads, while leaving the cached repository as the primary dependency.
- Added a regression test that exercises the bug with `CachedSchoolProfileRepository` in the loop so the cache interaction is covered directly.

### Workaround

Wait ~5 minutes for the TTL to expire, or restart the API server to clear the in-process cache immediately.

### Verification

- `uv run --project apps/backend pytest apps/backend/tests/unit/test_get_school_profile_use_case.py -q`
- Isolated repro confirmed the stale first response before the fix and successful first-request deprivation hydration when a dedicated refresh repository bypasses the in-process cache.

---

## Tracker Notes

- `make lint` passed on 2026-03-10 after the cache invalidation + cache bypass fixes.
- `make test` passed on 2026-03-10:
  - Backend: `373 passed, 93 skipped`
  - Web: `30 passed` test files / `215 passed` tests
- `cd apps/web && npm run lint` and `cd apps/web && npm run typecheck` both passed as part of `make lint`.
- BUG-003 is no longer a current failing test on this branch; the compare test suite passed during `make test`.
