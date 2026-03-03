import { describe, expect, it } from "vitest";

import type { SchoolProfileResponse, SchoolTrendsResponse } from "../../../api/types";
import { mapProfileToVM, fmtPct, fmtDate, fallback } from "./profileMapper";

const BASE_PROFILE: SchoolProfileResponse = {
  school: {
    urn: "100001",
    name: "Test Primary School",
    phase: "Primary",
    type: "Academy",
    status: "Open",
    postcode: "SW1A 1AA",
    lat: 51.501,
    lng: -0.1416
  },
  demographics_latest: {
    academic_year: "2024/25",
    disadvantaged_pct: 17.2,
    fsm_pct: null,
    sen_pct: 13.0,
    ehcp_pct: 2.1,
    eal_pct: 8.4,
    first_language_english_pct: 90.6,
    first_language_unclassified_pct: 1.0,
    coverage: {
      fsm_supported: false,
      ethnicity_supported: false,
      top_languages_supported: false
    }
  },
  ofsted_latest: {
    overall_effectiveness_code: "2",
    overall_effectiveness_label: "Good",
    inspection_start_date: "2025-10-10",
    publication_date: "2025-11-15",
    is_graded: true,
    ungraded_outcome: null
  },
  ofsted_timeline: {
    events: [
      {
        inspection_number: "10426708",
        inspection_start_date: "2024-01-10",
        publication_date: "2024-02-03",
        inspection_type: "Section 5",
        overall_effectiveness_label: "Good",
        headline_outcome_text: null,
        category_of_concern: null
      },
      {
        inspection_number: "10426709",
        inspection_start_date: "2025-11-11",
        publication_date: "2026-01-11",
        inspection_type: "Section 8",
        overall_effectiveness_label: null,
        headline_outcome_text: "Strong standard",
        category_of_concern: null
      }
    ],
    coverage: {
      is_partial_history: false,
      earliest_event_date: "2015-09-14",
      latest_event_date: "2026-01-15",
      events_count: 9
    }
  },
  area_context: {
    deprivation: {
      lsoa_code: "E01004736",
      imd_decile: 3,
      idaci_score: 0.241,
      idaci_decile: 2,
      source_release: "IoD2025"
    },
    crime: {
      radius_miles: 1.0,
      latest_month: "2026-01",
      total_incidents: 486,
      categories: [
        { category: "violent-crime", incident_count: 132 },
        { category: "anti-social-behaviour", incident_count: 97 }
      ]
    },
    coverage: {
      has_deprivation: true,
      has_crime: true,
      crime_months_available: 12
    }
  }
};

const BASE_TRENDS: SchoolTrendsResponse = {
  urn: "100001",
  years_available: ["2023/24", "2024/25"],
  history_quality: {
    is_partial_history: true,
    min_years_for_delta: 2,
    years_count: 2
  },
  series: {
    disadvantaged_pct: [
      { academic_year: "2023/24", value: 16.0, delta: null, direction: null },
      { academic_year: "2024/25", value: 17.2, delta: 1.2, direction: "up" }
    ],
    sen_pct: [
      { academic_year: "2023/24", value: 12.5, delta: null, direction: null },
      { academic_year: "2024/25", value: 13.0, delta: 0.5, direction: "up" }
    ],
    ehcp_pct: [{ academic_year: "2024/25", value: 2.1, delta: null, direction: null }],
    eal_pct: [{ academic_year: "2024/25", value: 8.4, delta: null, direction: null }]
  }
};

describe("fmtPct", () => {
  it("formats a number to 1dp with % suffix", () => {
    expect(fmtPct(17.2)).toBe("17.2%");
  });

  it("returns null for null input", () => {
    expect(fmtPct(null)).toBeNull();
  });

  it("handles zero", () => {
    expect(fmtPct(0)).toBe("0.0%");
  });
});

describe("fmtDate", () => {
  it("formats an ISO date to readable UK format", () => {
    const result = fmtDate("2025-10-10");
    expect(result).toMatch(/10.*Oct.*2025/);
  });

  it("returns null for null input", () => {
    expect(fmtDate(null)).toBeNull();
  });
});

describe("fallback", () => {
  it("returns the value when non-empty", () => {
    expect(fallback("Primary", "Unknown")).toBe("Primary");
  });

  it("returns placeholder for null", () => {
    expect(fallback(null, "Unknown")).toBe("Unknown");
  });

  it("returns placeholder for empty string", () => {
    expect(fallback("", "Unknown")).toBe("Unknown");
  });

  it("returns placeholder for whitespace-only string", () => {
    expect(fallback("   ", "Unknown")).toBe("Unknown");
  });
});

