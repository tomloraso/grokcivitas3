# Data Sources

## Document Control

- Status: Current planning baseline
- Last updated: 2026-03-06
- Scope: Sources actively used or explicitly planned for the Civitas school-research product

## Active Source Catalog

| Source key | Upstream source | Cadence | Current usage | Notes |
|---|---|---|---|---|
| `gias` | Get Information About Schools bulk downloads | Ongoing, refreshed on schedule | School identity, governance, contact, location, capacity, and enriched profile fields | Canonical school dimension |
| `dfe_characteristics` | DfE SPC + SEN school-level underlying files | Annual release family with multi-year lookback | Demographics, FSM/FSM6, EAL, ethnicity, SEND, language coverage where published | Uses the Phase 4 release-file strategy |
| `dfe_attendance` | DfE attendance release files | Annual or term-aligned release cadence | Attendance, absence, and persistent absence trends | School-level release-file ingestion |
| `dfe_behaviour` | DfE suspensions and exclusions release files | Annual | Suspensions and exclusions trends | School-level release-file ingestion |
| `dfe_workforce` | DfE workforce release files | Annual | Workforce metrics and leadership snapshots | Some detailed metrics remain source-limited |
| `dfe_performance` | DfE statistics APIs for KS2 and KS4 | Annual | Performance indicators and disadvantaged gap | API-backed rather than file-backed |
| `ofsted_latest` | Ofsted latest inspection asset | Monthly | Headline rating, sub-judgements, most recent inspection date | Latest snapshot view |
| `ofsted_timeline` | Ofsted inspection history assets | Monthly with historical backfill assets | Full inspection history timeline | Timeline view and derived inspection age |
| `ons_imd` | English Indices of Deprivation release files | New release only | IMD decile, rank, score, and IDACI context | Joined through LSOA |
| `police_crime_context` | Police UK monthly archive files | Monthly | Local crime counts and categories within configured radius | Archive is primary; API is fallback or verification only |
| `uk_house_prices` | HM Land Registry monthly data | Monthly | House-price context and trends | Area-level aggregate use only |
| `postcodes_io` | Postcodes.io API | On demand | User-postcode resolution, LSOA and geography enrichment | Cache-first runtime behavior |

## Planned Additional Source Work

These are not yet active sources, but they remain candidates for later phases:

- payment provider API for premium access
- authentication provider contracts
- any future source required for pupil premium impact or other currently missing metrics

## Source Strategy Notes

### Identity and geography

- `gias` remains the canonical join surface for school identity.
- `postcodes_io` supports both user search and area-context enrichment.

### School metrics

- Characteristics, attendance, behaviour, and workforce now rely on verified school-level releases rather than one-off exploratory paths.
- Performance data is API-driven and therefore requires contract checks before release-dependent work.

### Area context

- IMD, crime, and house-price context are currently the active area enrichments.
- Health and other public-service datasets remain post-MVP candidates.

## Current Source-Limited Areas

- Pupil mobility or turnover is not available at the required school-level granularity in the current active releases.
- Detailed top-language lists are only partially available at school level.
- Some workforce experience, turnover, qualifications, and leadership detail remain source-limited depending on the release family.
- Pupil premium impact still requires additional source definition before implementation.

## Pipeline Expectations

- Every source must flow through Bronze -> Silver -> Gold.
- Canonical Bronze root is `data/bronze`.
- Source verification evidence should be captured before implementation when the upstream contract is unstable, discovered dynamically, or API-driven.
