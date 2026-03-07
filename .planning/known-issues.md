# Known Issues

Living document. Remove an entry when the fix is committed and verified in production.

---

## BUG-001 — School profile endpoint times out (benchmark query full-table scan)

**Status:** Fix implemented locally, not yet committed
**Severity:** Critical
**File:** `apps/backend/src/civitas/infrastructure/persistence/postgres_school_trends_repository.py`
**Function:** `get_metric_benchmark_series`

### Root cause
The function builds a `school_geo` CTE that scans **all 50,531 schools** on every request, doing a LATERAL join against `postcode_cache` using the unindexed expression `replace(upper(postcode), ' ', '')`. With PostgreSQL's default `work_mem = 4MB`, sort/hash operations spill to disk (`BufFileRead` wait event), causing 8–21 minute query runtimes. Multiple concurrent requests exhaust the connection pool (`QueuePool limit of size 5 overflow 10`).

The `metric_benchmarks_yearly` table already holds 318 pre-computed benchmark rows that go unused on every subsequent request — the full computation runs unconditionally.

### Fix
Cache-first path: query `metric_benchmarks_yearly` for the target school only. Fall back to the full computation only on cache miss, prefixed with `SET LOCAL work_mem = '64MB'` to prevent disk spill.

```python
benchmark_rows = _get_metric_benchmark_rows_from_cache(connection, urn)
if not benchmark_rows:
    connection.execute(text("SET LOCAL work_mem = '64MB'"))
    benchmark_rows = _compute_metric_benchmark_rows(connection, urn)
    _persist_metric_benchmark_rows(connection, [dict(row) for row in benchmark_rows])
```

The fast-path query scopes to a single school (`WHERE schools.urn = :urn`) and joins against the pre-computed cache. Verified at ~88ms in psql.

---

## BUG-002 — Postcode resolver blocks on external HTTP for up to 30 seconds per request

**Status:** Fix implemented locally, not yet committed
**Severity:** High
**Linked to:** BUG-001 (pool exhaustion caused postcode cache to go stale, triggering this path)
**Files:**
- `apps/backend/src/civitas/infrastructure/http/postcode_resolver.py`
- `apps/backend/src/civitas/infrastructure/persistence/postgres_postcode_cache_repository.py`

### Root cause
`CachedPostcodeResolver.resolve()` falls through to `PostcodesIoClient.lookup()` when the 30-day cache TTL expires. The HTTP client is configured with `timeout=10s`, `max_retries=2`, `backoff=0.5s` — worst case ~31.5 seconds of blocking per request. This runs on every profile load where `has_deprivation = False`. School postcodes essentially never change, so hitting a live API on TTL expiry is unnecessary.

### Fix
Stale-while-revalidate: check for any cached entry (regardless of age) before making the HTTP call. Only call the live API for postcodes completely absent from the cache.

Add `get_any(postcode)` to `PostgresPostcodeCacheRepository` — same as `get_fresh` but without the `AND cached_at >= :fresh_after` filter.

Update `CachedPostcodeResolver.resolve()`:

```python
def resolve(self, postcode: str) -> PostcodeCoordinates:
    cached = self._cache_repository.get_fresh(postcode=postcode, ttl=self._cache_ttl)
    if cached is not None and cached.lsoa_code is not None:
        return cached

    # Stale-while-revalidate: return stale data to avoid blocking on external HTTP.
    stale = self._cache_repository.get_any(postcode=postcode)
    if stale is not None and stale.lsoa_code is not None:
        return stale

    resolved = self._postcodes_io_client.lookup(postcode)
    self._cache_repository.upsert(coordinates=resolved)
    return resolved
```
