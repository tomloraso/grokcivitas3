# Phase H7 Design - Hardening Quality Gates And Sign-Off

## Document Control

- Status: Proposed
- Last updated: 2026-03-03
- Depends on:
  - `.planning/phases/phase-hardening/H1-pipeline-run-policy-quality-gates.md`
  - `.planning/phases/phase-hardening/H2-source-normalization-contracts.md`
  - `.planning/phases/phase-hardening/H3-historical-demographics-backfill-lookback.md`
  - `.planning/phases/phase-hardening/H4-data-completeness-contract-api-ui.md`
  - `.planning/phases/phase-hardening/H5-operational-observability-freshness-coverage-drift.md`
  - `.planning/phases/phase-hardening/H6-pipeline-resilience-performance-hardening.md`
  - `.agents/tooling.md`
  - `.agents/testing.md`

## Objective

Define mandatory quality gates and sign-off criteria so hardening is closed only when data correctness, completeness transparency, observability, and resilience requirements all pass in one consistent repository state.

## Quality Gates (Mandatory)

## Gate 0 - Run Policy And Contract Guardrails

- Validate hard-failure semantics and normalization contracts from `H1` and `H2`.

Required commands:

- `uv run --project apps/backend pytest apps/backend/tests/unit/test_pipeline_runner.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/unit/test_pipeline_cli.py -q`
- `uv run --project apps/backend python tools/scripts/verify_source_contracts_runtime.py`

## Gate 1 - Historical Backfill And Trend Depth

- Validate `H3` lookback controls and historical trend population behavior.

Required commands:

- `uv run --project apps/backend pytest apps/backend/tests/integration/test_dfe_characteristics_pipeline.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/integration/test_school_trends_repository.py -q`
- `uv run --project apps/backend civitas pipeline backfill --source dfe_characteristics --lookback-years 5 --dry-run`

## Gate 2 - Completeness Contract Across API And UI

- Validate `H4` section-level completeness metadata and user-facing behavior.

Required commands:

1. `uv run --project apps/backend python tools/scripts/export_openapi.py`
2. `cd apps/web && npm run generate:types`
3. `uv run --project apps/backend pytest apps/backend/tests/integration/test_school_profile_api.py apps/backend/tests/integration/test_school_trends_api.py -q`
4. `cd apps/web && npm run test -- school-profile`
5. `cd apps/web && npm run lint`
6. `cd apps/web && npm run typecheck`

## Gate 3 - Freshness And Coverage Observability

- Validate `H5` snapshot, drift, and alert evaluation behavior.

Required commands:

- `uv run --project apps/backend pytest apps/backend/tests/unit/test_data_quality_use_cases.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/integration/test_data_quality_repository.py -q`
- `uv run --project apps/backend python tools/scripts/check_data_quality_slo.py --strict`

## Gate 4 - Resilience, Recovery, And Performance

- Validate `H6` retry, checkpoint resume, and throughput hardening.

Required commands:

- `uv run --project apps/backend pytest apps/backend/tests/unit/test_pipeline_retry_policy.py -q`
- `uv run --project apps/backend pytest apps/backend/tests/integration/test_pipeline_resume.py -q`
- `uv run --project apps/backend python tools/scripts/run_pipeline_recovery_drill.py --strict`
- `uv run --project apps/backend python tools/scripts/benchmark_pipeline_throughput.py --strict`

## Gate 5 - Repository Golden Path

Final repository-wide checks from repo root:

- `make lint`
- `make test`

## Acceptance Checklist

1. Pipeline runs cannot silently succeed when stage/promote outputs violate quality policy.
2. Normalization behavior is contract-driven and versioned for all active feeds.
3. Historical demographics support configurable lookback with auditable provenance.
4. Profile and trends contracts expose explicit, user-friendly completeness metadata.
5. Freshness and coverage drift are monitored with actionable alerting.
6. Recovery and performance drills prove resumability and stable throughput.
7. All mandatory gates pass in a single consistent repository state.

## Exit Criteria

Hardening phase is complete only when all gates pass and the original RCA concerns are closed with evidence:

- missing core school data is either populated or explicitly reason-coded as source-unavailable,
- trend history behavior is explained by measured source coverage rather than silent pipeline loss,
- sparse profile pages remain understandable and trustworthy to end users.

## Sign-Off Artifact

At closeout, add:

- `.planning/phases/phase-hardening/signoff-YYYY-MM-DD.md`

The sign-off artifact must include:

1. command execution evidence for every gate,
2. snapshot metrics for freshness and coverage,
3. unresolved risks and approved follow-up actions.

## Risks And Mitigations

- Risk: partial gate execution gives false confidence.
  - Mitigation: explicit command list and mandatory single-state pass requirement.
- Risk: hardening changes drift from planning intent.
  - Mitigation: sign-off artifact includes mapping from each RCA concern to implemented evidence.
