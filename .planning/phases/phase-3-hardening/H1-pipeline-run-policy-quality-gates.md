# Phase 3 / H1 Design - Pipeline Run Policy And Quality Gates

## Document Control

- Status: Proposed
- Last updated: 2026-03-03
- Depends on:
 - `.planning/phases/phase-3-hardening/README.md`
  - `.planning/phases/phase-0/0A-data-platform-baseline.md`
  - `apps/backend/src/civitas/infrastructure/pipelines/base.py`
  - `apps/backend/src/civitas/infrastructure/pipelines/runner.py`
  - `docs/architecture/backend-conventions.md`

## Objective

Replace permissive pipeline success semantics with deterministic quality-gated outcomes so invalid or empty staged results cannot silently pass.

## Scope

### In scope

- Define run outcome policy for `downloaded_rows`, `staged_rows`, `promoted_rows`, and rejection ratios.
- Enforce policy in runner before final status writeback.
- Introduce explicit run statuses for no-op and quality-gate failure.
- Add source-level configurable rejection thresholds.

### Out of scope

- Source-specific normalization rules (owned by `H2`).
- New metrics UI and alerts (owned by `H5`).

## Run Outcome Policy

1. `downloaded_rows == 0`:
   - status: `failed_source_unavailable`.
2. `downloaded_rows > 0` and `staged_rows == 0`:
   - status: `failed_quality_gate`.
3. `staged_rows > 0` and `promoted_rows == 0`:
   - status: `failed_quality_gate`.
4. `rejected_rows / downloaded_rows > max_reject_ratio`:
   - status: `failed_quality_gate`.
5. checksum unchanged from prior successful run and no new promoted records:
   - status: `skipped_no_change`.
6. all gates satisfied:
   - status: `succeeded`.

## Decisions

1. Quality-gate failures are hard failures, not warnings.
2. "No change" is explicit and non-fatal.
3. Gate thresholds are source-specific and config-driven.
4. Error messages must include failing gate id and measured values.
5. H1 only introduces `max_reject_ratio`; additional threshold types are deferred until justified.

## File-Oriented Implementation Plan

1. `apps/backend/src/civitas/infrastructure/pipelines/base.py`
   - extend `PipelineRunStatus` with `failed_quality_gate`, `failed_source_unavailable`, `skipped_no_change`.
   - add `PipelineQualityConfig` and gate result dataclasses.
2. `apps/backend/src/civitas/infrastructure/config/settings.py`
   - add per-source reject-ratio thresholds:
     - `CIVITAS_PIPELINE_MAX_REJECT_RATIO_{SOURCE}`
3. `apps/backend/src/civitas/infrastructure/pipelines/runner.py`
   - evaluate gates after `download`, `stage`, `promote`.
   - set explicit failure reason text with measured counters.
   - emit `skipped_no_change` when Bronze checksum(s) match the prior successful run.
4. `apps/backend/src/civitas/cli/main.py`
   - print gate outcome details and return non-zero for hard failures.
5. `apps/backend/tests/unit/test_pipeline_runner.py`
   - add gate-policy matrix tests.
6. `apps/backend/tests/unit/test_pipeline_cli.py`
   - add CLI output and exit-code coverage for new statuses.

## Testing And Quality Gates

### Required tests

- source unavailable path fails with `failed_source_unavailable`.
- stage-zero path fails with `failed_quality_gate`.
- promote-zero path fails with `failed_quality_gate`.
- reject-ratio breach fails with `failed_quality_gate`.
- unchanged checksum path returns `skipped_no_change`.

### Required gates

- `uv run --project apps/backend pytest apps/backend/tests/unit/test_pipeline_runner.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/unit/test_pipeline_cli.py -q`
- `make lint`
- `make test`

## Acceptance Criteria

1. A run with `downloaded_rows > 0` and `staged_rows == 0` cannot finish as `succeeded`.
2. A run with `staged_rows > 0` and `promoted_rows == 0` cannot finish as `succeeded`.
3. Rejection spikes are configurable and enforceable by source.
4. CLI and `pipeline_runs.status` reflect deterministic policy outcomes.

## Risks And Mitigations

- Risk: overly strict thresholds block valid runs during source changes.
  - Mitigation: source-level threshold config and staged rollout.
- Risk: status proliferation makes operations harder to interpret.
  - Mitigation: map statuses to clear runbook actions in `H5`.
