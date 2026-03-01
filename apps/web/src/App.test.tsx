import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { runA11yAudit } from "./test/accessibility";
import { renderWithProviders } from "./test/render";

vi.mock("./components/maps/MapPanel", () => ({
  MapPanel: ({ title }: { title: string }) => <div data-testid="map-panel-mock">{title}</div>
}));

describe("App", () => {
  it("renders the foundations shell and baseline controls", () => {
    renderWithProviders(<App />);

    expect(screen.getByRole("heading", { name: "Civitas Schools Discovery" })).toBeInTheDocument();
    expect(screen.getByLabelText("Postcode")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Search schools" })).toBeInTheDocument();
    expect(screen.getByTestId("map-panel-mock")).toHaveTextContent("Nearby schools map");
  });

  it("supports previewing empty and error states", async () => {
    const user = userEvent.setup();

    renderWithProviders(<App />);

    await user.click(screen.getByLabelText("Preview state"));
    await user.click(screen.getByRole("option", { name: "Empty" }));
    expect(screen.getByText("No schools found")).toBeInTheDocument();

    await user.click(screen.getByLabelText("Preview state"));
    await user.click(screen.getByRole("option", { name: "Error" }));
    expect(screen.getByText("Search temporarily unavailable")).toBeInTheDocument();
  });

  it("passes accessibility smoke checks", async () => {
    const { container } = renderWithProviders(<App />);
    const results = await runA11yAudit(container);
    expect(results).toHaveNoViolations();
  });
});
