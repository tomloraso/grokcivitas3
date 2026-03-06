# AI Extension Guide

This guide documents the current AI implementation for school summaries.

## Current shape

The backend AI stack is intentionally narrow:

- `SchoolOverviewContext` in `apps/backend/src/civitas/domain/school_summaries/models.py`
- `SchoolAnalystContext` in `apps/backend/src/civitas/domain/school_summaries/models.py`
- `GenerateSchoolOverviewsUseCase`, `GenerateSchoolAnalystSummariesUseCase`, and the matching submit/poll batch use cases in `apps/backend/src/civitas/application/school_summaries/use_cases.py`
- `SummaryContextRepository` for Gold-table context assembly
- `SummaryGenerator` for provider-backed generation, with optional `AsyncBatchSummaryGenerator` capability
- `validate_generated_summary` and `validate_analyst_summary` for deterministic validation
- `PostgresSummaryRepository` for persisted summary text, history, and run telemetry keyed by `summary_kind`

The important constraint is that application code knows about two explicit product concepts, `overview` and `analyst`. It does not know about HTTP payloads, provider-specific APIs, or SQL joins.

## Design stance

Civitas does not preserve a fully generic multi-summary platform internally.

It supports a closed set of two explicit summary kinds, `overview` and `analyst`, each with its own prompt, context shape, and validation policy. If a future feature genuinely needs a third persisted AI artifact, design it as a new product decision first, then extend the architecture deliberately. Do not pre-generalise the current two-summary flow.

Provider-native execution capabilities are allowed at the infrastructure boundary when they reduce cost or improve throughput. Today that means both summary kinds can use a provider batch API when the selected provider exposes one, while the application layer still asks only for `overview` or `analyst` generation.

## Validation rules

Every stored LLM output must pass deterministic validation before persistence.

- Validation is intentionally high-precision rather than aggressive: it is designed to catch obvious problems, not to second-guess normal grounded phrasing.
- Broad word-count sanity bounds are enforced.
- Recommendation and suitability phrasing is rejected.
- Explicit unsupported claims are rejected when the text asserts unpublished Ofsted, Progress 8, or Attainment 8 data as if it were present.
- A single corrective retry is allowed using machine-readable reason codes.
- Failed items are quarantined through `ai_generation_run_items`; they are not served from `school_ai_summaries`.

## Storage model

Persistent outputs use:

- `school_ai_summaries` for current served text
- `school_ai_summary_history` for archived previous versions
- `ai_generation_runs` for per-run status keyed by `summary_kind`
- `ai_generation_run_items` for per-URN execution and retries

## Batch execution

Bulk summary generation may use provider-native batch execution, but the application layer treats it as a submit-and-finalize workflow rather than a blocking request.

- The application layer orchestrates two product concepts only: `overview` and `analyst`.
- `SubmitSchoolOverviewBatchesUseCase` and `SubmitSchoolAnalystBatchesUseCase` create provider batches and record `submitted_batch` run items with provider metadata.
- Matching poll use cases validate completed results, persist successes, and only fall back to individual requests for missing or failed batch items.
- Deterministic validation, corrective retry, persistence, and run telemetry stay unchanged after results are received.
- The synchronous generate use cases remain the fallback path for non-batch providers and targeted retries.

## Operational model

- `civitas generate-summaries` submits `overview`, `analyst`, or both and exits; it does not wait for xAI batch completion.
- `civitas poll-summary-batches` performs a single poll/finalize pass and exits.
- `pipeline run --all` may submit both summary kinds after successful promote when AI is enabled, but operators or scheduled automation must invoke the poll command separately.
- This matches xAI Batch API semantics: batch jobs are asynchronous, results may be collected while a batch is running, and completion is typically expected within a 24-hour window rather than in-process request time.
