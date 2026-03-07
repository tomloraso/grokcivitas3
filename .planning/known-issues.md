# Known Issues

Living document. Remove an entry only after the fix is committed and verified in production.

---

## BUG-001 - School profile endpoint times out (benchmark query ignores persisted benchmark cache)

**Status:** Confirmed defect. Fixed locally and verified by automated tests. Pending commit and production verification.
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

**Status:** Confirmed defect. Fixed locally and verified by automated tests. Pending commit and production verification.
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

## Tracker Notes

- `make lint` still fails in the current branch because unrelated files already need formatting:
  - `apps/backend/src/civitas/infrastructure/ai/prompt_templates/school_analyst.py`
  - `apps/backend/tests/unit/test_school_analyst_prompt.py`
- `uv run --project apps/backend mypy apps/backend/src` still has one unrelated pre-existing error in `apps/backend/src/civitas/infrastructure/ai/providers/grok_summary_generator.py`.
- `cd apps/web && npm run lint` and `cd apps/web && npm run typecheck` passed.
- `cd apps/web && npm run test` still has unrelated pre-existing failures in `apps/web/src/features/school-profile/school-profile.test.tsx`.
