import { renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { searchSchools } from "../../../api/client";
import type { SchoolsSearchResponse } from "../../../api/types";
import { useResultsMode } from "./useResultsMode";
import type { PostcodeSearchResult } from "../types";

vi.mock("../../../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../../api/client")>();
  return {
    ...actual,
    searchSchools: vi.fn()
  };
});

const searchSchoolsMock = vi.mocked(searchSchools);
const notSavedState = {
  status: "not_saved" as const,
  saved_at: null,
  capability_key: null,
  reason_code: null,
};

const BASE_RESULT: PostcodeSearchResult = {
  mode: "postcode",
  query: {
    postcode: "SW1A 1AA",
    radius_miles: 5,
    phases: [],
    sort: "closest"
  },
  center: {
    lat: 51.501009,
    lng: -0.141588
  },
  count: 1,
  schools: [
    {
      urn: "100001",
      name: "Camden Bridge Primary School",
      type: "Community school",
      phase: "Primary",
      postcode: "NW1 8NH",
      lat: 51.5424,
      lng: -0.1418,
      distance_miles: 0.52,
      pupil_count: 420,
      latest_ofsted: {
        label: "Good",
        sort_rank: 2,
        availability: "published"
      },
      academic_metric: {
        metric_key: "ks2_combined_expected_pct",
        label: "KS2 expected standard",
        display_value: "67%",
        sort_value: 67,
        availability: "published"
      },
      saved_state: notSavedState
    }
  ]
};

const PRIMARY_ACADEMIC_RESPONSE: SchoolsSearchResponse = {
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
  count: 1,
  schools: [
    {
      urn: "100001",
      name: "Camden Bridge Primary School",
      type: "Community school",
      phase: "Primary",
      postcode: "NW1 8NH",
      lat: 51.5424,
      lng: -0.1418,
      distance_miles: 0.52,
      pupil_count: 420,
      latest_ofsted: {
        label: "Good",
        sort_rank: 2,
        availability: "published"
      },
      academic_metric: {
        metric_key: "ks2_combined_expected_pct",
        label: "KS2 expected standard",
        display_value: "67%",
        sort_value: 67,
        availability: "published"
      },
      saved_state: notSavedState
    }
  ]
};

describe("useResultsMode", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("reuses the base postcode result for the default results query", async () => {
    const { result } = renderHook(() =>
      useResultsMode({
        baseResult: BASE_RESULT,
        isOpen: true,
        phases: [],
        sort: "closest"
      })
    );

    await waitFor(() => {
      expect(result.current.status).toBe("success");
    });

    expect(searchSchoolsMock).not.toHaveBeenCalled();
    expect(result.current.result).toEqual(BASE_RESULT);
  });

  it("fetches results variants when phase filters or sort change", async () => {
    searchSchoolsMock.mockResolvedValue(PRIMARY_ACADEMIC_RESPONSE);

    const { result } = renderHook(() =>
      useResultsMode({
        baseResult: BASE_RESULT,
        isOpen: true,
        phases: ["primary"],
        sort: "academic"
      })
    );

    await waitFor(() => {
      expect(searchSchoolsMock).toHaveBeenCalledWith({
        postcode: "SW1A 1AA",
        radius: 5,
        phase: ["primary"],
        sort: "academic"
      });
    });

    await waitFor(() => {
      expect(result.current.status).toBe("success");
    });
    expect(result.current.result?.mode).toBe("postcode");
    expect(result.current.result?.query.phases).toEqual(["primary"]);
    expect(result.current.result?.query.sort).toBe("academic");
  });
});
