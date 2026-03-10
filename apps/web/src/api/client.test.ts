import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  __resetApiRequestCacheForTests,
  __setApiAccessEpochForTests,
  ApiClientError,
  getAccountFavourites,
  getSchoolProfile,
  getSchoolTrendDashboard,
  getSchoolTrends,
  prefetchSchoolProfile,
  removeAccountFavourite,
  saveAccountFavourite,
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
    __setApiAccessEpochForTests("anonymous:none");
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

  it("varies access-sensitive cache keys by access epoch", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockImplementation(async () => jsonResponse(profilePayload));

    await expect(getSchoolProfile(URN)).resolves.toEqual(profilePayload);

    __setApiAccessEpochForTests("premium:premium_ai_analyst");
    await expect(getSchoolProfile(URN)).resolves.toEqual(profilePayload);

    expect(fetchMock).toHaveBeenCalledTimes(2);
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

  it("requests the account favourites library from the account endpoint", async () => {
    const payload = {
      access: {
        state: "available",
        capability_key: null,
        reason_code: null,
        product_codes: [],
        requires_auth: false,
        requires_purchase: false,
        school_name: null
      },
      count: 0,
      schools: []
    };
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse(payload));

    await expect(getAccountFavourites()).resolves.toEqual(payload);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/v1/account/favourites");
  });

  it("uses PUT and DELETE for favourite mutations", async () => {
    const payload = {
      status: "saved",
      saved_at: "2026-03-10T10:15:00Z",
      capability_key: null,
      reason_code: null
    };
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockImplementation(async () => jsonResponse(payload));

    await expect(saveAccountFavourite(URN)).resolves.toEqual(payload);
    await expect(removeAccountFavourite(URN)).resolves.toEqual(payload);

    expect(fetchMock).toHaveBeenCalledTimes(2);
    const [saveUrl, saveInit] = fetchMock.mock.calls[0] as [string, RequestInit];
    const [removeUrl, removeInit] = fetchMock.mock.calls[1] as [string, RequestInit];
    expect(saveUrl).toBe(`/api/v1/account/favourites/${URN}`);
    expect(saveInit.method).toBe("PUT");
    expect(removeUrl).toBe(`/api/v1/account/favourites/${URN}`);
    expect(removeInit.method).toBe("DELETE");
  });
});
