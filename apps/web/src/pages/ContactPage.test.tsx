import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ContactPage } from "./ContactPage";
import { siteConfig } from "../shared/config/site";
import { expectDocumentTitle } from "../test/head";
import { renderWithProviders } from "../test/render";

describe("ContactPage", () => {
  it("renders the contact email link and metadata", async () => {
    renderWithProviders(<ContactPage />);

    expect(screen.getByRole("heading", { name: "Contact and Feedback" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: siteConfig.supportEmail })).toHaveAttribute(
      "href",
      `mailto:${siteConfig.supportEmail}`
    );
    await expectDocumentTitle("Contact and Feedback");
  });
});
