# M2 - Demographics and Support Depth

## Goal

Complete the remaining demographics/support metrics not yet exposed from current school-level datasets.

## Gap Coverage

- FSM6
- SEND primary need categories
- Gender breakdown (% male / % female)
- Pupil mobility / turnover
- Top 5 home languages (if school-level published)

## Source Strategy

1. Existing ingested source extension first:
   - evaluate SPC/SEN school-level files already downloaded via `dfe_characteristics` for required columns.
2. If unavailable, add a new DfE source slice and document school-level publication limits.

## Bronze -> Silver -> Gold Plan

1. Bronze:
   - keep current release-file discovery for SPC/SEN;
   - if required, add a new publication slug/file-discovery path for missing fields.
2. Silver:
   - extend normalization contracts for supported columns and suppression tokens.
3. Gold:
   - extend `school_demographics_yearly` with typed columns for supported metrics;
   - if high-cardinality primary needs/languages require multiple rows, add dedicated yearly child tables keyed by `(urn, academic_year, category)`.

## API Plan

1. Extend profile response demographics payload with newly supported fields.
2. Add completeness reason codes for unpublishable school-level fields.
3. Keep unsupported list aligned with actual source publication behavior.

## Frontend Plan

1. Add new demographic cards and ranked lists for categories.
2. Reuse existing coverage notice pattern for unsupported/not-published fields.
3. Add trend visual support where multi-year values are present.

## Validation and Gates

- Source-contract tests for each new mapped column.
- Integration tests for demographics/profile payload parity.
- Explicit documentation for any metric still unavailable due source policy.
