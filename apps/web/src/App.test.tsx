import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { searchSchools } from "./api/client";
import type { SchoolsSearchResponse } from "./api/types";
import { runA11yAudit } from "./test/accessibility";
import { renderWithProviders } from "./test/render";

vi.mock("./api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./api/client")>();
  return {
    ...actual,
    searchSchools: vi.fn()
  };
});

vi.mock("./components/maps/MapPanel", () => ({
  MapPanel: ({ title, markers }: { title: string; markers: Array<{ id: string }> }) => (
    <div data-testid="map-panel-mock">
      {title}: {markers.length} markers
    </div>
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

describe("App", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the schools-search shell and baseline controls", () => {
    renderWithProviders(<App />);

    expect(screen.getByRole("heading", { name: "Civitas Schools Discovery" })).toBeInTheDocument();
    expect(screen.getByLabelText(/Postcode/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Search radius/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Search schools" })).toBeInTheDocument();
    expect(screen.getByText("Search for nearby schools by postcode to load results.")).toBeInTheDocument();
    expect(screen.getByTestId("map-panel-mock")).toHaveTextContent("Nearby schools map: 0 markers");
  });

  it("validates postcode input before submitting search", async () => {
    const user = userEvent.setup();
    renderWithProviders(<App />);

    await user.clear(screen.getByLabelText(/Postcode/i));
    await user.click(screen.getByRole("button", { name: "Search schools" }));

    expect(screen.getByText("Enter a UK postcode to search.")).toBeInTheDocument();
    expect(searchSchoolsMock).not.toHaveBeenCalled();
  });

  it("submits postcode search and renders returned schools", async () => {
    const user = userEvent.setup();
    searchSchoolsMock.mockResolvedValue(successfulSearchResponse);

    renderWithProviders(<App />);

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
    expect(screen.getByText("Nearby schools map: 2 markers")).toBeInTheDocument();
  });

  it("shows loading and empty states for a valid zero-result search", async () => {
    const user = userEvent.setup();
    let resolveSearch: (value: SchoolsSearchResponse) => void = () => undefined;
    searchSchoolsMock.mockReturnValue(
      new Promise<SchoolsSearchResponse>((resolve) => {
        resolveSearch = resolve;
      })
    );

    renderWithProviders(<App />);

    await user.click(screen.getByRole("button", { name: "Search schools" }));
    expect(screen.getByRole("status", { name: "Loading content" })).toBeInTheDocument();

    resolveSearch({
      ...successfulSearchResponse,
      count: 0,
      schools: []
    });

    expect(await screen.findByText("No schools found")).toBeInTheDocument();
    expect(
      screen.getByText("Try a wider radius or a nearby postcode to broaden the search area.")
    ).toBeInTheDocument();
  });

  it("shows recoverable error state when search fails", async () => {
    const user = userEvent.setup();
    searchSchoolsMock.mockRejectedValue(new Error("Request failed: 503"));

    renderWithProviders(<App />);

    await user.click(screen.getByRole("button", { name: "Search schools" }));

    expect(await screen.findByText("Search temporarily unavailable")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
  });

  it("supports keyboard focus and activation for form submission and retry controls", async () => {
    const user = userEvent.setup();
    searchSchoolsMock.mockRejectedValueOnce(new Error("Request failed: 503"));
    searchSchoolsMock.mockResolvedValueOnce(successfulSearchResponse);

    renderWithProviders(<App />);

    await user.tab();
    const postcodeInput = screen.getByLabelText(/Postcode/i);
    expect(postcodeInput).toHaveFocus();

    await user.clear(postcodeInput);
    await user.type(postcodeInput, "SW1A 1AA");

    await user.tab();
    expect(screen.getByLabelText(/Search radius/i)).toHaveFocus();

    await user.tab();
    const submitButton = screen.getByRole("button", { name: "Search schools" });
    expect(submitButton).toHaveFocus();

    await user.keyboard("{Enter}");

    const retryButton = await screen.findByRole("button", { name: "Try again" });
    await user.tab();
    expect(retryButton).toHaveFocus();

    await user.keyboard("{Enter}");

    await waitFor(() => {
      expect(searchSchoolsMock).toHaveBeenCalledTimes(2);
    });
    expect(await screen.findByText("Camden Bridge Primary School")).toBeInTheDocument();
  });

  it("passes accessibility smoke checks", async () => {
    const { container } = renderWithProviders(<App />);
    const results = await runA11yAudit(container);
    expect(results).toHaveNoViolations();
  });
});
