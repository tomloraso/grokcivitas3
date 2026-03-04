import { render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiClientError, getSchoolProfile, getSchoolTrends } from "../../api/client";
import type { SchoolProfileResponse, SchoolTrendsResponse } from "../../api/types";
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
  },
  completeness: {
    demographics: {
      status: "partial",
      reason_code: "source_not_provided",
      last_updated_at: "2026-01-31T09:00:00Z",
      years_available: null
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
    eal_pct: [{ academic_year: "2024/25", value: 8.4, delta: null, direction: null }]
  },
  completeness: {
    status: "partial",
    reason_code: "source_missing",
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
    is_graded: false,
    ungraded_outcome: "Effective safeguarding"
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
  return render(<RouterProvider router={router} />);
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

    expect(screen.getByLabelText(/Ofsted rating: Good/)).toBeInTheDocument();
    expect(screen.getByText("Graded")).toBeInTheDocument();

    expect(screen.getByText("Demographics")).toBeInTheDocument();
    expect(screen.getAllByText("17.2%").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Disadvantaged").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Some sections have partial or unavailable data right now.")).toBeInTheDocument();
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

    await screen.findByText("Trends");
    expect(screen.getByLabelText("Disadvantaged trend line")).toBeInTheDocument();
    expect(screen.getByText(/Limited history available \(2 years\)/)).toBeInTheDocument();
  });

  it("renders Ofsted timeline section with newest event first", async () => {
    profileMock.mockResolvedValue(PROFILE_RESPONSE);
    trendsMock.mockResolvedValue(TRENDS_RESPONSE);

    renderProfileAtUrn("100001");

    await screen.findByText("Ofsted Timeline");
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

    await screen.findByText("Ofsted Timeline");
    expect(screen.getByLabelText("Ofsted timeline events data is not available")).toBeInTheDocument();
    expect(screen.getByLabelText("Area deprivation context data is not available")).toBeInTheDocument();
    expect(screen.getByLabelText("Area crime context data is not available")).toBeInTheDocument();
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
        eal_pct: []
      },
      completeness: {
        status: "partial",
        reason_code: "source_missing",
        last_updated_at: "2026-01-31T09:00:00Z",
        years_available: ["2024/25"]
      }
    };
    profileMock.mockResolvedValue(PROFILE_RESPONSE);
    trendsMock.mockResolvedValue(singleYearTrends);

    renderProfileAtUrn("100001");

    await screen.findByText("Trends");
    expect(screen.getByText(/Limited history available/)).toBeInTheDocument();
    expect(
      screen.getByText("Limited history available (1 year). Trend deltas require at least 2 years of data.")
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
        eal_pct: []
      },
      completeness: {
        status: "unavailable",
        reason_code: "source_missing",
        last_updated_at: null,
        years_available: []
      }
    };
    profileMock.mockResolvedValue(PROFILE_RESPONSE);
    trendsMock.mockResolvedValue(emptyTrends);

    renderProfileAtUrn("100001");

    await screen.findByRole("heading", { name: "Camden Bridge Primary School" });
    expect(screen.getByText("No trend data available for this school.")).toBeInTheDocument();
    expect(screen.getByText("No historical years are available yet for trend analysis.")).toBeInTheDocument();
  });

  it("renders coverage notice for unsupported metrics", async () => {
    profileMock.mockResolvedValue(PROFILE_RESPONSE);
    trendsMock.mockResolvedValue(TRENDS_RESPONSE);

    renderProfileAtUrn("100001");

    await screen.findByText("Data Coverage");
    expect(screen.getByLabelText("Free School Meals (direct) data is not available")).toBeInTheDocument();
    expect(screen.getByLabelText("Ethnicity breakdown data is not available")).toBeInTheDocument();
    expect(screen.getByLabelText("Top non-English languages data is not available")).toBeInTheDocument();
  });

  it("degrades gracefully when trends fail with server error", async () => {
    profileMock.mockResolvedValue(PROFILE_RESPONSE);
    trendsMock.mockRejectedValue(new ApiClientError(503));

    renderProfileAtUrn("100001");

    expect(
      await screen.findByRole("heading", { name: "Camden Bridge Primary School" })
    ).toBeInTheDocument();
    expect(screen.getByText("Demographics")).toBeInTheDocument();
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
