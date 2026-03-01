import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { runA11yAudit } from "../../test/accessibility";
import { renderWithProviders } from "../../test/render";
import { AppShell } from "./AppShell";
import { PageContainer } from "./PageContainer";
import { SplitPaneLayout } from "./SplitPaneLayout";

describe("layout primitives", () => {
  it("renders app shell and page container wrappers", () => {
    const { container } = renderWithProviders(
      <AppShell>
        <PageContainer>
          <p>Content body</p>
        </PageContainer>
      </AppShell>
    );

    expect(screen.getByText("Content body")).toBeInTheDocument();
    expect(container.firstChild).toHaveClass("relative");
  });

  it("defines responsive split-pane behavior for map and list", () => {
    renderWithProviders(
      <SplitPaneLayout listPane={<div>List pane</div>} mapPane={<div>Map pane</div>} />
    );

    const splitPane = screen.getByLabelText("School results").parentElement;
    expect(splitPane).not.toBeNull();
    expect(splitPane?.className).toContain("lg:grid-cols");
  });

  it("passes accessibility smoke checks", async () => {
    const { container } = renderWithProviders(
      <SplitPaneLayout listPane={<div>List pane</div>} mapPane={<div>Map pane</div>} />
    );

    const results = await runA11yAudit(container);
    expect(results).toHaveNoViolations();
  });
});
