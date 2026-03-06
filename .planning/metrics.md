# Metrics Catalog

## Document Control

- Status: Current planning baseline
- Last updated: 2026-03-06
- Scope: Metrics exposed today or explicitly planned for the Civitas school-research product

## Status Meanings

- `Implemented`: shipped end to end in pipeline, API, and UI.
- `Partial`: implemented where publishable, but not all subfields or years are available.
- `Source-limited`: explicit gap due to upstream school-level publication limits.
- `Planned`: intended future metric group, not yet implemented.

## Current Catalog

| Metric group | Status | Source | Notes |
|---|---|---|---|
| Distance from searched postcode | Implemented | Postcodes.io + `schools` geography | Search result headline metric |
| School identity, phase, type, status, age range | Implemented | GIAS | Search and profile baseline |
| Latest Ofsted overall effectiveness | Implemented | Ofsted latest | Profile headline |
| Ofsted sub-judgements | Implemented | Ofsted latest | Profile detail |
| Full Ofsted history | Implemented | Ofsted timeline | Timeline card and trend context |
| Time since last inspection | Implemented | Ofsted latest + timeline | Derived indicator |
| FSM percentage | Implemented | DfE characteristics | Multi-year where available |
| FSM6 percentage | Implemented | DfE characteristics | Multi-year where available |
| SEN support and EHCP | Implemented | DfE characteristics | Multi-year where available |
| SEND primary-need categories | Implemented | DfE characteristics | School-level breakdown |
| Ethnicity breakdown | Implemented | DfE characteristics | School-level breakdown from approved release files |
| EAL percentage | Implemented | DfE characteristics | Multi-year where available |
| Gender breakdown | Partial | DfE characteristics | Available only where derivable from current school-level releases |
| Home-language coverage | Partial | DfE characteristics | School-level language coverage exists, but detailed top-language breadth is source-limited |
| Pupil mobility or turnover | Source-limited | Not published at required school level | Exposed as unavailable where relevant |
| Overall attendance | Implemented | DfE attendance | Latest and multi-year coverage |
| Persistent absence | Implemented | DfE attendance | Latest and multi-year coverage |
| Suspensions | Implemented | DfE behaviour | Latest and multi-year coverage |
| Permanent exclusions | Implemented | DfE behaviour | Latest and multi-year coverage |
| KS2 performance | Implemented | DfE performance | Profile and dashboard coverage |
| KS4 performance | Implemented | DfE performance | Profile and dashboard coverage |
| Attainment 8 and Progress 8 | Implemented | DfE performance | Profile and dashboard coverage |
| EBacc entry and achievement | Implemented | DfE performance | Profile and dashboard coverage |
| Disadvantaged pupil performance gap | Implemented | DfE performance | Profile and dashboard coverage |
| Pupil-teacher ratio | Implemented | DfE workforce | Latest and multi-year coverage |
| Supply or agency staff share | Implemented | DfE workforce | Latest and multi-year coverage |
| QTS coverage | Implemented | DfE workforce | Latest and multi-year coverage |
| Workforce experience or qualification detail | Partial | DfE workforce | Depends on school-level publication coverage |
| Teacher turnover | Partial | DfE workforce | Available where publishable and covered by active assets |
| Leadership snapshot | Partial | GIAS + DfE workforce | Latest snapshot fields only |
| IMD context | Implemented | ONS IMD | Decile, rank, score, IDACI |
| Local crime context | Implemented | Police UK archive | Category counts and local summary |
| House-price context | Implemented | Land Registry | Area trend and context summary |
| Benchmarks for supported metrics | Implemented | Derived from Gold serving layer | Profile, trends, and dashboard responses |
| Cross-domain trend dashboard | Implemented | Derived from Gold serving layer | Dashboard route payload |
| Compare-ready aligned metric set | Planned | Existing Gold facts | Planned for Phase 8 |
| Premium-only data boundary | Planned | Existing Gold facts + entitlements | Planned for Phase 9 |
| Pupil premium impact | Planned | Additional source required | Not yet sourced |

## Product Rules

- Metrics must remain source-backed and non-editorial.
- Missing or partial coverage must be explained explicitly in API and UI metadata.
- Frontend display types should be derived from backend contracts rather than hand-maintained wire models.

## Open Questions

1. Whether pupil premium impact remains worth sourcing for MVP-adjacent delivery.
2. Which benchmark views should become first-class compare metrics in Phase 8.
