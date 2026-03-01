import type { components, operations } from "./generated-types";

export type HealthResponse =
  operations["health_api_v1_health_get"]["responses"][200]["content"]["application/json"];

export type Task = components["schemas"]["TaskResponse"];

export type CreateTaskRequest = components["schemas"]["TaskCreateRequest"];

export type SchoolsSearchResponse = components["schemas"]["SchoolsSearchResponse"];

export type SchoolSearchResultItem = components["schemas"]["SchoolSearchItemResponse"];

export type SearchSchoolsQuery =
  operations["search_schools_api_v1_schools_get"]["parameters"]["query"];
