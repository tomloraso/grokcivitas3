import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { runA11yAudit } from "../../test/accessibility";
import { renderWithProviders } from "../../test/render";
import { MapPanel } from "./MapPanel";
import type { MapMarker } from "./MapPanel";

vi.mock("./MapPanelMapLibre", () => ({
  default: ({
    center,
    markers
  }: {
    center: { lat: number; lng: number };
    markers: MapMarker[];
  }) => (
    <div data-testid="maplibre-map-mock">
      MapLibre markers: {markers.length} center: {center.lat.toFixed(4)}, {center.lng.toFixed(4)}
    </div>
  )
}));

describe("MapPanel", () => {
  it("uses default UK center when no explicit center exists", async () => {
    renderWithProviders(<MapPanel center={null} markers={[]} />);

    expect(await screen.findByTestId("maplibre-map-mock")).toHaveTextContent(
      "center: 51.5072, -0.1276"
    );
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

    expect(await screen.findByTestId("maplibre-map-mock")).toHaveTextContent(
      "MapLibre markers: 1"
    );
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
