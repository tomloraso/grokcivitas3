import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiClientError, searchSchools, searchSchoolsByName } from "../../../api/client";
import type { SchoolNameSearchResponse, SchoolsSearchResponse } from "../../../api/types";
import { useSchoolsSearch } from "./useSchoolsSearch";

vi.mock("../../../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../../api/client")>();
  return {
    ...actual,
    searchSchools: vi.fn(),
    searchSchoolsByName: vi.fn()
  };
});

const searchSchoolsMock = vi.mocked(searchSchools);
const searchSchoolsByNameMock = vi.mocked(searchSchoolsByName);

const postcodeResponse: SchoolsSearchResponse = {
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
      }
    }
  ]
};

const nameResponse: SchoolNameSearchResponse = {
  count: 1,
  schools: [
    {
      urn: "136655",
      name: "Congleton High School",
      type: "Academy converter",
      phase: "Secondary",
      postcode: "CW12 4NS",
      lat: 53.4628,
      lng: -2.2406,
      distance_miles: 0
    }
  ]
};

describe("useSchoolsSearch", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("validates empty submit and does not call APIs", async () => {
    const { result } = renderHook(() => useSchoolsSearch());

    await act(async () => {
      await result.current.submitSearch();
    });

    expect(result.current.form.searchError).toBe("Enter a UK postcode or school name to search.");
    expect(searchSchoolsMock).not.toHaveBeenCalled();
    expect(searchSchoolsByNameMock).not.toHaveBeenCalled();
  });

  it("submits postcode search and stores postcode-mode result", async () => {
    searchSchoolsMock.mockResolvedValue(postcodeResponse);
    const { result } = renderHook(() => useSchoolsSearch());

    act(() => {
      result.current.setSearchText("SW1A 1AA");
    });

    await act(async () => {
      await result.current.submitSearch();
    });

    expect(searchSchoolsMock).toHaveBeenCalledWith({ postcode: "SW1A 1AA", radius: 5 });
    expect(result.current.state.status).toBe("success");
    expect(result.current.state.result?.mode).toBe("postcode");
    if (result.current.state.result?.mode !== "postcode") {
      throw new Error("Expected postcode search result");
    }
    expect(result.current.state.result.query.postcode).toBe("SW1A 1AA");
  });

  it("submits name search and stores name-mode result with query", async () => {
    searchSchoolsByNameMock.mockResolvedValue(nameResponse);
    const { result } = renderHook(() => useSchoolsSearch());

    act(() => {
      result.current.setSearchText("congleton high school");
    });

    await act(async () => {
      await result.current.submitSearch();
    });

    await waitFor(() => {
      expect(searchSchoolsByNameMock).toHaveBeenCalledWith("congleton high school");
    });
    expect(result.current.state.status).toBe("success");
    expect(result.current.state.result?.mode).toBe("name");
    if (result.current.state.result?.mode !== "name") {
      throw new Error("Expected name search result");
    }
    expect(result.current.state.result.nameQuery).toBe("congleton high school");
  });

  it("clears stale postcode results when switching to name mode and shows name-specific errors", async () => {
    searchSchoolsMock.mockResolvedValue(postcodeResponse);
    searchSchoolsByNameMock.mockRejectedValue(new ApiClientError(404));
    const { result } = renderHook(() => useSchoolsSearch());

    act(() => {
      result.current.setSearchText("SW1A 1AA");
    });

    await act(async () => {
      await result.current.submitSearch();
    });

    expect(result.current.state.result?.mode).toBe("postcode");

    act(() => {
      result.current.setSearchText("congleton high school");
    });

    expect(result.current.state.result).toBeNull();

    await act(async () => {
      await result.current.submitSearch();
    });

    expect(result.current.state.status).toBe("error");
    expect(result.current.state.result).toBeNull();
    expect(result.current.state.errorMessage).toBe("School name search failed. Please try again.");
  });
});
