# AI Features

## Document Control

- Status: Current implemented baseline
- Last updated: 2026-03-07
- Related phase: `Phase 8 - AI overview + school identity enrichment`

## Current AI Scope

Civitas currently supports one AI feature:

- one pre-generated, factual school overview shown on school profile pages

This is intentionally narrow. Civitas does not currently expose a chat surface, multi-artifact generation, or request-time LLM inference to end users.

## School Overview Rules

- Summary length targets roughly 120 to 180 words.
- Content stays factual, neutral, and source-backed.
- Summary may cover school type, age range, size, location context, pupil indicators, performance signals, and inspection signals where available.
- Summary must not provide advice, rankings, suitability judgments, or subjective recommendations.

## Generation Model

- Summaries are pre-generated and stored, never generated during profile requests.
- Generation typically runs after successful data refresh or via manual operational trigger.
- Each stored summary records provenance fields such as `model_id`, `prompt_version`, `generated_at`, and `data_version_hash`.
- Deterministic validation is required before persistence.
- Previous versions are archived in summary history storage.

## Product Guardrails

- Only one AI artifact is in scope today.
- The AI layer augments source data; it does not replace raw tables, charts, or official inspection information.
- The disclaimer shown to users must remain prominent and explicit.

## Current Implementation Notes

- LLM access is hidden behind backend ports and infrastructure adapters.
- Batch-capable providers may be used for operational efficiency, but the product surface still models one overview artifact.
- Summary generation is a post-pipeline concern and should not block profile reads.

## Deferred Decisions

1. Whether the overview remains free or becomes part of premium access later.
2. Whether any second AI artifact is justified by a concrete user need after MVP.
3. Whether future report-export work should reuse the same summary pipeline or remain fully separate.
