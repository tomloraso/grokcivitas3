# Phase 7 / AI-2 Design - AI-Generated School Overview Summary

## Document Control

- Status: Implemented
- Last updated: 2026-03-06
- Depends on:
  - `.planning/phases/phase-7-ai-overview/AI-1-gias-enrichment.md`
  - `.planning/ai-features.md`
  - `docs/architecture/backend-conventions.md`

## Tracking Update (2026-03-06)

- Implemented as an overview-only path using `GetSchoolOverviewUseCase` and `GenerateSchoolOverviewsUseCase`.
- Context assembly stays behind `SummaryContextRepository`; application use cases never query Gold tables directly.
- Deterministic validation is mandatory before persistence: word-count bounds, banned phrasing, missing-reference checks, non-context entity detection, and one corrective retry.
- `school_ai_summaries`, `ai_generation_runs`, and `ai_generation_run_items` are implemented, and overview text is surfaced on the school profile API/UI only when a validated summary exists.
- AI generation is integrated into both manual CLI flows and `pipeline run --all` post-pipeline execution when `CIVITAS_AI_ENABLED=true`.

## Objective

Introduce a pre-generated, factual school overview (120-180 words) for every school, using a port-based LLM integration that follows the existing hexagonal architecture.

## Design Decisions

1. Pre-generated, not live.
2. One AI artifact only: `overview`.
3. Provider selection stays configurable, but the product contract stays neutral.
4. Validation before persistence is mandatory.
5. A single corrective retry is allowed after validation failure.
6. Previous overview versions are archived in `school_ai_summary_history`.

## Stored Shape

Current summary table:

```sql
CREATE TABLE school_ai_summaries (
    urn text PRIMARY KEY,
    text text NOT NULL,
    data_version_hash text NOT NULL,
    prompt_version text NOT NULL,
    model_id text NOT NULL,
    generated_at timestamptz NOT NULL,
    generation_duration_ms integer NULL
);
```

Run telemetry:

```sql
CREATE TABLE ai_generation_runs (
    id uuid PRIMARY KEY,
    trigger text NOT NULL,
    requested_count integer NOT NULL,
    succeeded_count integer NOT NULL DEFAULT 0,
    generation_failed_count integer NOT NULL DEFAULT 0,
    validation_failed_count integer NOT NULL DEFAULT 0,
    started_at timestamptz NOT NULL,
    completed_at timestamptz NULL,
    status text NOT NULL
);

CREATE TABLE ai_generation_run_items (
    run_id uuid NOT NULL REFERENCES ai_generation_runs(id) ON DELETE CASCADE,
    urn text NOT NULL,
    status text NOT NULL,
    attempt_count integer NOT NULL DEFAULT 0,
    failure_reason_codes text[] NULL,
    completed_at timestamptz NULL,
    PRIMARY KEY (run_id, urn)
);
```
