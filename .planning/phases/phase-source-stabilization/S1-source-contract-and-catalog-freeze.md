# Phase S1 Design - Source Contract And Catalog Freeze

## Document Control

- Status: Complete
- Last updated: 2026-03-04
- Depends on:
  - `.planning/project-brief.md`
  - `.planning/phases/phase-source-stabilization/README.md`
  - `docs/architecture/backend-conventions.md`

## Objective

Freeze the approved demographics source catalog, schema requirements, and fallback behavior so implementation is deterministic and auditable.

## In scope

- Define approved publication families and release series.
- Define required columns per source family.
- Define lookback window and legacy-year rules.
- Define fallback and failure semantics.

## Out of scope

- Code implementation of discovery/ingest.
- API/UI behavior changes (handled in `S4`).

## Source decisions (approved baseline)

1. Primary source family: `school-pupils-and-their-characteristics` school-level underlying data.
2. Secondary source family: `special-educational-needs-in-england` school-level underlying data.
3. Supported release slugs: non-legacy release pages (`2019-20` onward where available).
4. Lookback default: `6` years.

## External endpoints and datasets (authoritative)

### Statistics API (existing reference surface)

- Base docs: `https://api.education.gov.uk/statistics/docs/`
- Existing v1 base: `https://api.education.gov.uk/statistics/v1`

### Release pages used for source discovery

- SPC publication slug: `school-pupils-and-their-characteristics`
- SEN publication slug: `special-educational-needs-in-england`
- Release page template:
  - `https://explore-education-statistics.service.gov.uk/find-statistics/{publicationSlug}/{releaseSlug}`

### Content download endpoint

- `https://content.explore-education-statistics.service.gov.uk/api/releases/{releaseVersionId}/files/{fileId}`

### Approved dataset families

1. SPC: school-level underlying data (exclude class-size files).
2. SEN: school-level underlying data.

## No-overengineering policy

1. No backwards-compatibility shim layer for old single-dataset ingestion.
2. No permanent dual-source execution path that keeps old and new ingestion in parallel.
3. Any temporary validation-only overlap must be time-boxed and removed in the same phase before sign-off.

## Required fields

### SPC required columns

- `urn` or `URN`
- `time_period` (or derive from release slug when absent)
- `% of pupils known to be eligible for free school meals`
- `% of pupils known to be eligible for free school meals (Performance Tables)`
- `% of pupils whose first language is known or believed to be other than English`
- `% of pupils whose first language is known or believed to be English`
- `% of pupils whose first language is unclassified`

### SEN required columns

- `URN`
- `time_period`
- `Total pupils`
- `SEN support`
- `EHC plan`

## Fallback rules

1. If a release page is callable but school-level file is missing, fail source verification for that year.
2. If required columns are missing, fail staging contract checks for that file.
3. If one source family is available and the other is not, load available metrics but mark completeness as partial with explicit reason code.
4. No interpolation across missing years.

## File-oriented implementation plan

1. `.planning/phases/phase-source-stabilization/source-catalog-YYYY-MM-DD.md` (new evidence artifact)
   - record approved publication slug, release slug, release version id, file id, and file name.
2. `apps/backend/src/civitas/infrastructure/config/settings.py`
   - add typed settings for source mode, publication slugs, lookback, and strictness flags.
3. `tools/scripts/verify_phase_s_sources.py` (new)
   - verify callable pages/files and required columns for configured lookback.
4. `apps/backend/tests/unit/test_verify_phase_s_sources.py` (new)
   - test source verifier parsing, failure paths, and deterministic output.

## Codex execution checklist

1. Implement verifier script and unit tests first.
2. Produce one source-catalog artifact from live checks.
3. Fail fast on missing fields/years; do not silently skip.
4. Run required gates and capture output in commit notes.

## Required commands

- `uv run --project apps/backend python tools/scripts/verify_phase_s_sources.py`
- `uv run --project apps/backend pytest apps/backend/tests/unit/test_verify_phase_s_sources.py -q`

## Acceptance criteria

1. Approved source catalog is explicit and versioned in planning artifacts.
2. Source verification script proves callable files and required columns.
3. Failure conditions are explicit and test-covered.

## Implementation tracking (2026-03-04)

- [x] Added `tools/scripts/verify_phase_s_sources.py`.
- [x] Added `apps/backend/tests/unit/test_verify_phase_s_sources.py`.
- [x] Added demographics source settings in `apps/backend/src/civitas/infrastructure/config/settings.py`.
- [x] Generated `.planning/phases/phase-source-stabilization/source-catalog-2026-03-04.md` from live verification.
- [x] Extended SPC contract verification to require direct FSM percentage column.
