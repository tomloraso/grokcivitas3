# Data Architecture

## Principles

1. **Every byte traceable.** Any value in Gold (PostgreSQL) can be traced back through Staging to Bronze (raw source file).
2. **Bronze is the reproducibility checkpoint.** Gold can be rebuilt entirely from raw files without re-downloading sources.
3. **Bronze is immutable.** Raw files are never modified after download. Each download is timestamped.
4. **One pipeline pattern per source.** Each data source follows the same Bronze -> Staging -> Gold path, implemented as a discrete pipeline module.
5. **Schema changes are explicit.** Gold migrations are tracked via Alembic or equivalent.

---

## Layer definitions

### Bronze - Raw archive

**Location:** `data/bronze/{source}/{yyyy-mm-dd}/`  
**Format:** Original files exactly as downloaded (CSV, JSON, ZIP).  
**Retention:** Indefinite (audit trail).  
**Write pattern:** Download script saves file with timestamp. Never overwrites.

Example structure:
```
data/bronze/
  dfe-pupil-characteristics/
    2025-06-15/
      england_school_information.csv
      ...
  gias/
    2026-01-20/
      edubasealldata.csv
  ofsted/
    2026-01-20/
      management_information_schools.csv
  police-uk/
    2026-01/
      2026-01-avon-and-somerset-street.csv
      ...
  land-registry/
    2026-01/
      pp-monthly-update.csv
  ons-imd/
    2025-09-10/
      imd2019lsoa.csv
```

### Staging - Cleaned and validated (PostgreSQL)

**Location:** PostgreSQL staging schema (`staging.{source}_{run_date}`).  
**Format:** PostgreSQL tables loaded via `COPY FROM` CSV.  
**Lifecycle:** Created per pipeline run, dropped after successful Gold upsert.  
**Write pattern:** Full load per source per pipeline run. Idempotent.

Staging responsibilities:
- **Type casting** - string dates -> date types, numeric strings -> floats/ints.
- **Column renaming** - source-specific column names -> canonical names.
- **Deduplication** - remove exact duplicates within a source.
- **Null handling** - source-specific sentinel values (for example: "SUPP", "x", "NE") -> explicit nulls.
- **Validation** - reject rows missing required fields (for example: school URN). Log rejections.

Staging does NOT:
- Join across sources.
- Apply business logic or derived metrics.
- Denormalize for serving.

### Gold - Serving store (PostgreSQL + PostGIS)

**Engine:** PostgreSQL 16+ with PostGIS extension.  
**Write pattern:** Pipeline upserts from staging tables into Gold tables. Transactional so loads are atomic.

Gold responsibilities:
- **Cross-source joins** - link schools (GIAS) to metrics (DfE), inspections (Ofsted), and area context (crime, IMD).
- **Enrichment** - postcode resolution to lat/lng (via Postcodes.io), distance calculations.
- **Denormalization** - materialized views or denormalized tables optimized for API query patterns.
- **Indexing** - PostGIS GIST spatial indexes, B-tree on URN/school ID, compound indexes on common filters.
- **History** - typed yearly snapshots per school (domain-specific fact tables), enabling trend queries without EAV pivots.

**Advantages of staging-in-PostgreSQL over a separate format (for example, Parquet):**
- One query language (SQL) for transform and serving.
- `COPY FROM` CSV is fast for bulk ingestion.
- Staging and Gold can share transaction boundaries.
- No extra format/tooling dependency for MVP.
- If needed later, Parquet can be introduced at a Bronze -> Staging boundary extension.

---

## Source catalog

### 1. GIAS (Get Information About Schools)

**URL:** https://get-information-schools.service.gov.uk/Downloads  
**Refresh:** Ongoing (GIAS updates as schools change)  
**Ingestion cadence:** Weekly or on-demand  
**Key fields:** URN, EstablishmentName, TypeOfEstablishment (name), PhaseOfEducation (name), EstablishmentStatus (name), Postcode, Easting, Northing, OpenDate, CloseDate, StatutoryLowAge, StatutoryHighAge, SchoolCapacity, NumberOfPupils  
**Role in Gold:** Canonical school dimension table. Every other source joins to GIAS via URN.
**Coordinate rule:** Convert Easting/Northing from EPSG:27700 (BNG) to EPSG:4326 for serving geometry.

### 2. DfE School Performance / Pupil Characteristics

**URL:** https://explore-education-statistics.service.gov.uk/  
**Refresh:** Annual (typically June)  
**Ingestion cadence:** Annual after release  
**Key fields:** URN, AcademicYear, FSMPercentage, FSM6Percentage, SENPercentage, EHCPPercentage, EthnicityBreakdown, TopLanguages  
**Role in Gold:** Demographics and need metrics stored in typed yearly fact tables for trend queries.

### 3. Ofsted Inspections

**URL:** https://www.gov.uk/government/statistical-data-sets/monthly-management-information-ofsteds-school-inspections-outcomes  
**Refresh:** Monthly  
**Ingestion cadence:** Monthly  
**Key fields:** URN, InspectionDate, OverallEffectiveness, PreviousOverallEffectiveness, InspectionType  
**Role in Gold:** Inspection history timeline. Latest rating as headline; full history for timeline view.

### 4. Police UK crime data

