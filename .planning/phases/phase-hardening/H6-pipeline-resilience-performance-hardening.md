# Phase H6 Design - Pipeline Resilience, Performance, And Recovery Hardening

## Document Control

- Status: Proposed
- Last updated: 2026-03-03
- Depends on:
  - `.planning/phases/phase-hardening/H1-pipeline-run-policy-quality-gates.md`
  - `.planning/phases/phase-hardening/H2-source-normalization-contracts.md`
  - `.planning/phases/phase-hardening/H5-operational-observability-freshness-coverage-drift.md`
  - `.planning/phases/phase-0/0A-data-platform-baseline.md`
  - `docs/architecture/backend-conventions.md`

## Objective

Harden ingestion pipelines for production operation under large files, transient source failures, and partial-run interruptions while preserving deterministic, idempotent outcomes.

## Scope

### In scope

- Retry/backoff policy for transient transport failures.
- Checkpointing and resume support across download, stage, and promote boundaries.
- Chunked staging/promote writes to control memory and transaction size.
- Concurrency controls and source-level lock protection.
- Recovery drills and throughput benchmarking with defined SLO targets.

### Out of scope

- Distributed workflow engine migration.
- Net-new data source onboarding.

## Resilience Policy

1. Retries are limited, jittered, and reason-coded.
2. Each run persists step checkpoints that can safely resume.
3. Promote remains idempotent via stable conflict keys and deterministic transforms.
4. A source lock prevents overlapping writes for the same source.
5. Failures produce actionable checkpoint state, not ambiguous partial success.

## Performance Targets

- Pipelines must process large monthly source files without memory spikes from full-file in-memory loads.
- Throughput baseline and runtime ceilings must be measured and tracked per source.
- Resume mode must recover failed runs without restarting from raw download when artifacts are already available.

## File-Oriented Implementation Plan

1. `apps/backend/src/civitas/infrastructure/config/settings.py`
   - add pipeline hardening controls:
     - `CIVITAS_PIPELINE_HTTP_TIMEOUT_SECONDS`
     - `CIVITAS_PIPELINE_MAX_RETRIES`
     - `CIVITAS_PIPELINE_RETRY_BACKOFF_SECONDS`
     - `CIVITAS_PIPELINE_STAGE_CHUNK_SIZE`
     - `CIVITAS_PIPELINE_PROMOTE_CHUNK_SIZE`
     - `CIVITAS_PIPELINE_MAX_CONCURRENT_SOURCES`
     - `CIVITAS_PIPELINE_RESUME_ENABLED`
2. `apps/backend/alembic/versions/*_hardening_pipeline_checkpoints.py` (new)
   - add `pipeline_checkpoints` table keyed by `run_id + source + step`.
3. `apps/backend/src/civitas/infrastructure/pipelines/base.py`
   - define checkpoint/retry policy models and source lock contract.
4. `apps/backend/src/civitas/infrastructure/pipelines/runner.py`
   - add resilient retry wrapper, source lock acquisition, and checkpoint persistence.
5. `apps/backend/src/civitas/infrastructure/persistence/postgres_pipeline_checkpoint_repository.py` (new)
   - implement checkpoint read/write and resume recovery.
6. `apps/backend/src/civitas/infrastructure/pipelines/*.py`
   - refactor source pipelines to stream/chunk stage writes and promote operations.
7. `apps/backend/src/civitas/cli/main.py`
   - add commands:
     - `civitas pipeline run --source <source> --resume`
     - `civitas pipeline resume --run-id <id>`
8. `tools/scripts/benchmark_pipeline_throughput.py` (new)
   - benchmark source runtime and rows/second against configured thresholds.
9. `tools/scripts/run_pipeline_recovery_drill.py` (new)
   - simulate controlled interruption and verify successful resume.
10. `apps/backend/tests/unit/test_pipeline_retry_policy.py` (new)
    - unit tests for retry/backoff and retry classification.
11. `apps/backend/tests/integration/test_pipeline_resume.py` (new)
    - integration tests for checkpoint resume behavior.

## Testing And Quality Gates

### Required tests

- transient download failure retries and then succeeds within configured retry budget.
- non-retryable failures fail fast without retry loops.
- interrupted runs resume from latest safe checkpoint.
- chunked stage/promote paths remain idempotent across reruns.

### Required gates

- `uv run --project apps/backend pytest apps/backend/tests/unit/test_pipeline_retry_policy.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/integration/test_pipeline_resume.py -q`
- `uv run --project apps/backend python tools/scripts/run_pipeline_recovery_drill.py --strict`
- `uv run --project apps/backend python tools/scripts/benchmark_pipeline_throughput.py --strict`
- `make lint`
- `make test`

## Acceptance Criteria

1. Pipeline failures are recoverable with deterministic resume behavior.
2. Large ingests operate within bounded memory and transaction sizes.
3. Retry behavior improves resilience without masking persistent data-quality failures.
4. Throughput and recovery expectations are codified and testable.

## Implementation Notes

- Stage writes and rejection logging are chunked by configured batch size to bound statement payload size.
- Promote paths remain set-based SQL upserts from staging tables; additional row-chunk loops are intentionally not added where set-based statements already avoid Python-side buffering.

## Risks And Mitigations

- Risk: checkpoint logic introduces subtle duplicate writes.
  - Mitigation: idempotent conflict keys plus resume integration tests.
- Risk: aggressive retries increase source pressure.
  - Mitigation: bounded retries with backoff, jitter, and source-level concurrency limits.
