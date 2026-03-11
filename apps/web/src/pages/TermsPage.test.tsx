import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TermsPage } from "./TermsPage";
import { expectDocumentTitle } from "../test/head";
import { renderWithProviders } from "../test/render";

describe("TermsPage", () => {
  it("renders the terms content and metadata", async () => {
    renderWithProviders(<TermsPage />);

    expect(screen.getByRole("heading", { name: "Terms of Use" })).toBeInTheDocument();
    expect(screen.getByText(/acceptable use/i)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Governing Law" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Changes To These Terms" })).toBeInTheDocument();
    await expectDocumentTitle("Terms of Use");
  });
});
