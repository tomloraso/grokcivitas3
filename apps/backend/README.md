# Backend

Hexagonal Python backend service for Civitas.

## Layout

- `src/civitas/domain`: pure business logic.
- `src/civitas/application`: use-cases and ports.
- `src/civitas/infrastructure`: IO implementations.
- `src/civitas/api`: HTTP layer.
- `src/civitas/cli`: CLI layer.
- `src/civitas/bootstrap`: dependency composition.

## Commands

```bash
uv sync --project apps/backend --extra dev
uv run --project apps/backend alembic -c apps/backend/alembic.ini upgrade head
uv run --project apps/backend ruff check apps/backend
uv run --project apps/backend mypy apps/backend/src
uv run --project apps/backend pytest
uv run --project apps/backend civitas pipeline run --source gias
uv run --project apps/backend uvicorn civitas.api.main:app --reload
```

## Operations

### Benchmark cache

The `metric_benchmarks_yearly` table stores pre-computed local and national averages for every metric key. These averages are used by the school profile page to render the comparison bars (This school / Local area / England) across all sections (attendance, behaviour, workforce, performance, demographics).

**The cache must be rebuilt any time the school dataset changes** — i.e. after running pipelines that add, update, or remove school records. If the cache is stale, local averages will reflect the schools that were present when the cache was last built, which can make a school's value appear identical to its local average.

```bash
# Rebuild benchmarks for all schools (run from the repo root)
uv run --project apps/backend civitas pipeline materialize-benchmarks --all

# Rebuild for specific URNs only (faster, use after targeted updates)
uv run --project apps/backend civitas pipeline materialize-benchmarks --urn 136655 --urn 136656
```

This is a fast operation (seconds to low minutes depending on dataset size) and is safe to re-run at any time.

**Note — in-process profile cache:** The API holds an in-process school profile cache (default TTL: 300 seconds). After rebuilding benchmarks, profile responses already in cache will still return old benchmark values until the TTL expires. The pipeline runner invalidates this cache automatically, but `materialize-benchmarks` does not. To see updated benchmarks immediately after a rebuild, either wait ~5 minutes or restart the API server. This is a known gap — `MaterializeSchoolBenchmarksUseCase` should be wired to a `SchoolProfileCacheInvalidator` port.

