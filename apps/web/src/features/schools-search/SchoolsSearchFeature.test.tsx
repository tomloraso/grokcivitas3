import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createMemoryRouter, RouterProvider } from "react-router-dom";

import { ThemeProvider } from "../../app/providers/ThemeProvider";
import { RootLayout } from "../../app/RootLayout";
import { AuthProvider } from "../auth/AuthProvider";
import { ANONYMOUS_SESSION } from "../auth/types";
import { searchSchools, searchSchoolsByName } from "../../api/client";
import type { SchoolsSearchResponse } from "../../api/types";
import { SchoolsSearchFeature } from "./SchoolsSearchFeature";

vi.mock("../../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../api/client")>();
  return {
    ...actual,
    searchSchools: vi.fn(),
    searchSchoolsByName: vi.fn()
  };
});

vi.mock("../../components/maps/MapPanelChromeless", () => ({
  MapPanelChromeless: ({ markers }: { markers: Array<{ id: string }> }) => (
    <div data-testid="map-panel-mock">Chromeless map: {markers.length} markers</div>
  )
}));

const searchSchoolsMock = vi.mocked(searchSchools);
const searchSchoolsByNameMock = vi.mocked(searchSchoolsByName);

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
      }
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
        children: [{ index: true, element: <SchoolsSearchFeature /> }]
      }
    ],
    { initialEntries: ["/"] }
  );

  return render(
    <ThemeProvider>
      <AuthProvider autoLoad={false} initialSession={ANONYMOUS_SESSION}>
        <RouterProvider router={router} />
      </AuthProvider>
    </ThemeProvider>
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
  });

  it("opens and closes results mode over the existing postcode search", async () => {
    const user = userEvent.setup();
    renderFeature();

    await user.type(screen.getByRole("textbox", { name: /search/i }), "SW1A 1AA");
    await user.click(screen.getByRole("button", { name: "Search schools" }));

    await waitFor(() => {
      expect(screen.getByTestId("result-summary")).toHaveTextContent("within 5 miles");
    });

    expect(searchSchoolsMock).toHaveBeenCalledTimes(1);

    await user.click(screen.getByRole("button", { name: "Results" }));

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });
    expect(screen.getByText("Results for SW1A 1AA")).toBeInTheDocument();
    expect(
      within(screen.getByRole("dialog")).queryByRole("button", { name: "Academic" })
    ).not.toBeInTheDocument();
    expect(searchSchoolsMock).toHaveBeenCalledTimes(1);

    await user.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Map" }));

    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });
  });

  it("applies primary filtering and keeps results sorting on the supported options", async () => {
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

    await user.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Primary" }));

    await waitFor(() => {
      expect(searchSchoolsMock).toHaveBeenCalledWith({
        postcode: "SW1A 1AA",
        radius: 5,
        phase: ["primary"],
        sort: "closest"
      });
    });
  });
});
