# M4 - Workforce and Leadership Pipelines

## Goal

Add staffing and leadership context metrics from workforce publications and existing school metadata.

## Gap Coverage

- Pupil-teacher ratio
- Supply/agency staff percentage
- Teachers with 3+ years experience
- Teacher turnover
- QTS percentage
- Staff qualifications and leadership details where available

## Source Strategy

- New external sources required for workforce metrics (DfE School Workforce publications/API).
- Existing source extension for leadership where available in GIAS/Ofsted metadata.
- Mandatory endpoint/file schema inspection before normalization contract design.

## Bronze -> Silver -> Gold Plan

1. Bronze:
   - add workforce source download and manifest with release metadata.
2. Silver:
   - normalize yearly workforce rows and leadership attributes.
3. Gold:
   - add `school_workforce_yearly` keyed by `(urn, academic_year)`;
   - add/update leadership snapshot table if required for non-yearly fields.

## API Plan

1. Extend profile with workforce latest values and leadership snapshot.
2. Extend trends endpoint with workforce series where available.
3. Add completeness sections for workforce and leadership.

## Frontend Plan

1. Add staffing cards and trend indicators to the profile page.
2. Add leadership metadata block with explicit source freshness.
3. Ensure unavailable source conditions render deterministic copy.

## Validation and Gates

- Schema-contract tests and representative normalization fixtures.
- Profile/trends integration coverage for workforce metrics.
- Performance checks for added joins and payload size.
