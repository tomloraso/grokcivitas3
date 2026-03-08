# Documentation Guide

## docs/ vs .agents/

- `docs/`: system documentation and architecture references.
- `.agents/`: agent execution and contribution guidance.

## Update checklist

1. Update affected `docs/` pages.
2. Add new pages to `docs/index.md`.
3. Update architecture diagrams and decision records when boundaries change.
4. For ingestion/data-shape changes, update `docs/runbooks/pipelines.md` and keep Bronze -> Silver -> Gold guidance current.
5. For benchmark cache workflow changes, document when `metric_benchmarks_yearly` is rebuilt,
   keep the request path read-only, and update `.agents/pipelines.md` alongside
   `docs/runbooks/pipelines.md`.

## Required pages

- `docs/architecture.md`
- `docs/architecture/principles.md`
- `docs/architecture/boundaries.md`
- `docs/architecture/backend-conventions.md`
- `docs/architecture/frontend-conventions.md`
- `docs/architecture/testing-strategy.md`
- `docs/runbooks/pipelines.md`
