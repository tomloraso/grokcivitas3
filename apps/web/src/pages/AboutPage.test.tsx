import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AboutPage } from "./AboutPage";
import { siteConfig } from "../shared/config/site";
import { expectDocumentTitle } from "../test/head";
import { renderWithProviders } from "../test/render";

describe("AboutPage", () => {
  it("renders the about content and updates the page title", async () => {
    renderWithProviders(<AboutPage />);

    expect(
      screen.getByRole("heading", { name: `About ${siteConfig.productName}` })
    ).toBeInTheDocument();
    expect(screen.getByText(/does not rank schools/i)).toBeInTheDocument();
    await expectDocumentTitle("About");
  });
});
