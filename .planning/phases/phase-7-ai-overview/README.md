# Phase 7 Design Index - AI Overview And School Identity Enrichment

## Document Control

- Status: Implemented
- Last updated: 2026-03-06
- Phase owner: Product + Engineering
- Source phase: `.planning/phased-delivery.md`
- Reference: `.planning/ai-features.md`
- Legacy workstream IDs retained: `AI-1`, `AI-2`, and `AI-4`

## Purpose

This folder contains implementation-ready planning for enriching school profile data and introducing two pre-generated AI school summaries: a factual overview and an analyst view.

Phase 7 targets:

1. Widening the GIAS pipeline to extract additional school identity and contact fields.
2. AI-generated school summaries using a port-based LLM integration that follows existing hexagonal architecture.
3. Operational hardening around summary history, retry behavior, post-pipeline execution, and provider-native batch support.

## Tracking Update (2026-03-06)

- `AI-1` is implemented: `gias.v2` is live, `schools` is widened, normalization warning aggregates are persisted, and the profile API and web UI now expose the enriched GIAS fields.
- `AI-2` is implemented as a two-summary delivery: `overview` and `analyst` each have dedicated prompt/context/validation paths, shared provider transport, deterministic validation, corrective retry, run telemetry, manual CLI flows, and school-profile rendering.
- `AI-4` is implemented as hardening around the two explicit summary kinds: summary history archival, post-pipeline batch submission, explicit batch polling/finalization, provider-native async batch execution, and architecture guidance now describe a closed `overview` plus `analyst` model rather than an open generic platform.

## Verification Snapshot

- Targeted backend unit and integration slices for GIAS enrichment, overview generation, repositories, settings, profile API, CLI summary preview, pipeline AI submission, and batch polling passed during implementation.
- Web verification passed with `npm run lint`, `npm run typecheck`, and the school-profile feature test slice.
- Full repository `make lint` and `make test` remain the final closeout commands for full-repo sign-off.

## Delivery Model

Phase 7 is split into three deliverables:

1. `AI-1-gias-enrichment.md`
2. `AI-2-school-overview-summary.md`
3. `AI-4-extensible-ai-platform.md`
