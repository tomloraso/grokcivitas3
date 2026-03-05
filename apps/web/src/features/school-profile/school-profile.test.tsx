import { render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiClientError, getSchoolProfile, getSchoolTrends } from "../../api/client";
import type { SchoolProfileResponse, SchoolTrendsResponse } from "../../api/types";
import { TooltipProvider } from "../../components/ui/Tooltip";
import { runA11yAudit } from "../../test/accessibility";
import { SchoolProfileFeature } from "./SchoolProfileFeature";

vi.mock("../../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../api/client")>();
  return {
    ...actual,
    getSchoolProfile: vi.fn(),
    getSchoolTrends: vi.fn()
  };
});

const profileMock = vi.mocked(getSchoolProfile);
const trendsMock = vi.mocked(getSchoolTrends);

const PROFILE_RESPONSE: SchoolProfileResponse = {
  school: {
    urn: "100001",
    name: "Camden Bridge Primary School",
    phase: "Primary",
    type: "Academy",
    status: "Open",
    postcode: "NW1 8NH",
    lat: 51.5424,
    lng: -0.1418
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
      status: "available",
      reason_code: null,
      last_updated_at: "2026-01-31T13:00:00Z",
      years_available: null
    }
  }
};

const TRENDS_RESPONSE: SchoolTrendsResponse = {
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

const UNGRADED_PROFILE: SchoolProfileResponse = {
  ...PROFILE_RESPONSE,
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

const DIRECT_FSM_PROFILE: SchoolProfileResponse = {
  ...PROFILE_RESPONSE,
  demographics_latest: {
    ...PROFILE_RESPONSE.demographics_latest!,
    fsm_pct: 16.9,
    coverage: {
      ...PROFILE_RESPONSE.demographics_latest!.coverage,
      fsm_supported: true
    }
  }
};

const ETHNICITY_SUPPORTED_PROFILE: SchoolProfileResponse = {
  ...PROFILE_RESPONSE,
  demographics_latest: {
    ...PROFILE_RESPONSE.demographics_latest!,
    coverage: {
      ...PROFILE_RESPONSE.demographics_latest!.coverage,
      ethnicity_supported: true
    },
    ethnicity_breakdown: [
      {
        key: "white_british",
        label: "White British",
        percentage: 49.0,
        count: 98
      },
      {
        key: "indian",
        label: "Indian",
        percentage: 7.0,
        count: 14
      }
    ]
  }
};

function renderProfileAtUrn(urn: string) {
  const router = createMemoryRouter(
    [
      {
        path: "schools/:urn",
        element: <SchoolProfileFeature />
      }
    ],
    { initialEntries: [`/schools/${urn}`] }
  );
  return render(
    <TooltipProvider>
      <RouterProvider router={router} />
    </TooltipProvider>
  );
}

describe("SchoolProfileFeature", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading state initially", async () => {
    profileMock.mockReturnValue(new Promise(() => {}));
    trendsMock.mockReturnValue(new Promise(() => {}));

    renderProfileAtUrn("100001");

    expect(screen.getAllByRole("status", { name: "Loading content" })).toHaveLength(3);
  });

  it("renders core profile before trends request resolves", async () => {
    let resolveTrends: (value: SchoolTrendsResponse) => void = () => undefined;
    const trendsPromise = new Promise<SchoolTrendsResponse>((resolve) => {
      resolveTrends = resolve;
    });
    profileMock.mockResolvedValue(PROFILE_RESPONSE);
    trendsMock.mockReturnValue(trendsPromise);

    renderProfileAtUrn("100001");

    expect(
      await screen.findByRole(
        "heading",
        { name: "Camden Bridge Primary School" },
        { timeout: 5000 }
      )
    ).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Something went wrong" })).not.toBeInTheDocument();

    resolveTrends(TRENDS_RESPONSE);
    await waitFor(() => {
      expect(screen.getByLabelText("Disadvantaged trend")).toBeInTheDocument();
    });
  });

  it("renders school profile on success", async () => {
    profileMock.mockResolvedValue(PROFILE_RESPONSE);
    trendsMock.mockResolvedValue(TRENDS_RESPONSE);

    renderProfileAtUrn("100001");

    expect(
      await screen.findByRole("heading", { name: "Camden Bridge Primary School" })
    ).toBeInTheDocument();

    expect(screen.getByText("Primary")).toBeInTheDocument();
    expect(screen.getByText("Academy")).toBeInTheDocument();
    expect(screen.getByText("NW1 8NH")).toBeInTheDocument();

    expect(screen.getAllByLabelText(/Ofsted rating: Good/).length).toBeGreaterThanOrEqual(1);

    expect(screen.getByRole("heading", { name: "Pupil Demographics" })).toBeInTheDocument();
    expect(screen.getAllByText("17.2%").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/Disadvantaged/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("School Performance")).toBeInTheDocument();
    expect(screen.getByText("Attainment 8")).toBeInTheDocument();
    expect(screen.getByText("47.2")).toBeInTheDocument();
    expect(screen.getByText("Quality of education")).toBeInTheDocument();
    expect(screen.getAllByText("Good").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Most recent 2 Jan 2026/)).toBeInTheDocument();
  });

  it("renders Ofsted ungraded state", async () => {
    profileMock.mockResolvedValue(UNGRADED_PROFILE);
    trendsMock.mockResolvedValue(TRENDS_RESPONSE);

    renderProfileAtUrn("100001");

    await waitFor(() => {
      expect(screen.getAllByText("Ungraded").length).toBeGreaterThanOrEqual(1);
    });
    expect(screen.getByText(/Effective safeguarding/)).toBeInTheDocument();
  });

  it("prefers direct FSM in the hero", async () => {
    profileMock.mockResolvedValue(DIRECT_FSM_PROFILE);
    trendsMock.mockResolvedValue(TRENDS_RESPONSE);

    renderProfileAtUrn("100001");

    await screen.findByRole("heading", { name: "Camden Bridge Primary School" });
    expect(screen.getAllByText("Free School Meals (direct)").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Current eligibility rate")).toBeInTheDocument();
    expect(
      screen.queryByText(
        "Free School Meals (direct) and Disadvantaged use different DfE definitions, so percentages can differ."
      )
    ).not.toBeInTheDocument();
  });

  it("renders not-found state for missing school", async () => {
    profileMock.mockRejectedValue(new ApiClientError(404));
    trendsMock.mockRejectedValue(new ApiClientError(404));

    renderProfileAtUrn("999999");

    expect(await screen.findByRole("heading", { name: "School not found" })).toBeInTheDocument();
    expect(screen.getByText(/999999/)).toBeInTheDocument();
    expect(screen.getByText("Back to search")).toBeInTheDocument();
  });

  it("renders error state with retry on profile server error", async () => {
    profileMock.mockRejectedValue(new Error("Request failed: 503"));
    trendsMock.mockRejectedValue(new Error("Request failed: 503"));

    renderProfileAtUrn("100001");

    expect(await screen.findByRole("heading", { name: "Something went wrong" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
  });

  it("renders trend panel with sparklines", async () => {
    profileMock.mockResolvedValue(PROFILE_RESPONSE);
    trendsMock.mockResolvedValue(TRENDS_RESPONSE);

    renderProfileAtUrn("100001");

    await screen.findByRole("heading", { name: "Pupil Demographics" });
    expect(screen.getByLabelText("Disadvantaged trend")).toBeInTheDocument();
  });

  it("renders Ofsted timeline section with newest event first", async () => {
    profileMock.mockResolvedValue(PROFILE_RESPONSE);
    trendsMock.mockResolvedValue(TRENDS_RESPONSE);

    renderProfileAtUrn("100001");

    await screen.findByText("Inspection History");
    expect(screen.getByText("11 Nov 2025")).toBeInTheDocument();
    expect(screen.getByText("10 Jan 2024")).toBeInTheDocument();
    expect(screen.getByText("Strong standard")).toBeInTheDocument();
  });

  it("renders area context sections when data is available", async () => {
    profileMock.mockResolvedValue(PROFILE_RESPONSE);
    trendsMock.mockResolvedValue(TRENDS_RESPONSE);

    renderProfileAtUrn("100001");

    await screen.findByText("Area Deprivation");
    expect(screen.getByText("IMD Decile")).toBeInTheDocument();
    expect(screen.getByText("IMD Rank")).toBeInTheDocument();
    expect(screen.getByText("IMD Score")).toBeInTheDocument();
    expect(screen.getByText("10,234")).toBeInTheDocument();
    expect(screen.getByText("22.400")).toBeInTheDocument();
    expect(screen.getByText("IDACI Score")).toBeInTheDocument();
    expect(screen.getByText("0.241")).toBeInTheDocument();

    await screen.findByText("Area Crime");
    expect(screen.getByText("486")).toBeInTheDocument();
    expect(screen.getByText("Violent Crime")).toBeInTheDocument();
    expect(screen.getByText("Total incidents (Jan 2026)")).toBeInTheDocument();
  });

  it("renders explicit unavailable states for area context and timeline", async () => {
    const unavailableProfile: SchoolProfileResponse = {
      ...PROFILE_RESPONSE,
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
        ...PROFILE_RESPONSE.completeness,
        ofsted_timeline: {
          status: "unavailable",
          reason_code: "source_missing",
          last_updated_at: null,
          years_available: null
        },
        area_deprivation: {
          status: "unavailable",
          reason_code: "not_joined_yet",
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
    profileMock.mockResolvedValue(unavailableProfile);
    trendsMock.mockResolvedValue(TRENDS_RESPONSE);

    renderProfileAtUrn("100001");

    await screen.findByText("Inspection History");
    expect(screen.getByLabelText("Ofsted timeline events data is not available")).toBeInTheDocument();
    expect(screen.getByLabelText("Area deprivation data is not available")).toBeInTheDocument();
    expect(screen.getByLabelText("Area crime context data is not available")).toBeInTheDocument();
  });

  it("renders zero-incident crime state with a coverage-gap notice", async () => {
    const zeroIncidentProfile: SchoolProfileResponse = {
      ...PROFILE_RESPONSE,
      area_context: {
        ...PROFILE_RESPONSE.area_context,
        crime: {
          radius_miles: 1,
          latest_month: "2026-01",
          total_incidents: 0,
          categories: []
        },
        coverage: {
          has_deprivation: true,
          has_crime: true,
          crime_months_available: 1
        }
      },
      completeness: {
        ...PROFILE_RESPONSE.completeness,
        area_crime: {
          status: "partial",
          reason_code: "source_coverage_gap",
          last_updated_at: "2026-01-31T13:00:00Z",
          years_available: null
        }
      }
    };
    profileMock.mockResolvedValue(zeroIncidentProfile);
    trendsMock.mockResolvedValue(TRENDS_RESPONSE);

    renderProfileAtUrn("100001");

    await screen.findByText("Area Crime");
    expect(
      screen.getByText("No incidents were recorded within this radius for the latest available month.")
    ).toBeInTheDocument();
    expect(
      screen.getByText("The source currently has limited coverage for this information.")
    ).toBeInTheDocument();
    expect(screen.getByText("Total incidents (Jan 2026)")).toBeInTheDocument();
  });

  it("renders stale-refresh notice when area crime needs recompute", async () => {
    const staleCrimeProfile: SchoolProfileResponse = {
      ...PROFILE_RESPONSE,
      area_context: {
        ...PROFILE_RESPONSE.area_context,
        crime: null,
        coverage: {
          has_deprivation: true,
          has_crime: false,
          crime_months_available: 0
        }
      },
      completeness: {
        ...PROFILE_RESPONSE.completeness,
        area_crime: {
          status: "unavailable",
          reason_code: "stale_after_school_refresh",
          last_updated_at: "2026-01-31T13:00:00Z",
          years_available: null
        }
      }
    };
    profileMock.mockResolvedValue(staleCrimeProfile);
    trendsMock.mockResolvedValue(TRENDS_RESPONSE);

    renderProfileAtUrn("100001");

    await screen.findByText("Area Crime");
    expect(
      screen.getByText("This section will refresh after the next local-area data update.")
    ).toBeInTheDocument();
  });

  it("handles single-year trend series correctly", async () => {
    const singleYearTrends: SchoolTrendsResponse = {
      ...TRENDS_RESPONSE,
      years_available: ["2024/25"],
      history_quality: {
        is_partial_history: true,
        min_years_for_delta: 2,
        years_count: 1
      },
      series: {
        disadvantaged_pct: [{ academic_year: "2024/25", value: 17.2, delta: null, direction: null }],
        sen_pct: [],
        ehcp_pct: [],
        eal_pct: [],
        first_language_english_pct: [],
        first_language_unclassified_pct: []
      },
      completeness: {
        status: "partial",
        reason_code: "insufficient_years_published",
        last_updated_at: "2026-01-31T09:00:00Z",
        years_available: ["2024/25"]
      }
    };
    profileMock.mockResolvedValue(PROFILE_RESPONSE);
    trendsMock.mockResolvedValue(singleYearTrends);

    renderProfileAtUrn("100001");

    await screen.findByRole("heading", { name: "Camden Bridge Primary School" });
    expect(screen.getByRole("heading", { name: "Pupil Demographics" })).toBeInTheDocument();
    expect(
      screen.getByText("We currently have one published year for this school.")
    ).toBeInTheDocument();
  });

  it("renders explicit empty trend state when all trend series are empty", async () => {
    const emptyTrends: SchoolTrendsResponse = {
      urn: "100001",
      years_available: [],
      history_quality: {
        is_partial_history: true,
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
        reason_code: "source_file_missing_for_year",
        last_updated_at: null,
        years_available: []
      }
    };
    profileMock.mockResolvedValue(PROFILE_RESPONSE);
    trendsMock.mockResolvedValue(emptyTrends);

    renderProfileAtUrn("100001");

    await screen.findByRole("heading", { name: "Camden Bridge Primary School" });
    expect(screen.getByRole("heading", { name: "Pupil Demographics" })).toBeInTheDocument();
    expect(
      screen.getByText("A published file for this year is not yet available for this school.")
    ).toBeInTheDocument();
  });

  it("renders coverage notice for unsupported metrics", async () => {
    profileMock.mockResolvedValue(PROFILE_RESPONSE);
    trendsMock.mockResolvedValue(TRENDS_RESPONSE);

    renderProfileAtUrn("100001");

    await screen.findByLabelText("Free School Meals (direct) data is not available");
    expect(screen.getByLabelText("Free School Meals (direct) data is not available")).toBeInTheDocument();
    expect(screen.getByLabelText("Ethnicity breakdown data is not available")).toBeInTheDocument();
    expect(screen.getByLabelText("Top non-English languages data is not available")).toBeInTheDocument();
  });

  it("renders ethnicity breakdown and hides ethnicity from coverage gaps when supported", async () => {
    profileMock.mockResolvedValue(ETHNICITY_SUPPORTED_PROFILE);
    trendsMock.mockResolvedValue(TRENDS_RESPONSE);

    renderProfileAtUrn("100001");

    await screen.findByText("Ethnicity breakdown");
    expect(screen.getByText("White British")).toBeInTheDocument();
    expect(screen.getByText("Indian")).toBeInTheDocument();

    expect(screen.getByLabelText("Free School Meals (direct) data is not available")).toBeInTheDocument();
    expect(screen.queryByLabelText("Ethnicity breakdown data is not available")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Top non-English languages data is not available")).toBeInTheDocument();
  });

  it("degrades gracefully when trends fail with server error", async () => {
    profileMock.mockResolvedValue(PROFILE_RESPONSE);
    trendsMock.mockRejectedValue(new ApiClientError(503));

    renderProfileAtUrn("100001");

    expect(
      await screen.findByRole("heading", { name: "Camden Bridge Primary School" })
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Pupil Demographics" })).toBeInTheDocument();
    expect(screen.getByLabelText("Trends data is unavailable")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Something went wrong" })).not.toBeInTheDocument();
  });

  it("passes accessibility smoke check", async () => {
    profileMock.mockResolvedValue(PROFILE_RESPONSE);
    trendsMock.mockResolvedValue(TRENDS_RESPONSE);

    const { container } = renderProfileAtUrn("100001");

    await screen.findByRole("heading", { name: "Camden Bridge Primary School" });
    const results = await runA11yAudit(container);
    expect(results).toHaveNoViolations();
  });
});
