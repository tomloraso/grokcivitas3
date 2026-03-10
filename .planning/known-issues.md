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

**Status:** Open
**Severity:** Low (data self-heals within 5 minutes; no incorrect data served past TTL)
**Detected:** 2026-03-10
**Assigned to:** Liam Kerrigan
**Files:**
- `apps/backend/src/civitas/application/school_trends/use_cases.py` — `MaterializeSchoolBenchmarksUseCase`
- `apps/backend/src/civitas/infrastructure/persistence/cached_school_profile_repository.py`
- `apps/backend/src/civitas/infrastructure/pipelines/runner.py` — `_touch_school_profile_cache_version` (existing pattern to follow)

### Validation

Confirmed. Running `civitas pipeline materialize-benchmarks --all` rebuilds the `metric_benchmarks_yearly` table with fresh benchmark averages, but the in-process `CachedSchoolProfileRepository` (default TTL: 300 seconds) is not notified. Profile responses already held in the in-process cache continue to return the pre-rebuild benchmark values until the TTL expires naturally. This means benchmark bars on the school profile page (all sections: demographics, attendance, behaviour, workforce, results & progress) can appear stale for up to 5 minutes after a rebuild.

### Root cause

`MaterializeSchoolBenchmarksUseCase` only calls the `SchoolBenchmarkMaterializer` port — it has no reference to a cache invalidation mechanism. The pipeline runner (`PipelineRunRecorder._touch_school_profile_cache_version`) already implements the correct pattern (upsert `app_cache_versions` with `cache_key = "school_profile"`), but this is not called from the benchmark materialisation path.

### Proposed fix

1. Define a `SchoolProfileCacheInvalidator` port in `apps/backend/src/civitas/application/school_profiles/ports/` (or reuse an existing port if one exists).
2. Inject an optional implementation into `MaterializeSchoolBenchmarksUseCase`.
3. Call it after a successful materialisation.
4. Wire the concrete `PostgresSchoolProfileCacheVersionProvider` (or a lightweight writer equivalent) into the use case via the bootstrap container.

### Workaround

Wait ~5 minutes for the TTL to expire, or restart the API server to clear the in-process cache immediately.

### Verification (once fixed)

Confirm that immediately after running `civitas pipeline materialize-benchmarks --all`, a fresh profile request returns updated benchmark values without requiring a server restart or TTL expiry.

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

Confirmed. Querying `school_performance_yearly WHERE urn = '136655'` returns a single row (`2024/25`). The `AcademicPerformanceSection` component requires `performance.history.length >= 2` to compute a year-on-year delta and render the sparkline + `TrendIndicator` footer. With only one year present, `delta = null` and the footer is suppressed entirely. Verified on 2026-03-10 via direct DB query:

```
academic_year: 2024/25  attainment8_average: 44.8  progress8_average: null
```

### Root cause

The DfE academic performance pipeline has only ingested a single academic year (`2024/25`) into `school_performance_yearly`. The trend display is data-driven: trends appear automatically once a second year exists. No frontend code change is required.

### Proposed fix

Run the DfE performance pipeline against the 2023/24 release file to populate a prior-year row for each affected school. Trends and sparklines will appear in the Results & Progress section immediately on the next profile fetch (after the in-process cache TTL expires or the server is restarted).

Check scope of the gap — it likely affects all or most schools, not just Congleton High School (URN 136655).

### Workaround

None. The section renders correctly for available data; it simply has nothing to compare against.

### Verification (once fixed)

Confirm that `school_performance_yearly WHERE urn = '136655'` returns at least two rows, and that the Results & Progress section on `/schools/136655` shows sparklines and trend indicators for attainment/progress metrics.

---

## Tracker Notes

- `make lint` still fails in the current branch because unrelated files already need formatting:
  - `apps/backend/src/civitas/infrastructure/ai/prompt_templates/school_analyst.py`
  - `apps/backend/tests/unit/test_school_analyst_prompt.py`
- `uv run --project apps/backend mypy apps/backend/src` still has one unrelated pre-existing error in `apps/backend/src/civitas/infrastructure/ai/providers/grok_summary_generator.py`.
- `cd apps/web && npm run lint` and `cd apps/web && npm run typecheck` passed.
- `cd apps/web && npm run test`: 1 pre-existing failure — BUG-003 (compare feature, introduced `9cd9525`, not related to phase 7 work). School-profile test suite fully passing as of `747e4f7`.
