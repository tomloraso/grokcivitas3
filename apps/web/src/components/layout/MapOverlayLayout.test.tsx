import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MapOverlayLayout } from "./MapOverlayLayout";

describe("MapOverlayLayout", () => {
  it("sets data-layout attribute for CSS targeting", () => {
    const { container } = render(
      <MapOverlayLayout map={<div data-testid="map" />}>
        <div data-testid="panel" />
      </MapOverlayLayout>
    );

    const root = container.firstElementChild;
    expect(root).toHaveAttribute("data-layout", "map-overlay");
  });

  it("renders map and overlay panel content", () => {
    render(
      <MapOverlayLayout map={<div data-testid="map" />}>
        <div data-testid="panel">Panel content</div>
      </MapOverlayLayout>
    );

    expect(screen.getByTestId("map")).toBeInTheDocument();
    expect(screen.getByTestId("panel")).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Map view" })).toBeInTheDocument();
  });
});
