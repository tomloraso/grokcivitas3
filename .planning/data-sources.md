# Data Sources

This document defines every data source used by Civitas. All sources are public UK government or open data. The pipeline will ingest, clean, and join them into PostGIS.

## Core School Data
- **GIAS (Get Information About Schools)**  
  Source: Department for Education (DfE)  
  What it provides: School identifiers, phase, type, location (postcode, coordinates), capacity, pupil numbers, governance.  
  Extraction: Bulk CSV download + API.  
  Frequency: Updated termly (January, May, October). Full refresh every 3 months.

- **Ofsted Inspection Data**  
  Source: Ofsted  
  What it provides: Overall effectiveness rating, sub-judgements, inspection dates, key findings.  
  Extraction: Ofsted API + bulk CSV exports.  
  Frequency: Real-time as reports are published + full refresh quarterly.

- **DfE School Census & Performance Data**  
  Source: Department for Education  
  What it provides: Pupil characteristics (FSM, ethnicity, SEN, EAL, attendance, exclusions), staffing, Attainment 8 / Progress 8, KS2 results.  
  Extraction: Termly census files + annual performance tables (CSV).  
  Frequency: Termly for census, annual for performance data.

## Area & Context Data
- **Postcode & Geography**  
  Source: postcodes.io (open API)  
  Extraction: API calls during ingestion.  
  Frequency: Real-time (static data).

- **Crime Statistics**  
  Source: police.uk (open data)  
  Extraction: Monthly CSV bulk download.  
  Frequency: Monthly.

- **Index of Multiple Deprivation (IMD)**  
  Source: Ministry of Housing, Communities & Local Government  
  Extraction: Latest release CSV.  
  Frequency: Updated every 3–4 years (use latest 2025 release).

- **House Prices**  
  Source: HM Land Registry (UK House Price Index)  
  Extraction: Monthly CSV + postcode-level data.  
  Frequency: Monthly (average price within 1-hour radius or 5-mile radius).

## Pipeline Notes
- All ingestion will be automated via scheduled jobs (GitHub Actions or Render cron).
- Data will be versioned and stored with timestamps.
- Joins will happen on URN (Unique Reference Number) and postcode.
- Full refresh cycle: every 3 months + event-triggered (new Ofsted report, new census).