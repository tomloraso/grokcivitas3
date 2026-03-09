import type {
  BillingPortalSessionCreateRequest,
  BillingPortalSessionCreateResponse,
  BillingProductsResponse,
  CheckoutSessionCreateRequest,
  CheckoutSessionCreateResponse,
  CheckoutSessionStatusResponse,
  AuthStartResponse,
  CreateTaskRequest,
  HealthResponse,
  SchoolCompareResponse,
  SchoolNameSearchResponse,
  SchoolProfileResponse,
  SchoolTrendDashboardResponse,
  SchoolTrendsResponse,
  SearchSchoolsQuery,
  SessionResponse,
  SchoolsSearchResponse,
  Task
} from "./types";

const SCHOOL_ENDPOINT_CACHE_TTL_MS = 5 * 60 * 1000;
const SCHOOL_ENDPOINT_CACHE_LIMIT = 200;
const SCHOOL_PROFILE_PATH_RE = /^\/api\/v1\/schools\/[^/?#]+$/;
const SCHOOL_COMPARE_PATH_RE = /^\/api\/v1\/schools\/compare\?urns=[^?#]+$/;
const SCHOOL_TRENDS_PATH_RE = /^\/api\/v1\/schools\/[^/?#]+\/trends$/;
const SCHOOL_TRENDS_DASHBOARD_PATH_RE =
  /^\/api\/v1\/schools\/[^/?#]+\/trends\/dashboard$/;

interface CacheEntry {
  value: unknown;
  expiresAt: number;
}

const responseCache = new Map<string, CacheEntry>();
const inFlightRequests = new Map<string, Promise<unknown>>();

interface StartSignInInput {
  email: string;
  returnTo?: string | null;
}

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

  if (
    SCHOOL_COMPARE_PATH_RE.test(url) ||
    SCHOOL_PROFILE_PATH_RE.test(url) ||
    SCHOOL_TRENDS_PATH_RE.test(url) ||
    SCHOOL_TRENDS_DASHBOARD_PATH_RE.test(url)
  ) {
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
    const { credentials, headers: incomingHeaders, ...restInit } = init ?? {};
    const headers = new Headers(incomingHeaders);
    if (!headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }

    const response = await fetch(url, {
      ...restInit,
      credentials: credentials ?? "same-origin",
      headers
    });

    if (!response.ok) {
      let message: string | undefined;
      try {
        const payload = (await response.json()) as { detail?: unknown };
        if (typeof payload.detail === "string") {
          message = payload.detail;
        }
      } catch {
        // Keep the default status-only message when the error body is empty or invalid.
      }

      throw new ApiClientError(response.status, message);
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
  resetApiRequestCache();
}

export function resetApiRequestCache(): void {
  responseCache.clear();
  inFlightRequests.clear();
}

export async function startSignIn(
  payload: StartSignInInput
): Promise<AuthStartResponse> {
  return request<AuthStartResponse>("/api/v1/auth/start", {
    method: "POST",
    body: JSON.stringify({
      email: payload.email,
      return_to: payload.returnTo ?? null
    })
  });
}

export async function getSession(): Promise<SessionResponse> {
  return request<SessionResponse>("/api/v1/session");
}

export async function signOut(): Promise<SessionResponse> {
  return request<SessionResponse>("/api/v1/auth/signout", {
    method: "POST"
  });
}

export async function listBillingProducts(): Promise<BillingProductsResponse> {
  return request<BillingProductsResponse>("/api/v1/billing/products");
}

export async function createCheckoutSession(
  payload: CheckoutSessionCreateRequest
): Promise<CheckoutSessionCreateResponse> {
  return request<CheckoutSessionCreateResponse>(
    "/api/v1/billing/checkout-sessions",
    {
      method: "POST",
      body: JSON.stringify(payload)
    }
  );
}

export async function getCheckoutSessionStatus(
  checkoutId: string
): Promise<CheckoutSessionStatusResponse> {
  return request<CheckoutSessionStatusResponse>(
    `/api/v1/billing/checkout-sessions/${encodeURIComponent(checkoutId)}`
  );
}

export async function createBillingPortalSession(
  payload: BillingPortalSessionCreateRequest
): Promise<BillingPortalSessionCreateResponse> {
  return request<BillingPortalSessionCreateResponse>(
    "/api/v1/billing/portal-sessions",
    {
      method: "POST",
      body: JSON.stringify(payload)
    }
  );
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
  radius,
  phase,
  sort
}: SearchSchoolsQuery): Promise<SchoolsSearchResponse> {
  const params = new URLSearchParams({ postcode });
  if (radius !== undefined && radius !== null) {
    params.set("radius", radius.toString());
  }
  if (phase) {
    for (const phaseValue of phase) {
      params.append("phase", phaseValue);
    }
  }
  if (sort !== undefined && sort !== null) {
    params.set("sort", sort);
  }

  return request<SchoolsSearchResponse>(`/api/v1/schools?${params.toString()}`);
}

export async function searchSchoolsByName(
  name: string
): Promise<SchoolNameSearchResponse> {
  const params = new URLSearchParams({ name });
  return request<SchoolNameSearchResponse>(
    `/api/v1/schools/search?${params.toString()}`
  );
}

export async function getSchoolProfile(
  urn: string
): Promise<SchoolProfileResponse> {
  return request<SchoolProfileResponse>(
    `/api/v1/schools/${encodeURIComponent(urn)}`
  );
}

export async function getSchoolCompare(
  urns: string[]
): Promise<SchoolCompareResponse> {
  const params = new URLSearchParams({ urns: urns.join(",") });
  return request<SchoolCompareResponse>(
    `/api/v1/schools/compare?${params.toString()}`
  );
}

export async function getSchoolTrends(
  urn: string
): Promise<SchoolTrendsResponse> {
  return request<SchoolTrendsResponse>(
    `/api/v1/schools/${encodeURIComponent(urn)}/trends`
  );
}

export async function getSchoolTrendDashboard(
  urn: string
): Promise<SchoolTrendDashboardResponse> {
  return request<SchoolTrendDashboardResponse>(
    `/api/v1/schools/${encodeURIComponent(urn)}/trends/dashboard`
  );
}
