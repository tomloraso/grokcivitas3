import type { components, operations } from "./generated-types";

export type HealthResponse =
  operations["health_api_v1_health_get"]["responses"][200]["content"]["application/json"];

export type Task = components["schemas"]["TaskResponse"];

export type CreateTaskRequest = components["schemas"]["TaskCreateRequest"];