describe("mapProfileToVM", () => {
  it("maps school identity fields", () => {
    const vm = mapProfileToVM(BASE_PROFILE, null);
    expect(vm.school).toEqual({
      urn: "100001",
      name: "Test Primary School",
      phase: "Primary",
      type: "Academy",
      status: "Open",
      postcode: "SW1A 1AA",
      lat: 51.501,
      lng: -0.1416
    });
  });

  it("maps demographics with formatted percentages", () => {
    const vm = mapProfileToVM(BASE_PROFILE, null);
    expect(vm.demographics).not.toBeNull();
    expect(vm.demographics!.academicYear).toBe("2024/25");

    const disadvMetric = vm.demographics!.metrics.find((m) => m.metricKey === "disadvantaged_pct");
    expect(disadvMetric).toEqual({
      label: "Disadvantaged",
      value: "17.2%",
      raw: 17.2,
      metricKey: "disadvantaged_pct"
    });

    const fsmMetric = vm.demographics!.metrics.find((m) => m.metricKey === "fsm_pct");
    expect(fsmMetric!.value).toBeNull();
    expect(fsmMetric!.raw).toBeNull();
  });

  it("maps demographics coverage flags", () => {
    const vm = mapProfileToVM(BASE_PROFILE, null);
    expect(vm.demographics!.coverage).toEqual({
      fsmSupported: false,
      ethnicitySupported: false,
      topLanguagesSupported: false
    });
  });

  it("maps Ofsted headline for graded inspection", () => {
    const vm = mapProfileToVM(BASE_PROFILE, null);
    expect(vm.ofsted).not.toBeNull();
    expect(vm.ofsted!.ratingCode).toBe("2");
    expect(vm.ofsted!.ratingLabel).toBe("Good");
    expect(vm.ofsted!.isGraded).toBe(true);
    expect(vm.ofsted!.inspectionDate).toMatch(/10.*Oct.*2025/);
  });

  it("maps ungraded Ofsted inspection", () => {
    const ungraded: SchoolProfileResponse = {
      ...BASE_PROFILE,
      ofsted_latest: {
        overall_effectiveness_code: null,
        overall_effectiveness_label: null,
        inspection_start_date: "2025-06-01",
        publication_date: "2025-07-15",
        is_graded: false,
        ungraded_outcome: "Effective safeguarding"
      }
    };
    const vm = mapProfileToVM(ungraded, null);
    expect(vm.ofsted!.isGraded).toBe(false);
    expect(vm.ofsted!.ungradedOutcome).toBe("Effective safeguarding");
    expect(vm.ofsted!.ratingCode).toBeNull();
  });

  it("returns null demographics when not present", () => {
    const noDemographics: SchoolProfileResponse = {
      ...BASE_PROFILE,
      demographics_latest: null
    };
    const vm = mapProfileToVM(noDemographics, null);
    expect(vm.demographics).toBeNull();
  });

  it("returns null ofsted when not present", () => {
    const noOfsted: SchoolProfileResponse = {
      ...BASE_PROFILE,
      ofsted_latest: null
    };
    const vm = mapProfileToVM(noOfsted, null);
    expect(vm.ofsted).toBeNull();
  });

  it("returns null trends when not provided", () => {
    const vm = mapProfileToVM(BASE_PROFILE, null);
    expect(vm.trends).toBeNull();
  });

  it("maps timeline events and sorts them newest-first", () => {
    const vm = mapProfileToVM(BASE_PROFILE, null);
    expect(vm.ofstedTimeline.events).toHaveLength(2);
    expect(vm.ofstedTimeline.events[0]!.inspectionNumber).toBe("10426709");
    expect(vm.ofstedTimeline.events[1]!.inspectionNumber).toBe("10426708");
    expect(vm.ofstedTimeline.coverage.isPartialHistory).toBe(false);
    expect(vm.ofstedTimeline.coverage.earliestEventDate).toMatch(/14.*Sep.*2015/);
    expect(vm.ofstedTimeline.coverage.latestEventDate).toMatch(/15.*Jan.*2026/);
    expect(vm.ofstedTimeline.coverage.eventsCount).toBe(9);
  });

  it("maps area context with deprivation and crime summaries", () => {
    const vm = mapProfileToVM(BASE_PROFILE, null);
    expect(vm.areaContext.coverage).toEqual({
      hasDeprivation: true,
      hasCrime: true,
      crimeMonthsAvailable: 12
    });

    expect(vm.areaContext.deprivation).toEqual({
      lsoaCode: "E01004736",
      imdDecile: 3,
      idaciScore: 0.241,
      idaciDecile: 2,
      sourceRelease: "IoD2025"
    });

    expect(vm.areaContext.crime).toEqual({
      radiusMiles: 1,
      latestMonth: "Jan 2026",
      totalIncidents: 486,
      categories: [
        { category: "Violent Crime", incidentCount: 132 },
        { category: "Anti Social Behaviour", incidentCount: 97 }
      ]
    });
  });

  it("maps area context unavailable states explicitly", () => {
    const unavailable: SchoolProfileResponse = {
      ...BASE_PROFILE,
      area_context: {
        deprivation: null,
        crime: null,
        coverage: {
          has_deprivation: false,
          has_crime: false,
          crime_months_available: 0
        }
      }
    };

    const vm = mapProfileToVM(unavailable, null);
    expect(vm.areaContext.deprivation).toBeNull();
    expect(vm.areaContext.crime).toBeNull();
    expect(vm.areaContext.coverage).toEqual({
      hasDeprivation: false,
      hasCrime: false,
      crimeMonthsAvailable: 0
    });
  });

  it("maps trends with series and history quality", () => {
    const vm = mapProfileToVM(BASE_PROFILE, BASE_TRENDS);
    expect(vm.trends).not.toBeNull();
    expect(vm.trends!.isPartialHistory).toBe(true);
    expect(vm.trends!.yearsCount).toBe(2);
    expect(vm.trends!.yearsAvailable).toEqual(["2023/24", "2024/25"]);
    expect(vm.trends!.series).toHaveLength(4);
  });

  it("maps trend deltas and direction for latest point", () => {
    const vm = mapProfileToVM(BASE_PROFILE, BASE_TRENDS);
    const disadvantaged = vm.trends!.series.find((s) => s.metricKey === "disadvantaged_pct");
    expect(disadvantaged!.latestDelta).toBe(1.2);
    expect(disadvantaged!.latestDirection).toBe("up");
  });

  it("returns null delta for single-point series", () => {
    const vm = mapProfileToVM(BASE_PROFILE, BASE_TRENDS);
    const ehcp = vm.trends!.series.find((s) => s.metricKey === "ehcp_pct");
    expect(ehcp!.points).toHaveLength(1);
    expect(ehcp!.latestDelta).toBeNull();
    expect(ehcp!.latestDirection).toBeNull();
  });

  it("identifies unsupported metrics from coverage flags", () => {
    const vm = mapProfileToVM(BASE_PROFILE, null);
    expect(vm.unsupportedMetrics).toHaveLength(3);
    const labels = vm.unsupportedMetrics.map((m) => m.label);
    expect(labels).toContain("Free School Meals (direct)");
    expect(labels).toContain("Ethnicity breakdown");
    expect(labels).toContain("Top non-English languages");
  });

  it("returns empty unsupported list when demographics missing", () => {
    const noDemographics: SchoolProfileResponse = {
      ...BASE_PROFILE,
      demographics_latest: null
    };
    const vm = mapProfileToVM(noDemographics, null);
    expect(vm.unsupportedMetrics).toHaveLength(0);
  });

  it("handles school with missing optional fields using fallbacks", () => {
    const sparse: SchoolProfileResponse = {
      school: {
        urn: "999999",
        name: "Sparse School",
        phase: null,
        type: null,
        status: null,
        postcode: null,
        lat: 51.5,
        lng: -0.1
      },
      demographics_latest: null,
      ofsted_latest: null,
      ofsted_timeline: {
        events: [],
        coverage: {
          is_partial_history: true,
          earliest_event_date: null,
          latest_event_date: null,
          events_count: 0
        }
      },
      area_context: {
        deprivation: null,
        crime: null,
        coverage: {
          has_deprivation: false,
          has_crime: false,
          crime_months_available: 0
        }
      }
    };
    const vm = mapProfileToVM(sparse, null);
    expect(vm.school.phase).toBe("Unknown");
    expect(vm.school.type).toBe("Unknown");
    expect(vm.school.status).toBe("Unknown");
    expect(vm.school.postcode).toBe("Unknown");
  });
});
