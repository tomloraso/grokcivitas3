import type { components, operations } from "./generated-types";

export type HealthResponse =
  operations["health_api_v1_health_get"]["responses"][200]["content"]["application/json"];

export type Task = components["schemas"]["TaskResponse"];

export type CreateTaskRequest = components["schemas"]["TaskCreateRequest"];

export type SchoolsSearchResponse = components["schemas"]["SchoolsSearchResponse"];

export type SchoolSearchResultItem = components["schemas"]["SchoolSearchItemResponse"];

export type SchoolNameSearchResponse = components["schemas"]["SchoolNameSearchResponse"];

export type SearchSchoolsQuery =
  operations["search_schools_api_v1_schools_get"]["parameters"]["query"];

/* ------------------------------------------------------------------ */
/* School profile + trends (Phase 1D / 1E)                             */
/* ------------------------------------------------------------------ */

export type SchoolProfileResponse = components["schemas"]["SchoolProfileResponse"];

export type SchoolProfileSchool = components["schemas"]["SchoolProfileSchoolResponse"];

export type SchoolProfileDemographicsLatest =
  components["schemas"]["SchoolProfileDemographicsLatestResponse"];

export type SchoolProfileDemographicsCoverage =
  components["schemas"]["SchoolProfileDemographicsCoverageResponse"];

export type SchoolProfileOfstedLatest =
  components["schemas"]["SchoolProfileOfstedLatestResponse"];

export type SchoolTrendsResponse = components["schemas"]["SchoolTrendsResponse"];

export type SchoolTrendsSeries = components["schemas"]["SchoolTrendsSeriesResponse"];

export type SchoolTrendPoint = components["schemas"]["SchoolTrendPointResponse"];

export type SchoolTrendsHistoryQuality =
  components["schemas"]["SchoolTrendsHistoryQualityResponse"];
