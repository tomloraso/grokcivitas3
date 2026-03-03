import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { MapOverlayLayout } from "./MapOverlayLayout";

// Helper to control matchMedia mock per test
function setMobile(mobile: boolean): void {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      media: query,
      matches: mobile,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
}

afterEach(() => {
  localStorage.clear();
  setMobile(false);
});

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

  describe("desktop collapse/expand", () => {
    it("starts expanded and can collapse", () => {
      render(
        <MapOverlayLayout map={<div />}>
          <p>Panel content</p>
        </MapOverlayLayout>
      );

      const panel = screen.getByRole("region", { name: "Results panel" });
      expect(panel).toBeVisible();
      expect(screen.getByText("Panel content")).toBeInTheDocument();

      // Click collapse button
      const collapseBtn = screen.getByRole("button", { name: "Collapse results panel" });
      fireEvent.click(collapseBtn);

      // Now aria label switches to "Expand"
      expect(screen.getByRole("button", { name: "Expand results panel" })).toBeInTheDocument();
      // Content should be hidden in collapsed state
      expect(screen.queryByText("Panel content")).not.toBeInTheDocument();
    });

    it("persists collapsed state to localStorage", () => {
      render(
        <MapOverlayLayout map={<div />}>
          <p>Panel content</p>
        </MapOverlayLayout>
      );

      const collapseBtn = screen.getByRole("button", { name: "Collapse results panel" });
      fireEvent.click(collapseBtn);

      expect(localStorage.getItem("civitas:panel-collapsed")).toBe("true");
    });

    it("shows summary in collapsed rail", () => {
      render(
        <MapOverlayLayout map={<div />} summary={<span data-testid="summary">5 schools</span>}>
          <p>Panel content</p>
        </MapOverlayLayout>
      );

      const collapseBtn = screen.getByRole("button", { name: "Collapse results panel" });
      fireEvent.click(collapseBtn);

      expect(screen.getByTestId("summary")).toBeInTheDocument();
    });

    it("announces state change to screen readers", () => {
      render(
        <MapOverlayLayout map={<div />}>
          <p>Content</p>
        </MapOverlayLayout>
      );

      // Expanded state announced
      expect(screen.getByText("Results panel expanded")).toBeInTheDocument();

      fireEvent.click(screen.getByRole("button", { name: "Collapse results panel" }));
      expect(screen.getByText("Results panel collapsed")).toBeInTheDocument();
    });
  });

  describe("mobile bottom-sheet", () => {
    it("renders bottom-sheet with drag handle on mobile", () => {
      setMobile(true);
      render(
        <MapOverlayLayout map={<div data-testid="map" />}>
          <p>Mobile content</p>
        </MapOverlayLayout>
      );

      expect(screen.getByText("Mobile content")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Expand results panel" })).toBeInTheDocument();
    });

    it("toggles between peek and expanded", () => {
      setMobile(true);
      render(
        <MapOverlayLayout map={<div />}>
          <p>Sheet content</p>
        </MapOverlayLayout>
      );

      // Starts in peek — button should say Expand
      const expandBtn = screen.getByRole("button", { name: "Expand results panel" });
      fireEvent.click(expandBtn);

      // Now in expanded — button should say Collapse
      expect(screen.getByRole("button", { name: "Collapse results panel" })).toBeInTheDocument();
    });

    it("announces sheet mode to screen readers", () => {
      setMobile(true);
      render(
        <MapOverlayLayout map={<div />}>
          <p>Content</p>
        </MapOverlayLayout>
      );

      expect(screen.getByText("Results panel collapsed")).toBeInTheDocument();

      fireEvent.click(screen.getByRole("button", { name: "Expand results panel" }));
      expect(screen.getByText("Results panel expanded")).toBeInTheDocument();
    });
  });

  describe("scroll shadows", () => {
    it("renders scroll shadow elements", () => {
      const { container } = render(
        <MapOverlayLayout map={<div />}>
          <p>Content</p>
        </MapOverlayLayout>
      );

      const topShadow = container.querySelector(".scroll-shadow-top");
      const bottomShadow = container.querySelector(".scroll-shadow-bottom");
      expect(topShadow).toBeInTheDocument();
      expect(bottomShadow).toBeInTheDocument();
    });

    it("scroll shadows start hidden", () => {
      const { container } = render(
        <MapOverlayLayout map={<div />}>
          <p>Content</p>
        </MapOverlayLayout>
      );

      const topShadow = container.querySelector(".scroll-shadow-top");
      const bottomShadow = container.querySelector(".scroll-shadow-bottom");
      expect(topShadow).toHaveAttribute("data-visible", "false");
      expect(bottomShadow).toHaveAttribute("data-visible", "false");
    });
  });
});
