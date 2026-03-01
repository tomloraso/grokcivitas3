import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { runA11yAudit } from "../../test/accessibility";
import { renderWithProviders } from "../../test/render";
import { MapPanel } from "./MapPanel";

vi.mock("./MapPanelLeaflet", () => ({
  default: ({ markers }: { markers: Array<{ id: string }> }) => (
    <div data-testid="leaflet-map-mock">Leaflet markers: {markers.length}</div>
  )
}));

describe("MapPanel", () => {
  it("shows guidance message when no map center exists yet", () => {
    renderWithProviders(<MapPanel center={null} markers={[]} />);

    expect(
      screen.getByText("Search results will appear here once a postcode is resolved.")
    ).toBeInTheDocument();
    expect(screen.getByText("0 markers")).toBeInTheDocument();
  });

  it("renders the lazy map view when center and markers are provided", async () => {
    renderWithProviders(
      <MapPanel
        center={{ lat: 51.5, lng: -0.12 }}
        markers={[
          {
            id: "school-1",
            lat: 51.5,
            lng: -0.12,
            label: "Camden Bridge Primary",
            distanceMiles: 0.52
          }
        ]}
      />
    );

    expect(await screen.findByTestId("leaflet-map-mock")).toHaveTextContent("Leaflet markers: 1");
    expect(screen.getByText("1 markers")).toBeInTheDocument();
  });

  it("passes accessibility smoke checks for map panel chrome", async () => {
    const { container } = renderWithProviders(
      <MapPanel center={null} markers={[]} title="Nearby schools map" />
    );

    const results = await runA11yAudit(container);
    expect(results).toHaveNoViolations();
  });
});