**URL:** https://data.police.uk/docs/  
**Refresh:** Monthly (with lag)  
**Ingestion cadence:** Monthly  
**Primary ingestion path:** Bulk monthly data files (preferred for reproducible full refreshes).  
**Fallback path:** API for targeted refreshes/ad-hoc lookups only.  
**Key fields:** Latitude, Longitude, Category, Month  
**Role in Gold:** Area crime context aggregated within configurable radius of school location.

### 5. Land Registry Price Paid

**URL:** https://www.gov.uk/government/statistical-data-sets/price-paid-data-downloads  
**Refresh:** Monthly CSV  
**Ingestion cadence:** Monthly  
**Key fields:** Price, DateOfTransfer, Postcode, PropertyType  
**Role in Gold:** Optional area context - median house price within school postcode district (aggregate only).  
**MVP status:** Optional. Include if time allows; exclude without impact.

### 6. Postcodes.io

**URL:** https://postcodes.io/  
**Refresh:** Stable  
**Ingestion cadence:** On-demand (lookup at search time + batch enrichment for school postcodes)  
**Key fields:** postcode -> latitude, longitude, lsoa, admin_district  
**Role in Gold:** Postcode resolution for user search and school LSOA enrichment for IMD joins.
**Runtime rule:** API search uses cache-first postcode resolution (`postcode_cache`) with TTL refresh.

### 7. ONS Index of Multiple Deprivation (IMD)

**URL:** https://www.gov.uk/government/statistics/english-indices-of-deprivation-2019  
**Refresh:** Periodic  
**Ingestion cadence:** On new release  
**Key fields:** LSOA, IMDDecile, IncomeDecile, ChildPovertyIndex  
**Role in Gold:** Area deprivation context joined via LSOA.

---

## Gold schema - key tables (indicative)

```
schools
  urn (PK)
  name, phase, type, status
  postcode, lat, lng      -- geography(Point, 4326)
  capacity, pupil_count
  open_date, close_date
  updated_at

school_demographics_yearly
  urn (FK), academic_year
  fsm_pct, fsm6_pct, sen_pct, ehcp_pct
  ethnicity_breakdown_json, top_languages_json
  (PK: urn + academic_year)

school_ofsted_latest
  urn (PK/FK)
  inspection_date, overall_effectiveness
  source_published_at

ofsted_inspections
  urn (FK), inspection_date
  overall_effectiveness, previous_effectiveness
  inspection_type

area_crime_context
  urn (FK), month
  crime_category, incident_count

area_deprivation
  lsoa (PK)
  imd_decile, income_decile, child_poverty_index

postcode_cache
  postcode (PK)
  lat, lng, lsoa, admin_district
  cached_at
```

**Indexes (minimum):**
- `schools.geography` - GIST spatial index for radius queries
- `schools.urn` - B-tree (PK)
- `school_demographics_yearly (urn, academic_year)` - compound index for trend queries
- `school_ofsted_latest.urn` - B-tree (PK)
- `ofsted_inspections (urn, inspection_date)` - compound index for timeline
- `area_crime_context (urn, month)` - compound index
- `postcode_cache.postcode` - B-tree (PK)

---

## Pipeline design

### Architecture

Each data source is a pipeline module in `apps/backend/src/civitas/infrastructure/pipelines/`:

```
pipelines/
  base.py              -- Abstract pipeline interface
  gias.py              -- GIAS: download -> clean -> load
  dfe_characteristics.py
  ofsted.py
  police_crime.py
  land_registry.py
  postcodes.py
  ons_imd.py
```

Each module implements:
1. **Download** - fetch source to Bronze, timestamped.
2. **Stage** - load Bronze CSV into PostgreSQL staging table, clean/validate.
3. **Promote** - upsert from staging into Gold production tables. Drop staging on success.

### Orchestration (MVP)

- CLI command: `civitas pipeline run --source gias` (or `--all`)
- Sequential execution per source.
- Logging: row counts, rejected rows, timing per stage.
- No external orchestrator for MVP (no Airflow/Dagster). CLI + scheduler job is sufficient.
- Future: add a lightweight orchestrator when dependency graphs/retries are needed.

### Error handling

- **Bronze:** download failure -> log and abort that source. No partial writes.
- **Staging:** validation failures -> write error log with rejected rows; continue with valid rows.
- **Gold:** promote failure -> transaction rollback. No partial serving state; staging preserved for debugging.

---

## Data refresh cadence

| Source | Refresh frequency | Pipeline trigger |
|--------|-------------------|-----------------|
| GIAS | Weekly | Scheduled job |
| DfE characteristics | Annual | Manual after release |
| Ofsted | Monthly | Scheduled job |
| Police UK | Monthly | Scheduled job |
| Land Registry | Monthly | Scheduled job |
| Postcodes.io | On-demand | Called during enrichment |
| ONS IMD | On new release | Manual |

---

## Open questions

1. **School workforce data** - DfE publishes teacher/staff data separately. Include in MVP or defer?
2. **Historical backfill** - how many years of DfE data are available for download? Need to verify archive access.
3. **Police API fallback limits** - if API fallback is used, what throttling strategy is required?
4. **Land Registry** - include in MVP or defer to Phase 2?
5. **Typed metrics JSON boundaries** - which non-core metrics stay in typed columns vs JSON blobs (ethnicity/language detail)?
