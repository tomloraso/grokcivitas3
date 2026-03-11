import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AccessibilityPage } from "./AccessibilityPage";
import { expectDocumentTitle } from "../test/head";
import { renderWithProviders } from "../test/render";

describe("AccessibilityPage", () => {
  it("renders the accessibility statement and metadata", async () => {
    renderWithProviders(<AccessibilityPage />);

    expect(
      screen.getByRole("heading", { name: "Accessibility Statement" })
    ).toBeInTheDocument();
    expect(screen.getByText(/keyboard navigation/i)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Enforcement Procedure" })).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /Equality Advisory and Support Service/i })
    ).toHaveAttribute("href", "https://www.equalityadvisoryservice.com/");
    expect(screen.getByText(/11 March 2026/)).toBeInTheDocument();
    await expectDocumentTitle("Accessibility Statement");
  });
});
