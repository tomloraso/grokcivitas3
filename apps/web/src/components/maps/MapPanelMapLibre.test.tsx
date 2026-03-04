import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { renderWithProviders } from "../../test/render";
import MapPanelMapLibre from "./MapPanelMapLibre";
import type { MapMarker } from "./MapPanel";

vi.mock("maplibre-gl", () => ({
  default: {
    addProtocol: vi.fn(),
  },
}));

vi.mock("pmtiles", () => ({
  Protocol: class MockProtocol {
    tile = vi.fn();
  },
}));

vi.mock("@turf/circle", () => ({
  default: vi.fn(() => ({
    type: "Feature",
    geometry: { type: "Polygon", coordinates: [] },
    properties: {},
  })),
}));

vi.mock("../../shared/hooks/useReducedMotion", () => ({
  useReducedMotion: () => true,
}));

vi.mock("react-map-gl/maplibre", async () => {
  const React = await import("react");

  const MapMock = React.forwardRef<HTMLDivElement, Record<string, unknown>>(function MapMock(
    props,
    ref
  ) {
    void ref;
    const interactiveLayerIds = Array.isArray(props.interactiveLayerIds)
      ? (props.interactiveLayerIds as string[]).join(",")
      : "";

    return (
      <div data-testid="map-mock" data-interactive-layer-ids={interactiveLayerIds}>
        <button
          type="button"
          data-testid="map-mock-zoom-14"
          onClick={() =>
            (props.onMove as ((event: { viewState: { longitude: number; latitude: number; zoom: number } }) => void) | undefined)?.({
              viewState: {
                longitude: props.longitude as number,
                latitude: props.latitude as number,
                zoom: 14,
              },
            })
          }
        >
          zoom
        </button>
        {props.children as React.ReactNode}
      </div>
    );
  });

  function SourceMock({
    id,
    children,
  }: {
    id: string;
    children?: React.ReactNode;
  }): JSX.Element {
    return <div data-testid={`source-${id}`}>{children}</div>;
  }

  function LayerMock({
    id,
    maxzoom,
  }: {
    id: string;
    maxzoom?: number;
  }): JSX.Element {
    return <div data-testid={`layer-${id}`} data-maxzoom={maxzoom ?? ""} />;
  }

  function MarkerMock({ children }: { children?: React.ReactNode }): JSX.Element {
    return <div data-testid="map-marker">{children}</div>;
  }

  function PopupMock({ children }: { children?: React.ReactNode }): JSX.Element {
    return <div data-testid="map-popup">{children}</div>;
  }

  function NavigationControlMock(): JSX.Element {
    return <div data-testid="nav-control" />;
  }

  return {
    __esModule: true,
    default: MapMock,
    Source: SourceMock,
    Layer: LayerMock,
    Marker: MarkerMock,
    Popup: PopupMock,
    NavigationControl: NavigationControlMock,
  };
});

const MARKERS: MapMarker[] = [
  {
    id: "100001",
    lat: 53.4244,
    lng: -2.2505,
    label: "Lancasterian School",
    phase: "Not applicable",
    distanceMiles: 1.2,
  },
  {
    id: "100002",
    lat: 53.4262,
    lng: -2.2484,
    label: "The Birches School",
    phase: "Not applicable",
    distanceMiles: 1.34,
  },
];

describe("MapPanelMapLibre", () => {
  it("renders unclustered singleton layer at search zoom and keeps it interactive", () => {
    renderWithProviders(
      <MapPanelMapLibre
        center={{ lat: 53.407377, lng: -2.255712 }}
        radiusMiles={5}
        markers={MARKERS}
      />
    );

    expect(screen.getByTestId("layer-unclustered-schools")).toBeInTheDocument();
    expect(screen.getByTestId("layer-unclustered-schools")).toHaveAttribute("data-maxzoom", "14");
    expect(screen.getByTestId("map-mock")).toHaveAttribute(
      "data-interactive-layer-ids",
      "clusters,unclustered-schools"
    );
    expect(screen.queryAllByTestId("map-marker")).toHaveLength(0);
  });

  it("renders React markers at zoom 14 to avoid the previous zoom gap", async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <MapPanelMapLibre
        center={{ lat: 53.407377, lng: -2.255712 }}
        radiusMiles={5}
        markers={MARKERS}
      />
    );

    await user.click(screen.getByTestId("map-mock-zoom-14"));

    await waitFor(() => {
      expect(screen.getAllByTestId("map-marker")).toHaveLength(2);
    });
  });
});
