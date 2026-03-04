import type {
  CreateTaskRequest,
  HealthResponse,
  SchoolNameSearchResponse,
  SchoolProfileResponse,
  SchoolTrendsResponse,
  SearchSchoolsQuery,
  SchoolsSearchResponse,
  Task
} from "./types";

const SCHOOL_ENDPOINT_CACHE_TTL_MS = 5 * 60 * 1000;
const SCHOOL_ENDPOINT_CACHE_LIMIT = 200;
const SCHOOL_PROFILE_PATH_RE = /^\/api\/v1\/schools\/[^/?#]+$/;
const SCHOOL_TRENDS_PATH_RE = /^\/api\/v1\/schools\/[^/?#]+\/trends$/;

interface CacheEntry {
  value: unknown;
  expiresAt: number;
}

const responseCache = new Map<string, CacheEntry>();
const inFlightRequests = new Map<string, Promise<unknown>>();

export class ApiClientError extends Error {
  readonly status: number;

  constructor(status: number, message?: string) {
    super(message ?? `Request failed: ${status}`);
    this.name = "ApiClientError";
    this.status = status;
  }
}

function normalizeMethod(init?: RequestInit): string {
  return (init?.method ?? "GET").toUpperCase();
}

function cacheTtlForRequest(url: string, init?: RequestInit): number | null {
  if (normalizeMethod(init) !== "GET") {
    return null;
  }

  if (SCHOOL_PROFILE_PATH_RE.test(url) || SCHOOL_TRENDS_PATH_RE.test(url)) {
    return SCHOOL_ENDPOINT_CACHE_TTL_MS;
  }

  return null;
}

function readFromCache<T>(key: string): T | null {
  const entry = responseCache.get(key);
  if (!entry) {
    return null;
  }

  if (entry.expiresAt <= Date.now()) {
    responseCache.delete(key);
    return null;
  }

  // Refresh insertion order to keep this entry hot.
  responseCache.delete(key);
  responseCache.set(key, entry);
  return entry.value as T;
}

function writeToCache(key: string, value: unknown, ttlMs: number): void {
  responseCache.delete(key);
  responseCache.set(key, {
    value,
    expiresAt: Date.now() + ttlMs
  });

  while (responseCache.size > SCHOOL_ENDPOINT_CACHE_LIMIT) {
    const [oldestKey] = responseCache.keys();
    if (!oldestKey) {
      break;
    }
    responseCache.delete(oldestKey);
  }
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const cacheTtlMs = cacheTtlForRequest(url, init);
  const cacheKey = `${normalizeMethod(init)}:${url}`;

  if (cacheTtlMs !== null) {
    const cached = readFromCache<T>(cacheKey);
    if (cached !== null) {
      return cached;
    }

    const existingRequest = inFlightRequests.get(cacheKey);
    if (existingRequest) {
      return (await existingRequest) as T;
    }
  }

  const runRequest = async (): Promise<T> => {
    const response = await fetch(url, {
      headers: { "Content-Type": "application/json" },
      ...init
    });

    if (!response.ok) {
      throw new ApiClientError(response.status);
    }

    return (await response.json()) as T;
  };

  if (cacheTtlMs === null) {
    return runRequest();
  }

  const requestPromise = runRequest() as Promise<unknown>;
  inFlightRequests.set(cacheKey, requestPromise);

  try {
    const payload = (await requestPromise) as T;
    writeToCache(cacheKey, payload, cacheTtlMs);
    return payload;
  } finally {
    inFlightRequests.delete(cacheKey);
  }
}

export function prefetchSchoolProfile(urn: string): void {
  void Promise.all([
    getSchoolProfile(urn),
    getSchoolTrends(urn).catch(() => null)
  ]).catch(() => undefined);
}

export function __resetApiRequestCacheForTests(): void {
  responseCache.clear();
  inFlightRequests.clear();
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

export async function searchSchoolsByName(name: string): Promise<SchoolNameSearchResponse> {
  const params = new URLSearchParams({ name });
  return request<SchoolNameSearchResponse>(`/api/v1/schools/search?${params.toString()}`);
}

export async function getSchoolProfile(urn: string): Promise<SchoolProfileResponse> {
  return request<SchoolProfileResponse>(`/api/v1/schools/${encodeURIComponent(urn)}`);
}

export async function getSchoolTrends(urn: string): Promise<SchoolTrendsResponse> {
  return request<SchoolTrendsResponse>(
    `/api/v1/schools/${encodeURIComponent(urn)}/trends`
  );
}
