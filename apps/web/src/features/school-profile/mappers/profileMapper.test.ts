import { describe, expect, it } from "vitest";

import type { SchoolProfileResponse, SchoolTrendsResponse } from "../../../api/types";
import {
  fallback,
  fmtDate,
  fmtPct,
  mapCompletenessReasonToMessageKey,
  mapProfileToVM
} from "./profileMapper";

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
    },
    ethnicity_breakdown: []
  },
  performance: {
    latest: {
      academic_year: "2024/25",
      attainment8_average: 47.2,
      progress8_average: 0.11,
      progress8_disadvantaged: -0.12,
      progress8_not_disadvantaged: 0.21,
      progress8_disadvantaged_gap: -0.33,
      engmath_5_plus_pct: 52.3,
      engmath_4_plus_pct: 71.4,
      ebacc_entry_pct: 36.2,
      ebacc_5_plus_pct: 25.5,
      ebacc_4_plus_pct: 31.3,
      ks2_reading_expected_pct: 74.1,
      ks2_writing_expected_pct: 72.8,
      ks2_maths_expected_pct: 75.4,
      ks2_combined_expected_pct: 68.9,
      ks2_reading_higher_pct: 21.3,
      ks2_writing_higher_pct: 19.4,
      ks2_maths_higher_pct: 23.7,
      ks2_combined_higher_pct: 16.8
    },
    history: [
      {
        academic_year: "2023/24",
        attainment8_average: 46.1,
        progress8_average: 0.05,
        progress8_disadvantaged: -0.19,
        progress8_not_disadvantaged: 0.16,
        progress8_disadvantaged_gap: -0.35,
        engmath_5_plus_pct: 50.1,
        engmath_4_plus_pct: 69.8,
        ebacc_entry_pct: 35.0,
        ebacc_5_plus_pct: 24.2,
        ebacc_4_plus_pct: 30.1,
        ks2_reading_expected_pct: 73.2,
        ks2_writing_expected_pct: 71.9,
        ks2_maths_expected_pct: 74.5,
        ks2_combined_expected_pct: 67.8,
        ks2_reading_higher_pct: 20.8,
        ks2_writing_higher_pct: 18.7,
        ks2_maths_higher_pct: 22.6,
        ks2_combined_higher_pct: 15.9
      },
      {
        academic_year: "2024/25",
        attainment8_average: 47.2,
        progress8_average: 0.11,
        progress8_disadvantaged: -0.12,
        progress8_not_disadvantaged: 0.21,
        progress8_disadvantaged_gap: -0.33,
        engmath_5_plus_pct: 52.3,
        engmath_4_plus_pct: 71.4,
        ebacc_entry_pct: 36.2,
        ebacc_5_plus_pct: 25.5,
        ebacc_4_plus_pct: 31.3,
        ks2_reading_expected_pct: 74.1,
        ks2_writing_expected_pct: 72.8,
        ks2_maths_expected_pct: 75.4,
        ks2_combined_expected_pct: 68.9,
        ks2_reading_higher_pct: 21.3,
        ks2_writing_higher_pct: 19.4,
        ks2_maths_higher_pct: 23.7,
        ks2_combined_higher_pct: 16.8
      }
    ]
  },
  ofsted_latest: {
    overall_effectiveness_code: "2",
    overall_effectiveness_label: "Good",
    inspection_start_date: "2025-10-10",
    publication_date: "2025-11-15",
    latest_oeif_inspection_start_date: "2025-10-10",
    latest_oeif_publication_date: "2025-11-15",
    quality_of_education_code: "2",
    quality_of_education_label: "Good",
    behaviour_and_attitudes_code: "2",
    behaviour_and_attitudes_label: "Good",
    personal_development_code: "2",
    personal_development_label: "Good",
    leadership_and_management_code: "2",
    leadership_and_management_label: "Good",
    latest_ungraded_inspection_date: "2026-01-02",
    latest_ungraded_publication_date: "2026-01-20",
    most_recent_inspection_date: "2026-01-02",
    days_since_most_recent_inspection: 61,
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
      imd_score: 22.4,
      imd_rank: 10234,
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
  },
  completeness: {
    demographics: {
      status: "partial",
      reason_code: "partial_metric_coverage",
      last_updated_at: "2026-01-31T09:00:00Z",
      years_available: null
    },
    performance: {
      status: "partial",
      reason_code: "insufficient_years_published",
      last_updated_at: "2026-01-31T09:00:00Z",
      years_available: ["2023/24", "2024/25"]
    },
    ofsted_latest: {
      status: "available",
      reason_code: null,
      last_updated_at: "2026-01-20T10:00:00Z",
      years_available: null
    },
    ofsted_timeline: {
      status: "available",
      reason_code: null,
      last_updated_at: "2026-01-18T11:00:00Z",
      years_available: null
    },
    area_deprivation: {
      status: "available",
      reason_code: null,
      last_updated_at: "2026-01-10T12:00:00Z",
      years_available: null
    },
    area_crime: {
      status: "partial",
      reason_code: "source_coverage_gap",
      last_updated_at: "2026-01-31T13:00:00Z",
      years_available: null
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
    eal_pct: [{ academic_year: "2024/25", value: 8.4, delta: null, direction: null }],
    first_language_english_pct: [
      { academic_year: "2023/24", value: 89.9, delta: null, direction: null },
      { academic_year: "2024/25", value: 90.6, delta: 0.7, direction: "up" }
    ],
    first_language_unclassified_pct: [
      { academic_year: "2023/24", value: 0.6, delta: null, direction: null },
      { academic_year: "2024/25", value: 1.0, delta: 0.4, direction: "up" }
    ]
  },
  completeness: {
    status: "partial",
    reason_code: "insufficient_years_published",
    last_updated_at: "2026-01-31T09:00:00Z",
    years_available: ["2023/24", "2024/25"]
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

describe("mapCompletenessReasonToMessageKey", () => {
  it("maps backend reason codes to stable UI message keys", () => {
    expect(mapCompletenessReasonToMessageKey("source_missing")).toBe("missing");
    expect(mapCompletenessReasonToMessageKey("insufficient_years_published")).toBe(
      "insufficientYearsPublished"
    );
    expect(mapCompletenessReasonToMessageKey("source_not_in_catalog")).toBe("sourceNotInCatalog");
    expect(mapCompletenessReasonToMessageKey("source_file_missing_for_year")).toBe(
      "sourceFileMissingForYear"
    );
    expect(mapCompletenessReasonToMessageKey("source_schema_incompatible_for_year")).toBe(
      "sourceSchemaIncompatibleForYear"
    );
    expect(mapCompletenessReasonToMessageKey("partial_metric_coverage")).toBe(
      "partialMetricCoverage"
    );
    expect(mapCompletenessReasonToMessageKey("source_not_provided")).toBe("notProvided");
    expect(mapCompletenessReasonToMessageKey("rejected_by_validation")).toBe("validationRejected");
    expect(mapCompletenessReasonToMessageKey("not_joined_yet")).toBe("notJoinedYet");
    expect(mapCompletenessReasonToMessageKey("pipeline_failed_recently")).toBe(
      "pipelineFailedRecently"
    );
    expect(mapCompletenessReasonToMessageKey("not_applicable")).toBe("notApplicable");
    expect(mapCompletenessReasonToMessageKey("source_coverage_gap")).toBe("sourceCoverageGap");
    expect(mapCompletenessReasonToMessageKey("stale_after_school_refresh")).toBe(
      "staleAfterSchoolRefresh"
    );
    expect(mapCompletenessReasonToMessageKey("no_incidents_in_radius")).toBe(
      "noIncidentsInRadius"
    );
    expect(mapCompletenessReasonToMessageKey(null)).toBeNull();
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
    expect(vm.demographics!.ethnicityBreakdown).toEqual([]);
  });

  it("maps ethnicity breakdown rows when payload is present", () => {
    const withEthnicity: SchoolProfileResponse = {
      ...BASE_PROFILE,
      demographics_latest: {
        ...BASE_PROFILE.demographics_latest!,
        coverage: {
          fsm_supported: false,
          ethnicity_supported: true,
          top_languages_supported: false
        },
        ethnicity_breakdown: [
          {
            key: "white_british",
            label: "White British",
            percentage: 49.0,
            count: 98
          },
          {
            key: "unclassified",
            label: "Unclassified",
            percentage: 4.0,
            count: 8
          }
        ]
      }
    };
    const vm = mapProfileToVM(withEthnicity, null);
    expect(vm.demographics!.ethnicityBreakdown).toEqual([
      {
        key: "white_british",
        label: "White British",
        percentage: 49,
        count: 98,
        percentageLabel: "49.0%"
      },
      {
        key: "unclassified",
        label: "Unclassified",
        percentage: 4,
        count: 8,
        percentageLabel: "4.0%"
      }
    ]);
  });

  it("maps Ofsted headline for graded inspection", () => {
    const vm = mapProfileToVM(BASE_PROFILE, null);
    expect(vm.ofsted).not.toBeNull();
    expect(vm.ofsted!.ratingCode).toBe("2");
    expect(vm.ofsted!.ratingLabel).toBe("Good");
    expect(vm.ofsted!.isGraded).toBe(true);
    expect(vm.ofsted!.inspectionDate).toMatch(/10.*Oct.*2025/);
    expect(vm.ofsted!.qualityOfEducationLabel).toBe("Good");
    expect(vm.ofsted!.behaviourAndAttitudesLabel).toBe("Good");
    expect(vm.ofsted!.daysSinceMostRecentInspection).toBe(61);
    expect(vm.ofsted!.mostRecentInspectionDate).toMatch(/2.*Jan.*2026/);
  });

  it("maps performance latest and history rows", () => {
    const vm = mapProfileToVM(BASE_PROFILE, null);
    expect(vm.performance).not.toBeNull();
    expect(vm.performance!.latest?.attainment8Average).toBe(47.2);
    expect(vm.performance!.latest?.engmath5PlusPct).toBe(52.3);
    expect(vm.performance!.history).toHaveLength(2);
    expect(vm.performance!.history[0]?.academicYear).toBe("2023/24");
  });

  it("maps ungraded Ofsted inspection", () => {
    const ungraded: SchoolProfileResponse = {
      ...BASE_PROFILE,
      ofsted_latest: {
        overall_effectiveness_code: null,
        overall_effectiveness_label: null,
        inspection_start_date: "2025-06-01",
        publication_date: "2025-07-15",
        latest_oeif_inspection_start_date: null,
        latest_oeif_publication_date: null,
        quality_of_education_code: null,
        quality_of_education_label: null,
        behaviour_and_attitudes_code: null,
        behaviour_and_attitudes_label: null,
        personal_development_code: null,
        personal_development_label: null,
        leadership_and_management_code: null,
        leadership_and_management_label: null,
        latest_ungraded_inspection_date: "2025-06-01",
        latest_ungraded_publication_date: "2025-07-15",
        most_recent_inspection_date: "2025-06-01",
        days_since_most_recent_inspection: 30,
        is_graded: false,
        ungraded_outcome: "Effective safeguarding"
      }
    };
    const vm = mapProfileToVM(ungraded, null);
    expect(vm.ofsted!.isGraded).toBe(false);
    expect(vm.ofsted!.ungradedOutcome).toBe("Effective safeguarding");
    expect(vm.ofsted!.ratingCode).toBeNull();
    expect(vm.ofsted!.daysSinceMostRecentInspection).toBe(30);
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
      imdScore: 22.4,
      imdRank: 10234,
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
      },
      completeness: {
        demographics: {
          status: "unavailable",
          reason_code: "source_file_missing_for_year",
          last_updated_at: null,
          years_available: null
        },
        performance: {
          status: "unavailable",
          reason_code: "source_missing",
          last_updated_at: null,
          years_available: null
        },
        ofsted_latest: {
          status: "unavailable",
          reason_code: "source_missing",
          last_updated_at: null,
          years_available: null
        },
        ofsted_timeline: {
          status: "unavailable",
          reason_code: "source_missing",
          last_updated_at: null,
          years_available: null
        },
        area_deprivation: {
          status: "unavailable",
          reason_code: "not_applicable",
          last_updated_at: null,
          years_available: null
        },
        area_crime: {
          status: "unavailable",
          reason_code: "not_joined_yet",
          last_updated_at: null,
          years_available: null
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
    expect(vm.trends!.series).toHaveLength(6);
  });

  it("maps profile and trends completeness metadata", () => {
    const vm = mapProfileToVM(BASE_PROFILE, BASE_TRENDS);

    expect(vm.completeness.demographics.status).toBe("partial");
    expect(vm.completeness.demographics.messageKey).toBe("partialMetricCoverage");
    expect(vm.completeness.demographics.lastUpdatedAt).toMatch(/31.*Jan.*2026/);
    expect(vm.completeness.performance.status).toBe("partial");
    expect(vm.completeness.performance.messageKey).toBe("insufficientYearsPublished");

    expect(vm.completeness.areaCrime.status).toBe("partial");
    expect(vm.completeness.areaCrime.messageKey).toBe("sourceCoverageGap");

    expect(vm.completeness.trends.status).toBe("partial");
    expect(vm.completeness.trends.messageKey).toBe("insufficientYearsPublished");
    expect(vm.completeness.trends.yearsAvailable).toEqual(["2023/24", "2024/25"]);
  });

  it("marks trends as temporarily unavailable when trends payload is missing", () => {
    const vm = mapProfileToVM(BASE_PROFILE, null);
    expect(vm.completeness.trends.status).toBe("unavailable");
    expect(vm.completeness.trends.messageKey).toBe("pipelineFailedRecently");
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

  it("does not flag ethnicity as unsupported when ethnicity rows exist", () => {
    const withEthnicityRows: SchoolProfileResponse = {
      ...BASE_PROFILE,
      demographics_latest: {
        ...BASE_PROFILE.demographics_latest!,
        coverage: {
          fsm_supported: false,
          ethnicity_supported: false,
          top_languages_supported: false
        },
        ethnicity_breakdown: [
          {
            key: "white_british",
            label: "White British",
            percentage: 49.0,
            count: 98
          }
        ]
      }
    };

    const vm = mapProfileToVM(withEthnicityRows, null);
    const labels = vm.unsupportedMetrics.map((m) => m.label);
    expect(labels).toContain("Free School Meals (direct)");
    expect(labels).not.toContain("Ethnicity breakdown");
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
      performance: null,
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
      },
      completeness: {
        demographics: {
          status: "unavailable",
          reason_code: "source_file_missing_for_year",
          last_updated_at: null,
          years_available: null
        },
        performance: {
          status: "unavailable",
          reason_code: "source_missing",
          last_updated_at: null,
          years_available: null
        },
        ofsted_latest: {
          status: "unavailable",
          reason_code: "source_missing",
          last_updated_at: null,
          years_available: null
        },
        ofsted_timeline: {
          status: "unavailable",
          reason_code: "source_missing",
          last_updated_at: null,
          years_available: null
        },
        area_deprivation: {
          status: "unavailable",
          reason_code: "not_applicable",
          last_updated_at: null,
          years_available: null
        },
        area_crime: {
          status: "unavailable",
          reason_code: "not_joined_yet",
          last_updated_at: null,
          years_available: null
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
