import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { NotFoundPage } from "./NotFoundPage";
import { renderWithProviders } from "../test/render";

describe("NotFoundPage", () => {
  it("renders 404 heading and back-to-search link", () => {
    renderWithProviders(<NotFoundPage />);

    expect(screen.getByRole("heading", { name: "Page not found" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to search" })).toHaveAttribute("href", "/");
  });

  it("renders explanatory text", () => {
    renderWithProviders(<NotFoundPage />);

    expect(
      screen.getByText(/doesn.t exist or has been moved/)
    ).toBeInTheDocument();
  });
});
