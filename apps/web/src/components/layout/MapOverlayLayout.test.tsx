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

  describe("desktop resizable panel", () => {
    it("renders panel at default width", () => {
      render(
        <MapOverlayLayout map={<div />}>
          <p>Panel content</p>
        </MapOverlayLayout>
      );

      const panel = screen.getByRole("region", { name: "Results panel" });
      expect(panel).toBeVisible();
      expect(panel.style.width).toBe("380px");
      expect(screen.getByText("Panel content")).toBeInTheDocument();
    });

    it("restores persisted width from localStorage", () => {
      localStorage.setItem("civitas:panel-width", "320");

      render(
        <MapOverlayLayout map={<div />}>
          <p>Panel content</p>
        </MapOverlayLayout>
      );

      const panel = screen.getByRole("region", { name: "Results panel" });
      expect(panel.style.width).toBe("320px");
    });

    it("clamps persisted width within bounds", () => {
      localStorage.setItem("civitas:panel-width", "600");

      render(
        <MapOverlayLayout map={<div />}>
          <p>Panel content</p>
        </MapOverlayLayout>
      );

      const panel = screen.getByRole("region", { name: "Results panel" });
      // 600 should be clamped to max 480
      expect(panel.style.width).toBe("480px");
    });

    it("renders resize handle with ARIA separator role", () => {
      render(
        <MapOverlayLayout map={<div />}>
          <p>Content</p>
        </MapOverlayLayout>
      );

      const handle = screen.getByRole("separator", { name: /Resize panel/ });
      expect(handle).toBeInTheDocument();
      expect(handle).toHaveAttribute("aria-orientation", "vertical");
      expect(handle).toHaveAttribute("aria-valuemin", "280");
      expect(handle).toHaveAttribute("aria-valuemax", "480");
    });

    it("always shows panel content (no collapsed state)", () => {
      render(
        <MapOverlayLayout map={<div />}>
          <p>Always visible</p>
        </MapOverlayLayout>
      );

      // No collapse/expand buttons
      expect(screen.queryByRole("button", { name: /Collapse/ })).not.toBeInTheDocument();
      expect(screen.queryByRole("button", { name: /Expand/ })).not.toBeInTheDocument();
      // Content always visible
      expect(screen.getByText("Always visible")).toBeVisible();
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
      // Drag handle button serves as expand/collapse toggle
      expect(screen.getByRole("button", { name: "Expand results panel" })).toBeInTheDocument();
    });

    it("toggles between peek and expanded via drag handle button", () => {
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
