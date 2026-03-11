import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ContentPageLayout } from "./ContentPageLayout";
import { renderWithProviders } from "../../test/render";

describe("ContentPageLayout", () => {
  it("renders the heading, lede, and prose wrapper", () => {
    renderWithProviders(
      <ContentPageLayout title="Example title" canonicalPath="/about" lede="Example lede">
        <p>Example body</p>
      </ContentPageLayout>
    );

    expect(screen.getByRole("heading", { name: "Example title" })).toBeInTheDocument();
    expect(screen.getByText("Example lede")).toBeInTheDocument();
    expect(document.querySelector("article.content-prose")).not.toBeNull();
  });
});
