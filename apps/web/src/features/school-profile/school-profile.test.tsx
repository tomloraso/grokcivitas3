import { render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  ApiClientError,
  getSchoolProfile,
  getSchoolTrendDashboard,
  getSchoolTrends
} from "../../api/client";
import { TooltipProvider } from "../../components/ui/Tooltip";
import { runA11yAudit } from "../../test/accessibility";
import { DASHBOARD_RESPONSE, PROFILE_RESPONSE, TRENDS_RESPONSE } from "./testData";
import { SchoolProfileFeature } from "./SchoolProfileFeature";

vi.mock("../../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../api/client")>();
  return {
    ...actual,
    getSchoolProfile: vi.fn(),
    getSchoolTrends: vi.fn(),
    getSchoolTrendDashboard: vi.fn()
  };
});

const profileMock = vi.mocked(getSchoolProfile);
const trendsMock = vi.mocked(getSchoolTrends);
const dashboardMock = vi.mocked(getSchoolTrendDashboard);

function renderProfileAtUrn(urn: string) {
  const router = createMemoryRouter(
    [
      {
        path: "schools/:urn",
        element: <SchoolProfileFeature />
      }
    ],
    { initialEntries: [`/schools/${urn}`] }
  );

  return render(
    <TooltipProvider>
      <RouterProvider router={router} />
    </TooltipProvider>
  );
}

describe("SchoolProfileFeature", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    profileMock.mockResolvedValue(PROFILE_RESPONSE);
    trendsMock.mockResolvedValue(TRENDS_RESPONSE);
    dashboardMock.mockResolvedValue(DASHBOARD_RESPONSE);
  });

  it("renders the widened metrics surface on success", async () => {
    renderProfileAtUrn("100001");

    expect(
      await screen.findByRole("heading", { name: "Camden Bridge Primary School" })
    ).toBeInTheDocument();

    expect(screen.getByRole("heading", { name: "Pupil Demographics" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Attendance and Behaviour" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Workforce and Leadership" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Benchmark Comparison" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Neighbourhood Context" })).toBeInTheDocument();

    expect(screen.getByText("FSM6")).toBeInTheDocument();
    expect(screen.getByText("SEND Primary Need")).toBeInTheDocument();
    expect(screen.getByText("Overall Attendance")).toBeInTheDocument();
    expect(screen.getAllByText("Suspensions Rate").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Pupil to Teacher Ratio").length).toBeGreaterThan(0);
    expect(screen.getByText("Headteacher")).toBeInTheDocument();
    expect(screen.getByText("House Prices")).toBeInTheDocument();
    expect(screen.getAllByText("Camden").length).toBeGreaterThan(0);
  });

  it("renders the profile before background trend/dashboard hydration completes", async () => {
    let resolveTrends: (value: typeof TRENDS_RESPONSE) => void = () => undefined;
    let resolveDashboard: (value: typeof DASHBOARD_RESPONSE) => void = () => undefined;

    trendsMock.mockReturnValue(
      new Promise((resolve) => {
        resolveTrends = resolve;
      })
    );
    dashboardMock.mockReturnValue(
      new Promise((resolve) => {
        resolveDashboard = resolve;
      })
    );

    renderProfileAtUrn("100001");

    expect(
      await screen.findByRole("heading", { name: "Camden Bridge Primary School" })
    ).toBeInTheDocument();
    expect(screen.getByText("FSM6")).toBeInTheDocument();

    resolveTrends(TRENDS_RESPONSE);
    resolveDashboard(DASHBOARD_RESPONSE);

    await waitFor(() => {
      expect(screen.getByLabelText("Disadvantaged Pupils trend")).toBeInTheDocument();
      expect(screen.getByLabelText("Disadvantaged Pupils (%) benchmark trend")).toBeInTheDocument();
    });
  });

  it("keeps the core profile visible when trend endpoints fail", async () => {
    trendsMock.mockRejectedValue(new ApiClientError(503));
    dashboardMock.mockRejectedValue(new ApiClientError(503));

    renderProfileAtUrn("100001");

    expect(
      await screen.findByRole("heading", { name: "Camden Bridge Primary School" })
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Benchmark Comparison" })).toBeInTheDocument();
    expect(screen.getAllByText("Disadvantaged Pupils").length).toBeGreaterThan(0);
  });

  it("renders not-found and retry error states", async () => {
    profileMock.mockRejectedValueOnce(new ApiClientError(404));
    renderProfileAtUrn("999999");

    expect(await screen.findByRole("heading", { name: "School not found" })).toBeInTheDocument();

    profileMock.mockRejectedValueOnce(new Error("Request failed: 503"));
    renderProfileAtUrn("100001");

    expect(await screen.findByRole("heading", { name: "Something went wrong" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
  });

  it(
    "passes accessibility smoke check",
    async () => {
      const { container } = renderProfileAtUrn("100001");

      await screen.findByRole("heading", { name: "Camden Bridge Primary School" });
      const results = await runA11yAudit(container);
      expect(results).toHaveNoViolations();
    },
    20000
  );
});
