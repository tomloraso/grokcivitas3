import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createMemoryRouter, RouterProvider } from "react-router-dom";

import { runA11yAudit } from "./test/accessibility";
import { ThemeProvider } from "./app/providers/ThemeProvider";

vi.mock("./components/maps/MapPanelChromeless", () => ({
  MapPanelChromeless: ({ markers }: { markers: Array<{ id: string }> }) => (
    <div data-testid="map-panel-mock">Chromeless map: {markers.length} markers</div>
  )
}));

const routeModulesPromise = Promise.all([
  import("./app/RootLayout"),
  import("./features/schools-search/SchoolsSearchFeature"),
  import("./pages/NotFoundPage")
]);

async function renderAppAtRoute(initialEntry = "/") {
  const [rootLayoutModule, schoolsSearchModule, notFoundModule] = await routeModulesPromise;
  const RootLayout = rootLayoutModule.RootLayout;
  const SchoolsSearchFeature = schoolsSearchModule.SchoolsSearchFeature;
  const NotFoundPage = notFoundModule.NotFoundPage;

  const router = createMemoryRouter(
    [
      {
        element: <RootLayout />,
        children: [
          { index: true, element: <SchoolsSearchFeature /> },
          {
            path: "schools/:urn",
            element: <div data-testid="profile-placeholder">Profile for URN</div>
          },
          { path: "*", element: <NotFoundPage /> }
        ]
      }
    ],
    { initialEntries: [initialEntry] }
  );

  return render(<ThemeProvider><RouterProvider router={router} /></ThemeProvider>);
}

describe("App", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the schools-search shell and baseline controls", async () => {
    await renderAppAtRoute("/");

    expect(screen.getByRole("heading", { name: "Find schools near you" })).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: /search/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Search schools" })).toBeInTheDocument();
    expect(screen.getByText("Search for nearby schools by postcode or name to load results.")).toBeInTheDocument();
    expect(screen.getByTestId("map-panel-mock")).toHaveTextContent("Chromeless map: 0 markers");
  }, 10000);

  it("renders site header with Civitas brand on all routes", async () => {
    await renderAppAtRoute("/");

    expect(screen.getAllByLabelText("Civitas - return to home").length).toBeGreaterThan(0);
    expect(screen.getAllByText("CIVITAS").length).toBeGreaterThan(0);
  });

  it("hides site footer on the search/map page", async () => {
    await renderAppAtRoute("/");

    expect(screen.queryByRole("contentinfo")).not.toBeInTheDocument();
  });

  it("renders site footer on non-map routes", async () => {
    await renderAppAtRoute("/schools/100001");

    expect(screen.getByRole("contentinfo")).toBeInTheDocument();
    expect(screen.getByText(/CIVITAS. All data sourced/)).toBeInTheDocument();
  });

  it("skip-to-content link is the first focusable element", async () => {
    await renderAppAtRoute("/");
    const user = userEvent.setup();

    await user.tab();
    const skipLink = screen.getByText("Skip to content");
    expect(skipLink).toHaveFocus();
    expect(skipLink).toHaveAttribute("href", "#main-content");
  });

  it("renders 404 page for unknown routes", async () => {
    await renderAppAtRoute("/unknown-path");

    expect(screen.getByRole("heading", { name: "Page not found" })).toBeInTheDocument();
    expect(screen.getByText("Back to search")).toBeInTheDocument();
  });

  it("renders profile route for /schools/:urn", async () => {
    await renderAppAtRoute("/schools/100001");

    expect(screen.getByTestId("profile-placeholder")).toBeInTheDocument();
  });

  it("passes accessibility smoke checks", async () => {
    const { container } = await renderAppAtRoute("/");
    const results = await runA11yAudit(container);
    expect(results).toHaveNoViolations();
  });
});
