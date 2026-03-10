import { renderHook, act } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { useResultFilters } from "./useResultFilters";
import type { SchoolSearchListItem } from "../types";

function makeSchool(overrides: Partial<SchoolSearchListItem> = {}): SchoolSearchListItem {
  return {
    urn: String(Math.random()),
    name: "Test School",
    type: "Academy",
    phase: "Primary",
    postcode: "SW1A 1AA",
    lat: 51.5,
    lng: -0.1,
    distance_miles: 1.0,
    pupil_count: 300,
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
    saved_state: {
      status: "not_saved",
      saved_at: null,
      capability_key: null,
      reason_code: null
    },
    ...overrides,
  };
}

const MIXED_SCHOOLS: SchoolSearchListItem[] = [
  makeSchool({ urn: "1", phase: "Primary", type: "Academy" }),
  makeSchool({ urn: "2", phase: "Primary", type: "Community school" }),
  makeSchool({ urn: "3", phase: "Secondary", type: "Academy" }),
  makeSchool({ urn: "4", phase: "Secondary", type: "Academy" }),
  makeSchool({ urn: "5", phase: "All through", type: "Free school" }),
];

describe("useResultFilters", () => {
  it("returns all schools when no filters active", () => {
    const { result } = renderHook(() => useResultFilters(MIXED_SCHOOLS));

    expect(result.current.filtered).toHaveLength(5);
    expect(result.current.hasActiveFilters).toBe(false);
    expect(result.current.hiddenCount).toBe(0);
  });

  it("builds phase facets sorted by count descending", () => {
    const { result } = renderHook(() => useResultFilters(MIXED_SCHOOLS));

    expect(result.current.phases).toEqual([
      { label: "Primary", count: 2, selected: false },
      { label: "Secondary", count: 2, selected: false },
      { label: "All through", count: 1, selected: false },
    ]);
  });

  it("filters by a single phase", () => {
    const { result } = renderHook(() => useResultFilters(MIXED_SCHOOLS));

    act(() => result.current.togglePhase("Primary"));

    expect(result.current.filtered).toHaveLength(2);
    expect(result.current.filtered.every((s) => s.phase === "Primary")).toBe(true);
    expect(result.current.hasActiveFilters).toBe(true);
    expect(result.current.hiddenCount).toBe(3);
  });

  it("OR-s within a facet group (multiple phases)", () => {
    const { result } = renderHook(() => useResultFilters(MIXED_SCHOOLS));

    act(() => {
      result.current.togglePhase("Primary");
      result.current.togglePhase("Secondary");
    });

    expect(result.current.filtered).toHaveLength(4);
  });

  it("deselects a toggled chip", () => {
    const { result } = renderHook(() => useResultFilters(MIXED_SCHOOLS));

    act(() => result.current.togglePhase("Primary"));
    expect(result.current.phases[0].selected).toBe(true);

    act(() => result.current.togglePhase("Primary"));
    expect(result.current.phases[0].selected).toBe(false);
    expect(result.current.filtered).toHaveLength(5);
  });

  it("clears all filters", () => {
    const { result } = renderHook(() => useResultFilters(MIXED_SCHOOLS));

    act(() => result.current.togglePhase("Primary"));
    expect(result.current.hasActiveFilters).toBe(true);

    act(() => result.current.clearFilters());
    expect(result.current.hasActiveFilters).toBe(false);
    expect(result.current.filtered).toHaveLength(5);
  });

  it("handles null phase as 'Unknown'", () => {
    const schools = [
      makeSchool({ urn: "1", phase: null }),
      makeSchool({ urn: "2", phase: "Primary" }),
    ];

    const { result } = renderHook(() => useResultFilters(schools));

    expect(result.current.phases.find((f) => f.label === "Unknown")?.count).toBe(1);

    act(() => result.current.togglePhase("Unknown"));
    expect(result.current.filtered).toHaveLength(1);
    expect(result.current.filtered[0].urn).toBe("1");
  });

  it("returns empty facets for empty schools array", () => {
    const { result } = renderHook(() => useResultFilters([]));

    expect(result.current.phases).toHaveLength(0);
    expect(result.current.filtered).toHaveLength(0);
  });
});
