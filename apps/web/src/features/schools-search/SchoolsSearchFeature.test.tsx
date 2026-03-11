import { render, screen, waitFor, within } from "@testing-library/react";
import { HelmetProvider } from "react-helmet-async";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createMemoryRouter, RouterProvider } from "react-router-dom";

import { ThemeProvider } from "../../app/providers/ThemeProvider";
import { RootLayout } from "../../app/RootLayout";
import { AuthProvider } from "../auth/AuthProvider";
import { ANONYMOUS_SESSION } from "../auth/types";
import {
  getSchoolProfile,
  getSchoolTrendDashboard,
  getSchoolTrends,
  searchSchools,
  searchSchoolsByName,
} from "../../api/client";
import type { SchoolsSearchResponse } from "../../api/types";
import { SchoolProfileFeature } from "../school-profile/SchoolProfileFeature";
import {
  DASHBOARD_RESPONSE,
  PROFILE_RESPONSE,
  TRENDS_RESPONSE,
} from "../school-profile/testData";
import { SchoolsSearchFeature } from "./SchoolsSearchFeature";

vi.mock("../../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../api/client")>();
  return {
    ...actual,
    searchSchools: vi.fn(),
    searchSchoolsByName: vi.fn(),
    getSchoolProfile: vi.fn(),
    getSchoolTrends: vi.fn(),
    getSchoolTrendDashboard: vi.fn(),
  };
});

vi.mock("../../components/maps/MapPanelChromeless", () => ({
  MapPanelChromeless: ({ markers }: { markers: Array<{ id: string }> }) => (
    <div data-testid="map-panel-mock">Chromeless map: {markers.length} markers</div>
  )
}));

const searchSchoolsMock = vi.mocked(searchSchools);
const searchSchoolsByNameMock = vi.mocked(searchSchoolsByName);
const getSchoolProfileMock = vi.mocked(getSchoolProfile);
const getSchoolTrendsMock = vi.mocked(getSchoolTrends);
const getSchoolTrendDashboardMock = vi.mocked(getSchoolTrendDashboard);
const notSavedState = {
  status: "not_saved" as const,
  saved_at: null,
  capability_key: null,
  reason_code: null,
};

