# Phase 7 Design Index - AI Overview And School Identity Enrichment

## Document Control

- Status: Implemented
- Last updated: 2026-03-06
- Phase owner: Product + Engineering
- Source phase: `.planning/phased-delivery.md`
- Reference: `.planning/ai-features.md`
- Legacy workstream IDs retained: `AI-1`, `AI-2`, and `AI-4`

## Purpose

This folder contains implementation-ready planning for enriching school profile data and introducing one pre-generated AI school overview.

Phase 7 targets:

1. Widening the GIAS pipeline to extract additional school identity and contact fields.
2. AI-generated factual school overviews using a port-based LLM integration that follows existing hexagonal architecture.
3. Operational hardening around summary history, retry behavior, post-pipeline execution, and provider-native batch support.

## Tracking Update (2026-03-06)

- `AI-1` is implemented: `gias.v2` is live, `schools` is widened, normalization warning aggregates are persisted, and the profile API and web UI now expose the enriched GIAS fields.
- `AI-2` is implemented: overview generation, deterministic validation, corrective retry, run telemetry, provider abstraction, manual CLI flows, and school-profile rendering are all wired end to end.
- `AI-4` is implemented as overview-only hardening: summary history archival, post-pipeline generation, provider-native batch execution, and architecture guidance now describe a single stored overview rather than a multi-summary platform.

## Verification Snapshot

- Targeted backend unit and integration slices for GIAS enrichment, overview generation, repositories, settings, profile API, CLI summary preview, and pipeline AI triggering passed during implementation.
- Web verification passed with `npm run lint`, `npm run typecheck`, and the school-profile feature test slice.
- Full repository `make lint` and `make test` remain the final closeout commands for full-repo sign-off.

## Delivery Model

Phase 7 is split into three deliverables:

1. `AI-1-gias-enrichment.md`
2. `AI-2-school-overview-summary.md`
3. `AI-4-extensible-ai-platform.md`
