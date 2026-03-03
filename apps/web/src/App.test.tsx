import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createMemoryRouter, RouterProvider } from "react-router-dom";

import { searchSchools } from "./api/client";
import type { SchoolsSearchResponse } from "./api/types";
import { runA11yAudit } from "./test/accessibility";

vi.mock("./api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./api/client")>();
  return {
    ...actual,
    searchSchools: vi.fn()
  };
});

vi.mock("./components/maps/MapPanelChromeless", () => ({
  MapPanelChromeless: ({ markers }: { markers: Array<{ id: string }> }) => (
    <div data-testid="map-panel-mock">Chromeless map: {markers.length} markers</div>
  )
}));

const searchSchoolsMock = vi.mocked(searchSchools);

const successfulSearchResponse: SchoolsSearchResponse = {
  query: {
    postcode: "SW1A 1AA",
    radius_miles: 5
  },
  center: {
    lat: 51.501009,
    lng: -0.141588
  },
  count: 2,
  schools: [
    {
      urn: "100001",
      name: "Camden Bridge Primary School",
      type: "Community school",
      phase: "Primary",
      postcode: "NW1 8NH",
      lat: 51.5424,
      lng: -0.1418,
      distance_miles: 0.52
    },
    {
      urn: "100002",
      name: "Alden Civic Academy",
      type: "Academy sponsor led",
      phase: "Secondary",
      postcode: "NW1 5TX",
      lat: 51.5357,
      lng: -0.1299,
      distance_miles: 1.12
    }
  ]
};

/**
 * Helper to render the app at a given route using createMemoryRouter
 * with the same route tree as the real app.
 */
async function renderAppAtRoute(initialEntry = "/") {
  // Dynamic import to get the route objects from the actual route config
  const { SchoolsSearchFeature } = await import(
    "./features/schools-search/SchoolsSearchFeature"
  );
  const { NotFoundPage } = await import("./pages/NotFoundPage");
  const { RootLayout } = await import("./app/RootLayout");

  const router = createMemoryRouter(
    [
      {
        element: <RootLayout />,
        children: [
          { index: true, element: <SchoolsSearchFeature /> },
          {
            path: "schools/:urn",
            element: <div data-testid="profile-placeholder">Profile for URN</div>
          },
          { path: "*", element: <NotFoundPage /> }
        ]
      }
    ],
    { initialEntries: [initialEntry] }
  );

  return render(<RouterProvider router={router} />);
}

describe("App", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the schools-search shell and baseline controls", async () => {
    await renderAppAtRoute("/");

    expect(screen.getByRole("heading", { name: "Find schools near you" })).toBeInTheDocument();
    expect(screen.getByLabelText(/Postcode/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Search radius/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Search schools" })).toBeInTheDocument();
    expect(screen.getByText("Search for nearby schools by postcode to load results.")).toBeInTheDocument();
    expect(screen.getByTestId("map-panel-mock")).toHaveTextContent("Chromeless map: 0 markers");
  }, 15_000);

  it("renders site header with Civitas brand on all routes", async () => {
    await renderAppAtRoute("/");

    // Use aria-label rather than role="banner" — JSDOM incorrectly gives
    // the banner role to <header> elements nested inside <main>.
    expect(screen.getByLabelText("Civitas - return to home")).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Primary" })).toBeInTheDocument();
  });

  it("hides site footer on the search/map page", async () => {
    await renderAppAtRoute("/");

    expect(screen.queryByRole("contentinfo")).not.toBeInTheDocument();
  });

  it("renders site footer on non-map routes", async () => {
    await renderAppAtRoute("/schools/100001");

    expect(screen.getByRole("contentinfo")).toBeInTheDocument();
    expect(screen.getByText(/Civitas. All data sourced/)).toBeInTheDocument();
  });

  it("skip-to-content link is the first focusable element", async () => {
    await renderAppAtRoute("/");
    const user = userEvent.setup();

    await user.tab();
    const skipLink = screen.getByText("Skip to content");
    expect(skipLink).toHaveFocus();
    expect(skipLink).toHaveAttribute("href", "#main-content");
  });

  it("renders 404 page for unknown routes", async () => {
    await renderAppAtRoute("/unknown-path");

    expect(screen.getByRole("heading", { name: "Page not found" })).toBeInTheDocument();
    expect(screen.getByText("Back to search")).toBeInTheDocument();
  });

  it("renders profile route for /schools/:urn", async () => {
    await renderAppAtRoute("/schools/100001");

    expect(screen.getByTestId("profile-placeholder")).toBeInTheDocument();
  });

  it("validates postcode input before submitting search", async () => {
    const user = userEvent.setup();
    await renderAppAtRoute("/");

    await user.clear(screen.getByLabelText(/Postcode/i));
    await user.click(screen.getByRole("button", { name: "Search schools" }));

    expect(screen.getByText("Enter a UK postcode to search.")).toBeInTheDocument();
    expect(searchSchoolsMock).not.toHaveBeenCalled();
  });

  it("submits postcode search and renders returned schools with profile links", async () => {
    const user = userEvent.setup();
    searchSchoolsMock.mockResolvedValue(successfulSearchResponse);

    await renderAppAtRoute("/");

    await user.clear(screen.getByLabelText(/Postcode/i));
    await user.type(screen.getByLabelText(/Postcode/i), "SW1A 1AA");
    await user.click(screen.getByRole("button", { name: "Search schools" }));

    await waitFor(() =>
      expect(searchSchoolsMock).toHaveBeenCalledWith({
        postcode: "SW1A 1AA",
        radius: 5
      })
    );

    expect(await screen.findByText("Camden Bridge Primary School")).toBeInTheDocument();
    expect(screen.getByText("Alden Civic Academy")).toBeInTheDocument();
    expect(screen.getByTestId("map-panel-mock")).toHaveTextContent("Chromeless map: 2 markers");

    // Verify profile links are present
    const profileLinks = screen.getAllByLabelText(/View profile for/);
    expect(profileLinks).toHaveLength(2);
    expect(profileLinks[0]).toHaveAttribute("href", "/schools/100001");
    expect(profileLinks[1]).toHaveAttribute("href", "/schools/100002");
  });

  it("shows loading and empty states for a valid zero-result search", async () => {
    const user = userEvent.setup();
    let resolveSearch: (value: SchoolsSearchResponse) => void = () => undefined;
    searchSchoolsMock.mockReturnValue(
      new Promise<SchoolsSearchResponse>((resolve) => {
        resolveSearch = resolve;
      })
    );

    await renderAppAtRoute("/");

    await user.click(screen.getByRole("button", { name: "Search schools" }));
    expect(screen.getByRole("status", { name: "Loading results" })).toBeInTheDocument();

    resolveSearch({
      ...successfulSearchResponse,
      count: 0,
      schools: []
    });

    expect(await screen.findByText("No schools found")).toBeInTheDocument();
  });

  it("shows recoverable error state when search fails", async () => {
    const user = userEvent.setup();
    searchSchoolsMock.mockRejectedValue(new Error("Request failed: 503"));

    await renderAppAtRoute("/");

    await user.click(screen.getByRole("button", { name: "Search schools" }));

    expect(await screen.findByText("Search temporarily unavailable")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
  });

  it("passes accessibility smoke checks", async () => {
    const { container } = await renderAppAtRoute("/");
    const results = await runA11yAudit(container);
    expect(results).toHaveNoViolations();
  });
});

