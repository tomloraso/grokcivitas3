# Phase Source Stabilization Design Index - Source Strategy Stabilization + Trend History Recovery

## Document Control

- Status: Complete (S1-S6 complete)
- Last updated: 2026-03-04
- Phase owner: Product + Engineering
- Source phase: `.planning/phased-delivery.md`

## Purpose

This folder contains implementation-ready planning for a blocking stabilization phase that resolves source-strategy issues affecting trend reliability and completeness messaging.

The phase addresses two concrete problems:

1. Historical trends are sparse because current demographics ingestion is effectively single-year.
2. Completeness messaging can expose implementation phrasing instead of source-aware, parent-facing explanations.

## Engineering guardrails

1. Do not add backwards-compatibility shims for the old single-dataset path.
2. Do not dual-run old and new demographics ingestion logic beyond short validation windows explicitly documented in sign-off.
3. Do not add adapter indirection unless required by a concrete source contract difference covered in tests.
4. Prefer replacement + deletion over parallel codepaths.

## Why this phase exists

As of 2026-03-04, the currently configured DfE dataset path provides one academic year (`2024/25`) for the active school-level characteristics feed. This prevents robust year-over-year trend behavior for many schools.

This phase introduces a multi-source strategy based on verified school-level release files and formalizes quality gates so progression can resume safely.

## Architecture View

```mermaid
flowchart LR
  subgraph Sources[External Sources]
    EESSPC[SPC school-level underlying files]
    EESSEN[SEN school-level underlying files]
  end

  subgraph Pipeline[Pipeline Runtime]
    DISC[Release discovery + file selection]
    BRONZE[Bronze raw files + manifests]
    STAGE[Normalized staging rows]
    MERGE[SPC + SEN merge by URN + academic year]
    GOLD[school_demographics_yearly]
  end

  subgraph Serving[Serving Layer]
    API[Profile + Trends API]
    UI[School profile trend UX]
    COMP[Completeness reason codes]
  end

  EESSPC --> DISC --> BRONZE --> STAGE --> MERGE --> GOLD
  EESSEN --> DISC
  GOLD --> API --> UI
  GOLD --> COMP --> API
```

## Delivery Model

Phase Source Stabilization is split into six deliverables:

1. `S1-source-contract-and-catalog-freeze.md`
2. `S2-release-file-discovery-and-bronze-ingest.md`
3. `S3-multi-source-normalization-and-gold-upsert.md`
4. `S4-completeness-contract-and-parent-facing-copy.md`
5. `S5-quality-gates-and-signoff.md`
6. `S6-school-level-ethnicity-breakdown-support.md`

## Execution Sequence

1. Complete `S1` first to freeze approved source families and schema requirements.
2. Complete `S2` to make source discovery and Bronze ingest deterministic.
3. Complete `S3` to normalize, merge, and promote multi-year demographics.
4. Complete `S4` to align API/UI completeness semantics and user messaging.
5. Complete `S5` as hard gate sign-off.
6. Complete `S6` to close school-level ethnicity coverage using existing SPC source files.

## Definition of Done

- Multi-year demographics history is sourced from approved, tested files.
- Open-school trend depth reaches target thresholds for primary and secondary.
- Completeness reason codes are source-aware and parent-readable.
- School-level ethnicity breakdown is supported from approved SPC school-level files.
- All implemented gates pass in one repository state (`make lint`, `make test` included).

## Change Management

- `.planning/phased-delivery.md` remains the high-level source of truth.
- Any source/catalog decision change must update `S1` and `S2` in the same PR.
- Any API/UI completeness behavior change must update `S4` in the same PR.
- Any school-level ethnicity coverage behavior change must update `S6` in the same PR.

## Decisions Captured

- 2026-03-04: progression to expansion phases is blocked until this phase is signed off.
- 2026-03-04: multi-year demographics recovery requires source-strategy change, not UI-only mitigations.
- 2026-03-04: phase implementation completed with gate evidence captured in `signoff-2026-03-04.md`.
- 2026-03-04: direct FSM percentage support is enabled from SPC release files; unsupported flag now reflects source-family availability rather than a hardcoded false.
- 2026-03-04: S6 plan added to implement school-level ethnicity breakdown using existing SPC school-level files.
- 2026-03-04: S6 implementation completed; profile contracts now expose school-level ethnicity breakdown where SPC source data is available.
