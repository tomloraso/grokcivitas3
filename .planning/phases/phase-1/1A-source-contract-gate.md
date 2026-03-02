# Phase 1A Design - Source Contract Gate (Non-Negotiable)

## Document Control

- Status: Draft
- Last updated: 2026-03-02
- Depends on:
  - `.planning/phases/phase-1/README.md`
  - `.planning/project-brief.md`
  - `.planning/data-architecture.md`
  - `docs/architecture.md`

## Objective

Enforce a hard pre-implementation gate so every Phase 1 source-dependent deliverable is grounded in real, callable endpoints with verified field coverage.

No implementation work for `1B` or `1C` may start until this gate passes.

## Scope

### In scope

- Define mandatory source verification checks.
- Lock endpoint contracts (method, URL pattern, required fields, fallback).
- Record verification snapshots with concrete dates and sample evidence.
- Define policy for unsupported required metrics (coverage gaps).

### Out of scope

- Pipeline transformation implementation details (owned by `1B` and `1C`).
- API and web implementation details (owned by `1D` to `1G`).

## Gate Rules (Blocking)

1. Every source-dependent design doc must include:
   - exact endpoint URL pattern(s),
   - HTTP method,
   - expected success status code,
   - required source fields,
   - verification date and evidence.
2. Every source must define a fallback path:
   - alternate callable endpoint, or
   - explicit environment override for manual source URL/file.
3. Every required Phase 1 metric must map to a verified source field or be explicitly marked unavailable.
4. Missing fields must not be fabricated or inferred from unrelated metrics.
5. Trend deliverables must include a minimum-history verification step before enabling trend deltas.

## Phase 1 Source Contract Matrix

### DfE demographics source family

- Base API: `https://api.education.gov.uk/statistics/v1`
- Required callable endpoints:
  - `GET /publications?page=1&pageSize=20`
  - `GET /publications/{publicationId}/data-sets?page=1&pageSize=20`
  - `GET /data-sets/{dataSetId}`
  - `GET /data-sets/{dataSetId}/meta`
  - `GET /data-sets/{dataSetId}/query?page=1&pageSize=1`
  - `GET /data-sets/{dataSetId}/csv`
- Current validated school-level dataset candidate (2026-03-02):
  - `dataSetId=019afee4-ba17-73cb-85e0-f88c101bb734`

### Ofsted latest source family

- Landing page:
  - `GET https://www.gov.uk/government/statistical-data-sets/monthly-management-information-ofsteds-school-inspections-outcomes`
- Latest CSV asset pattern:
  - `https://assets.publishing.service.gov.uk/media/.../Management_information_-_state-funded_schools_-_latest_inspections_as_at_*.csv`
- Current validated latest CSV (2026-03-02):
  - `https://assets.publishing.service.gov.uk/media/698b20be95285e721cd7127d/Management_information_-_state-funded_schools_-_latest_inspections_as_at_31_Jan_2026.csv`

## Verification Snapshot (Executed 2026-03-02)

### DfE checks

- Publications endpoint returned `200`.
- Publication datasets endpoint returned `200`.
- Dataset metadata endpoint returned `200`.
- Dataset query endpoint returned `200`.
- Dataset CSV endpoint returned `200` and header included `school_urn`.

### Ofsted checks

- Landing page returned `200`.
- Latest linked CSV asset returned `200`.
- CSV headers included:
  - `URN`
  - `Inspection start date`
  - `Publication date`
  - `Latest OEIF overall effectiveness`
  - `Ungraded inspection overall outcome`

## Required Metric Coverage Policy

Required Phase 1 profile metrics:

- `urn`
- `academic_year`
- `fsm_pct`
- `sen_pct`
- `ehcp_pct`
- `ethnicity_*`
- `language_*`
- `ofsted_overall_effectiveness`
- `ofsted_inspection_date`

Coverage policy:

1. If required metric exists in verified source fields:
   - mark as `supported`,
   - implement mapping in source pipeline doc.
2. If required metric does not exist in verified source fields:
   - mark as `unsupported_in_source`,
   - return `null` in API where applicable,
   - expose `coverage` flags in API response,
   - record decision in affected doc under "Decisions".

Current known gap from validated callable endpoints:

- No school-level ethnicity fields identified in current validated DfE endpoint set on 2026-03-02.

## Trend Depth Policy

1. A metric is trendable only if at least 2 academic years exist for a school.
2. A profile is "3-5 year ready" only if at least 3 years exist for target metrics.
3. If fewer years exist:
   - API still returns available years,
   - `delta` and `direction` are `null` when prior year is missing,
   - response includes `history_quality` metadata (`is_partial_history=true`).

## File-Oriented Implementation Plan

1. `tools/scripts/verify_phase1_sources.py` (new)
   - run HTTP checks for all Phase 1 source contracts.
   - validate required field presence in sampled headers/metadata.
   - fail non-zero on missing endpoint or required field.
2. `apps/backend/tests/unit/test_verify_phase1_sources.py` (new)
   - verify parser and gate behavior for pass/fail cases.
3. `.planning/phases/phase-1/source-verification-2026-03-02.md` (new snapshot artefact)
   - store endpoint status and sampled field evidence.
4. `.planning/phases/phase-1/1B-dfe-characteristics-pipeline.md`
   - consume this gate and lock chosen dataset ids/fields.
5. `.planning/phases/phase-1/1C-ofsted-latest-pipeline.md`
   - consume this gate and lock chosen latest CSV extraction logic.

## Acceptance Criteria

1. Source contract checks are executable and reproducible from repo root.
2. Every Phase 1 source-dependent deliverable references this gate and its pass criteria.
3. Unsupported source fields are explicitly documented and represented as coverage gaps, not hidden assumptions.
4. Phase 1 implementation is blocked if source checks fail.

## Risks And Mitigations

- Risk: endpoint contracts drift without warning.
  - Mitigation: executable source verification script as a required pre-implementation step.
- Risk: product scope assumes fields unavailable in callable sources.
  - Mitigation: explicit coverage policy and API-level coverage flags.
- Risk: trend expectations exceed actual historical depth.
  - Mitigation: trend depth policy with partial-history handling.