const POSTCODE_RESPONSE: SchoolsSearchResponse = {
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

function buildPostcodeResponse({
  phases = [],
  sort = "closest"
}: {
  phases?: SchoolsSearchResponse["query"]["phases"];
  sort?: SchoolsSearchResponse["query"]["sort"];
} = {}): SchoolsSearchResponse {
  return {
    ...POSTCODE_RESPONSE,
    query: {
      ...POSTCODE_RESPONSE.query,
      phases,
      sort
    }
  };
}

function renderFeature() {
  const router = createMemoryRouter(
    [
      {
        element: <RootLayout />,
        children: [
          { index: true, element: <SchoolsSearchFeature /> },
          { path: "schools/:urn", element: <SchoolProfileFeature /> },
        ]
      }
    ],
    { initialEntries: ["/"] }
  );

  return render(
    <HelmetProvider>
      <ThemeProvider>
        <AuthProvider autoLoad={false} initialSession={ANONYMOUS_SESSION}>
          <RouterProvider router={router} />
        </AuthProvider>
      </ThemeProvider>
    </HelmetProvider>
  );
}

describe("SchoolsSearchFeature", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    searchSchoolsMock.mockImplementation(async (request) =>
      buildPostcodeResponse({
        phases: request.phase ?? [],
        sort: request.sort ?? "closest"
      })
    );
    searchSchoolsByNameMock.mockResolvedValue({ count: 0, schools: [] });
    getSchoolProfileMock.mockResolvedValue(PROFILE_RESPONSE);
    getSchoolTrendsMock.mockResolvedValue(TRENDS_RESPONSE);
    getSchoolTrendDashboardMock.mockResolvedValue(DASHBOARD_RESPONSE);
  });

  it(
    "opens and closes results mode over the existing postcode search",
    async () => {
      const user = userEvent.setup();
      renderFeature();

      await user.type(screen.getByRole("textbox", { name: /search/i }), "SW1A 1AA");
      await user.click(screen.getByRole("button", { name: "Search schools" }));

      await waitFor(() => {
        expect(screen.getByTestId("result-summary")).toHaveTextContent("within 5 miles");
      });

      expect(searchSchoolsMock).toHaveBeenCalledTimes(1);
      expect(screen.getByRole("button", { name: "Save for later" })).toBeInTheDocument();

      await user.click(screen.getByRole("button", { name: "Results" }));

      await waitFor(() => {
        expect(screen.getByRole("dialog")).toBeInTheDocument();
      });
      expect(screen.getByText("Results for SW1A 1AA")).toBeInTheDocument();
      expect(
        within(screen.getByRole("dialog")).queryByRole("button", { name: "Academic" }),
      ).not.toBeInTheDocument();
      expect(searchSchoolsMock).toHaveBeenCalledTimes(1);

      await user.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Map" }));

      await waitFor(() => {
        expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
      });
    },
    10000,
  );

  it(
    "applies primary filtering and keeps results sorting on the supported options",
    async () => {
      const user = userEvent.setup();
      renderFeature();

      await user.type(screen.getByRole("textbox", { name: /search/i }), "SW1A 1AA");
      await user.click(screen.getByRole("button", { name: "Search schools" }));

      await waitFor(() => {
        expect(screen.getByTestId("result-summary")).toHaveTextContent("within 5 miles");
      });

      await user.click(screen.getByRole("button", { name: "Results" }));

      await waitFor(() => {
        expect(screen.getByRole("dialog")).toBeInTheDocument();
      });

      await user.click(
        within(screen.getByRole("dialog")).getByRole("button", { name: "Primary" }),
      );

      await waitFor(() => {
        expect(searchSchoolsMock).toHaveBeenCalledWith({
          postcode: "SW1A 1AA",
          radius: 5,
          phase: ["primary"],
          sort: "closest",
        });
      });
    },
    10000,
  );

  it(
    "opens a school profile from results mode and restores the active results state",
    async () => {
    const user = userEvent.setup();
    let holdFirstPrimaryRefresh = true;
    let capturedPrimaryRefresh = false;
    let releaseHeldPrimaryRefresh: () => void = () => {
      throw new Error("Expected the primary results refresh to be captured.");
    };

    searchSchoolsMock.mockImplementation(async (request) => {
      const phases = request.phase ?? [];
      const sort = request.sort ?? "closest";
      if (holdFirstPrimaryRefresh && sort === "closest" && phases.length === 1 && phases[0] === "primary") {
        holdFirstPrimaryRefresh = false;
        capturedPrimaryRefresh = true;
        return await new Promise<SchoolsSearchResponse>((resolve) => {
          releaseHeldPrimaryRefresh = () => resolve(buildPostcodeResponse({ phases, sort }));
        });
      }

      return buildPostcodeResponse({ phases, sort });
    });

    renderFeature();

    await user.type(screen.getByRole("textbox", { name: /search/i }), "SW1A 1AA");
    await user.click(screen.getByRole("button", { name: "Search schools" }));

    await waitFor(() => {
      expect(screen.getByTestId("result-summary")).toHaveTextContent("within 5 miles");
    });

    await user.click(screen.getByRole("button", { name: "Results" }));

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    await user.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Primary" }));

    await waitFor(() => {
      expect(searchSchoolsMock).toHaveBeenCalledWith({
        postcode: "SW1A 1AA",
        radius: 5,
        phase: ["primary"],
        sort: "closest"
      });
    });

    await user.click(
      within(screen.getByRole("dialog")).getByRole("link", {
        name: "Camden Bridge Primary School",
      }),
    );

    expect(
      await screen.findByRole("heading", { name: "Camden Bridge Primary School" })
    ).toBeInTheDocument();

    expect(capturedPrimaryRefresh).toBe(true);
    releaseHeldPrimaryRefresh();

    const resultsBreadcrumb = screen.getByRole("link", { name: "SW1A 1AA - 5 mi" });
    expect(resultsBreadcrumb).toHaveAttribute(
      "href",
      "/?view=results&sort=closest&phase=primary",
    );

    await user.click(resultsBreadcrumb);

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });
    expect(screen.getByRole("textbox", { name: /search/i })).toHaveValue("SW1A 1AA");
    expect(
      within(screen.getByRole("dialog")).getByRole("button", { name: "Primary" }),
    ).toHaveAttribute("aria-pressed", "true");
    },
    15000,
  );
});
