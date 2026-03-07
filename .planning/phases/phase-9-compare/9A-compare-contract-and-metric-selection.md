# 9A - Compare Contract And Metric Selection

## Goal

Define the exact compare payload shape and the metric set Phase 9 will support before backend and frontend implementation begins.

## Scope

- Comparison of two to four schools.
- One aligned compare contract shared by search, profile, and compare page entry points.
- Deterministic handling for missing, partial, or differently-dated metrics.

## Compare Sections

The compare experience should ship with these sections:

1. Identity and context
   - name, phase, type, age range, distance where available
2. Inspection
   - latest Ofsted, inspection date, time since inspection
3. Demographics
   - FSM, FSM6, SEN, EHCP, EAL, ethnicity summary
4. Attendance and behaviour
   - attendance, persistent absence, suspensions, exclusions
5. Workforce
   - pupil-teacher ratio, supply share, QTS, leadership snapshot where published
6. Performance
   - core KS2 or KS4 indicators appropriate to school phase
7. Area context
   - IMD, crime, house-price context

## Contract Rules

- Each metric row must expose a stable metric identifier, label, unit, and section key.
- Each school cell must expose:
  - value
  - academic year or snapshot date
  - completeness or availability metadata
  - benchmark metadata where already supported
- Rows should align by metric identifier, not by raw source column names.
- Phase-specific or school-type-specific metrics may be hidden when they are not meaningful for the selected school set.

## Missing-Data Rules

- Unsupported means the metric is not published at the necessary school level.
- Unavailable means the metric is part of the compare set but not available for that school and year.
- Suppressed means the metric exists but is hidden due to source suppression rules.
- Different years across schools are allowed, but year labels must remain visible in every cell.

## Acceptance Criteria

- Compare metric list is frozen and documented.
- Missing-data semantics are shared with existing profile and trends completeness language.
- API contract design is specific enough for schema and web mapping work to start.
