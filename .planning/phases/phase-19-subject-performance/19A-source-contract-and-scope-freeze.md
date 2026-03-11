# Phase 19 / 19A Design - Source Contract And Scope Freeze

## Document Control

- Status: Planned
- Last updated: 2026-03-11
- Depends on:
  - `.planning/project-brief.md`
  - `docs/runbooks/pipelines.md`

## Objective

Freeze the exact subject-level source contracts and the boundary between in-scope school-level data and out-of-scope national-only value-added data.

## Verified School-Level Sources

KS4 subject exam data:

- data-catalogue page:
  - `https://explore-education-statistics.service.gov.uk/data-catalogue/data-set/49abed18-1c61-489f-afc0-11f501335da1`
- CSV route:
  - `https://explore-education-statistics.service.gov.uk/data-catalogue/data-set/49abed18-1c61-489f-afc0-11f501335da1/csv`
- verified header:
  - `time_period`
  - `time_identifier`
  - `geographic_level`
  - `country_code`
  - `country_name`
  - `school_laestab`
  - `school_urn`
  - `school_name`
  - `old_la_code`
  - `new_la_code`
  - `la_name`
  - `version`
  - `establishment_type_group`
  - `pupil_count`
  - `qualification_type`
  - `qualification_detailed`
  - `grade_structure`
  - `subject`
  - `discount_code`
  - `subject_discount_group`
  - `grade`
  - `number_achieving`

16-18 entries and grades by institution and subject:

- data-catalogue page:
  - `https://explore-education-statistics.service.gov.uk/data-catalogue/data-set/9a275c77-4325-4ac8-aa9e-b1a2bd3ab63b`
- CSV route:
  - `https://explore-education-statistics.service.gov.uk/data-catalogue/data-set/9a275c77-4325-4ac8-aa9e-b1a2bd3ab63b/csv`
- verified header:
  - `time_period`
  - `time_identifier`
  - `geographic_level`
  - `country_code`
  - `country_name`
  - `version`
  - `old_la_code`
  - `new_la_code`
  - `la_name`
  - `school_name`
  - `school_urn`
  - `school_laestab`
  - `exam_cohort`
  - `qualification_detailed`
  - `qualification_level`
  - `a_level_equivelent_size`
  - `gcse_equivelent_size`
  - `grade_structure`
  - `subject`
  - `grade`
  - `entries_count`

## Verified National-Only Source

Subject value-added by qualification and subject:

- data-catalogue page:
  - `https://explore-education-statistics.service.gov.uk/data-catalogue/data-set/45296a16-8886-4ed9-aa50-2b907436e9bf`
- CSV route:
  - `https://explore-education-statistics.service.gov.uk/data-catalogue/data-set/45296a16-8886-4ed9-aa50-2b907436e9bf/csv`
- verified header:
  - `time_period`
  - `time_identifier`
  - `geographic_level`
  - `country_code`
  - `country_name`
  - `version`
  - `establishment_type_group`
  - `breakdown_topic`
  - `sex`
  - `ethnicity_major`
  - `ethnicity_minor`
  - `fsm_status`
  - `sen_status`
  - `disadvantage_status`
  - `first_language`
  - `ks2_scaled_score_group`
  - `school_admission_type`
  - `school_religious_character`
  - `qualification_type`
  - `subject`
  - `grade`
  - `number_achieving`
  - `percentage_achieving`

Scope rule:

- this dataset is not school-level and must not be used to fabricate school-level subject progress scores

## Bronze Strategy

1. Store raw CSV assets under:
   - `data/bronze/ks4_subject_performance/<run-date>/<academic_year>/`
   - `data/bronze/sixteen_to_eighteen_subject_performance/<run-date>/<academic_year>/`
2. Register explicit pipeline sources:
   - `ks4_subject_performance`
   - `sixteen_to_eighteen_subject_performance`
3. Add dedicated settings for each source's public CSV route, release page URL, and data-catalogue URL rather than overloading `dfe_performance` or `leaver_destinations`.
4. Manifest captures:
   - source URL
   - release page URL
   - data-catalogue URL
   - published `version`
   - observed headers
   - checksum
   - row count
   - download timestamp
5. Bronze remains the immutable audit surface for every downloaded asset; Silver/Gold may derive canonical serving rows from it but must not discard the underlying asset metadata.

## Versioning Rule

1. Published source `version` values are treated as meaningful release states, not incidental metadata.
2. If the same business-grain row is published in multiple versions, pipeline storage must preserve each version distinctly somewhere queryable by operators.
3. The serving layer must use an explicit preferred-version rule instead of whichever version happened to load last.

## Acceptance Criteria

1. Source contracts are frozen before pipeline code lands.
2. School-level and national-only sources are not conflated.
3. The phase remains honest about what is and is not supported by verified school-level data.
4. Pipeline source registration and configuration are explicit enough that subject-performance runs can be operated independently in the existing Bronze -> Silver -> Gold framework.
