# Phase 8 / AI-4 Design - Summary Platform Hardening

## Document Control

- Status: Implemented
- Last updated: 2026-03-06
- Depends on:
  - `.planning/phases/phase-8-ai-overview/AI-2-school-overview-summary.md`
  - `docs/architecture/backend-conventions.md`

## Objective

Harden the explicit two-summary AI path with summary history, post-pipeline execution, provider-native batch execution, and implementation guidance without preserving a generic open-ended multi-summary platform.

## Tracking Update (2026-03-06)

- `school_ai_summary_history` archives replaced rows for both `overview` and `analyst`.
- `pipeline run --all` submits both summary kinds after successful promote when AI is enabled, without blocking on provider batch completion.
- The architecture guide now documents an explicit `overview` plus `analyst` path and explicitly avoids generic multi-summary abstractions until product needs justify them.
- Provider-native async batch execution is wired through submit/poll adapter flows while preserving summary-kind-aware application semantics.

## Scope

- Summary history archival.
- Summary generation run telemetry keyed by `summary_kind`.
- Post-pipeline AI submission plus explicit batch polling/finalization.
- Provider-native batch execution for bulk overview and analyst generation.
- Closed two-summary architecture guidance.

## Non-Goals

- Additional AI summary types beyond `overview` and `analyst`.
- Premium AI product design.
