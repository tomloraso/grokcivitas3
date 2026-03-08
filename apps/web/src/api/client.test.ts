import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  __resetApiRequestCacheForTests,
  ApiClientError,
  getSchoolProfile,
  getSchoolTrendDashboard,
  getSchoolTrends,
  prefetchSchoolProfile,
  searchSchools
} from "./client";
import type {
  SchoolProfileResponse,
  SchoolTrendDashboardResponse,
  SchoolsSearchResponse,
  SchoolTrendsResponse
} from "./types";

const URN = "136655";

const profilePayload = {
  school: { urn: URN, name: "Congleton High School" }
} as unknown as SchoolProfileResponse;

const trendsPayload = {
  urn: URN,
  years_available: [],
  history_quality: {
    is_partial_history: false,
    min_years_for_delta: 2,
    years_count: 0
  },
  series: {
    disadvantaged_pct: [],
    sen_pct: [],
    ehcp_pct: [],
    eal_pct: [],
    first_language_english_pct: [],
    first_language_unclassified_pct: []
  },
  completeness: {
    status: "unavailable",
    reason_code: null,
    last_updated_at: null,
    years_available: []
  }
} as unknown as SchoolTrendsResponse;

const dashboardPayload = {
  urn: URN,
  sections: []
} as unknown as SchoolTrendDashboardResponse;

const searchPayload = {
  query: {
    postcode: "SW1A 1AA",
    radius_miles: 5,
    phases: ["primary"],
    sort: "academic"
  },
  center: {
    lat: 51.501009,
    lng: -0.141588
  },
  count: 0,
  schools: []
} as unknown as SchoolsSearchResponse;

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" }
  });
}

async function flushPromises(): Promise<void> {
  await Promise.resolve();
  await Promise.resolve();
}

describe("api client school endpoint cache", () => {
  beforeEach(() => {
    __resetApiRequestCacheForTests();
    vi.restoreAllMocks();
  });

  it("reuses an in-flight school profile request for the same URN", async () => {
    let resolvePending: ((response: Response) => void) | null = null;
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockImplementation(
        () =>
          new Promise<Response>((resolve) => {
            resolvePending = resolve;
          })
      );

    const first = getSchoolProfile(URN);
    const second = getSchoolProfile(URN);

    expect(fetchMock).toHaveBeenCalledTimes(1);

    if (!resolvePending) {
      throw new Error("Expected pending fetch resolver to be set.");
    }
    const resolve = resolvePending as (response: Response) => void;
    resolve(jsonResponse(profilePayload));

    await expect(first).resolves.toEqual(profilePayload);
    await expect(second).resolves.toEqual(profilePayload);
  });

  it("serves school profile responses from cache inside the TTL", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(profilePayload));

    await expect(getSchoolProfile(URN)).resolves.toEqual(profilePayload);
    await expect(getSchoolProfile(URN)).resolves.toEqual(profilePayload);

    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("does not cache failed profile responses", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse({}, 503))
      .mockResolvedValueOnce(jsonResponse(profilePayload));

    await expect(getSchoolProfile(URN)).rejects.toBeInstanceOf(ApiClientError);
    await expect(getSchoolProfile(URN)).resolves.toEqual(profilePayload);

    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("prefetches profile + trends and leaves dashboard lazy for the detail page", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url =
        typeof input === "string"
          ? input
          : input instanceof URL
            ? input.toString()
            : input.url;
      if (url.endsWith("/trends/dashboard")) {
        return jsonResponse(dashboardPayload);
      }
      if (url.endsWith("/trends")) {
        return jsonResponse(trendsPayload);
      }
      return jsonResponse(profilePayload);
    });

    prefetchSchoolProfile(URN);
    await flushPromises();

    expect(fetchMock).toHaveBeenCalledTimes(2);
    await expect(getSchoolProfile(URN)).resolves.toEqual(profilePayload);
    await expect(getSchoolTrends(URN)).resolves.toEqual(trendsPayload);
    await expect(getSchoolTrendDashboard(URN)).resolves.toEqual(dashboardPayload);
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it("serializes postcode results filters into repeated query params", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse(searchPayload));

    await expect(
      searchSchools({
        postcode: "SW1A 1AA",
        radius: 5,
        phase: ["primary", "secondary"],
        sort: "ofsted"
      })
    ).resolves.toEqual(searchPayload);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(
      "/api/v1/schools?postcode=SW1A+1AA&radius=5&phase=primary&phase=secondary&sort=ofsted"
    );
  });
});
