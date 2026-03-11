import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PrivacyPage } from "./PrivacyPage";
import { siteConfig } from "../shared/config/site";
import { expectDocumentTitle } from "../test/head";
import { renderWithProviders } from "../test/render";

describe("PrivacyPage", () => {
  it("renders cookie disclosures and metadata", async () => {
    renderWithProviders(<PrivacyPage />);

    expect(screen.getByRole("heading", { name: "Privacy Policy" })).toBeInTheDocument();
    expect(screen.getByText("Authentication session cookie")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "How Long We Keep It" })).toBeInTheDocument();
    expect(screen.getByText("Typical Lifetime")).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: siteConfig.privacyEmail }).length).toBeGreaterThan(0);
    await expectDocumentTitle("Privacy Policy");
  });
});
