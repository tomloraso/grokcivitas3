import type {
  CreateTaskRequest,
  HealthResponse,
  SearchSchoolsQuery,
  SchoolsSearchResponse,
  Task
} from "./types";

export class ApiClientError extends Error {
  readonly status: number;

  constructor(status: number, message?: string) {
    super(message ?? `Request failed: ${status}`);
    this.name = "ApiClientError";
    this.status = status;
  }
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...init
  });

  if (!response.ok) {
    throw new ApiClientError(response.status);
  }

  return (await response.json()) as T;
}

export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/api/v1/health");
}

export async function listTasks(): Promise<Task[]> {
  return request<Task[]>("/api/v1/tasks");
}

export async function createTask(payload: CreateTaskRequest): Promise<Task> {
  return request<Task>("/api/v1/tasks", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function searchSchools({
  postcode,
  radius
}: SearchSchoolsQuery): Promise<SchoolsSearchResponse> {
  const params = new URLSearchParams({ postcode });
  if (radius !== undefined && radius !== null) {
    params.set("radius", radius.toString());
  }

  return request<SchoolsSearchResponse>(`/api/v1/schools?${params.toString()}`);
}
