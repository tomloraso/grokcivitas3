import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { SiteHeader } from "./SiteHeader";
import { SiteFooter } from "./SiteFooter";
import { SkipToContent } from "./SkipToContent";
import { Breadcrumbs } from "./Breadcrumbs";
import { SearchContextProvider } from "../../shared/context/SearchContext";
import { renderWithProviders } from "../../test/render";
import { runA11yAudit } from "../../test/accessibility";

describe("SiteHeader", () => {
  it("renders brand mark in header banner", () => {
    renderWithProviders(<SiteHeader />);

    expect(screen.getByRole("banner")).toBeInTheDocument();
    expect(screen.getByLabelText("Civitas - return to home")).toBeInTheDocument();
    expect(screen.getByText("CIVITAS")).toBeInTheDocument();
  });

  it("passes accessibility smoke check", async () => {
    const { container } = renderWithProviders(<SiteHeader />);
    const results = await runA11yAudit(container);
    expect(results).toHaveNoViolations();
  });
});

describe("SiteFooter", () => {
  it("renders footer with copyright and navigation", () => {
    renderWithProviders(<SiteFooter />);

    expect(screen.getByRole("contentinfo")).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Footer" })).toBeInTheDocument();
    expect(screen.getByText(/CIVITAS. All data sourced/)).toBeInTheDocument();
  });

  it("renders footer links", () => {
    renderWithProviders(<SiteFooter />);

    expect(screen.getByText("About")).toBeInTheDocument();
    expect(screen.getByText("Contact")).toBeInTheDocument();
    expect(screen.getByText("Privacy")).toBeInTheDocument();
  });

  it("passes accessibility smoke check", async () => {
    const { container } = renderWithProviders(<SiteFooter />);
    const results = await runA11yAudit(container);
    expect(results).toHaveNoViolations();
  });
});

describe("SkipToContent", () => {
  it("renders skip link targeting #main-content", () => {
    renderWithProviders(<SkipToContent />);

    const link = screen.getByText("Skip to content");
    expect(link).toHaveAttribute("href", "#main-content");
  });

  it("becomes focused on first tab press", async () => {
    const user = userEvent.setup();
    renderWithProviders(<SkipToContent />);

    await user.tab();
    expect(screen.getByText("Skip to content")).toHaveFocus();
  });
});

describe("Breadcrumbs", () => {
  it("renders home icon and segments", () => {
    renderWithProviders(
      <Breadcrumbs segments={[{ label: "Test School" }]} />
    );

    expect(screen.getByRole("navigation", { name: "Breadcrumb" })).toBeInTheDocument();
    expect(screen.getByLabelText("Home")).toBeInTheDocument();
    expect(screen.getByText("Test School")).toBeInTheDocument();
  });

  it("marks last segment as current page", () => {
    renderWithProviders(
      <Breadcrumbs segments={[{ label: "Schools", href: "/" }, { label: "Profile" }]} />
    );

    expect(screen.getByText("Profile")).toHaveAttribute("aria-current", "page");
    expect(screen.getByText("Schools")).not.toHaveAttribute("aria-current");
  });

  it("renders intermediate segments as links", () => {
    renderWithProviders(
      <Breadcrumbs segments={[{ label: "Schools", href: "/" }, { label: "Profile" }]} />
    );

    expect(screen.getByRole("link", { name: "Schools" })).toHaveAttribute("href", "/");
  });

  it("passes accessibility smoke check", async () => {
    const { container } = renderWithProviders(
      <Breadcrumbs segments={[{ label: "Test School" }]} />
    );
    const results = await runA11yAudit(container);
    expect(results).toHaveNoViolations();
  });
});

describe("SiteHeader - search context", () => {
  it("shows search context chip on map page when search is active", () => {
    renderWithProviders(
      <SearchContextProvider initialSearch={{ postcode: "SW1A 1AA", radius: 5, count: 12 }}>
        <SiteHeader />
      </SearchContextProvider>,
      { initialEntries: ["/"] }
    );

    expect(screen.getByLabelText(/Searching SW1A 1AA within 5 miles/)).toBeInTheDocument();
    expect(screen.getByText("SW1A 1AA")).toBeInTheDocument();
    expect(screen.getByText("5 mi")).toBeInTheDocument();
    expect(screen.getByText("12 results")).toBeInTheDocument();
  });

  it("hides search context chip on non-map routes", () => {
    renderWithProviders(
      <SearchContextProvider initialSearch={{ postcode: "SW1A 1AA", radius: 5, count: 12 }}>
        <SiteHeader />
      </SearchContextProvider>,
      { initialEntries: ["/schools/100000"] }
    );

    expect(screen.queryByLabelText(/Searching/)).not.toBeInTheDocument();
  });

  it("hides search context chip when no search is active", () => {
    renderWithProviders(
      <SearchContextProvider>
        <SiteHeader />
      </SearchContextProvider>,
      { initialEntries: ["/"] }
    );

    expect(screen.queryByLabelText(/Searching/)).not.toBeInTheDocument();
  });
});

describe("Breadcrumbs - search context", () => {
  it("renders postcode breadcrumb linking back to search", () => {
    renderWithProviders(
      <Breadcrumbs
        segments={[
          { label: "SW1A 1AA", href: "/" },
          { label: "Test School" },
        ]}
      />
    );

    expect(screen.getByRole("link", { name: "SW1A 1AA" })).toHaveAttribute("href", "/");
    expect(screen.getByText("Test School")).toHaveAttribute("aria-current", "page");
  });
});

