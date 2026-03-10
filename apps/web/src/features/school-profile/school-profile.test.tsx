import { render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  ApiClientError,
  getSchoolProfile,
  getSchoolTrendDashboard,
  getSchoolTrends
} from "../../api/client";
import { ThemeProvider } from "../../app/providers/ThemeProvider";
import { ToastProvider } from "../../components/ui/Toast";
import { TooltipProvider } from "../../components/ui/Tooltip";
import { AuthProvider } from "../auth/AuthProvider";
import { ANONYMOUS_SESSION } from "../auth/types";
import { CompareSelectionProvider } from "../../shared/context/CompareSelectionContext";
import { SearchContextProvider } from "../../shared/context/SearchContext";
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
    <ThemeProvider>
      <AuthProvider autoLoad={false} initialSession={ANONYMOUS_SESSION}>
        <SearchContextProvider>
          <CompareSelectionProvider>
            <TooltipProvider>
              <ToastProvider>
                <RouterProvider router={router} />
              </ToastProvider>
            </TooltipProvider>
          </CompareSelectionProvider>
        </SearchContextProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

describe("SchoolProfileFeature", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    profileMock.mockResolvedValue(PROFILE_RESPONSE);
    trendsMock.mockResolvedValue(TRENDS_RESPONSE);
    dashboardMock.mockResolvedValue(DASHBOARD_RESPONSE);
  });

  it(
    "renders the widened metrics surface on success",
    async () => {
      renderProfileAtUrn("100001");

      expect(
        await screen.findByRole("heading", { name: "Camden Bridge Primary School" })
      ).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Save" })).toBeInTheDocument();

      expect(screen.getByRole("heading", { name: "Pupil Demographics" })).toBeInTheDocument();
      expect(screen.getByRole("heading", { name: "School Overview" })).toBeInTheDocument();
      expect(screen.getByRole("heading", { name: "Analyst View" })).toBeInTheDocument();
      expect(screen.getByRole("heading", { name: "Day-to-Day at School" })).toBeInTheDocument();
      expect(screen.getByRole("heading", { name: "Teachers & Staff" })).toBeInTheDocument();
      expect(screen.getByRole("heading", { name: "Neighbourhood Context" })).toBeInTheDocument();

      expect(
        screen.getByText(/This overview is AI-generated from public government data/i)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/This analyst view is AI-generated from public government data/i)
      ).toBeInTheDocument();
      expect(screen.getAllByText("Ever Eligible for Free Meals").length).toBeGreaterThan(0);
      expect(screen.getByText("Special Educational Needs")).toBeInTheDocument();
      expect(screen.getByText("Overall Attendance")).toBeInTheDocument();
      expect(screen.getAllByText("Suspension Rate").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Pupil to Teacher Ratio").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Headteacher").length).toBeGreaterThan(0);
      expect(screen.getByText("House Prices")).toBeInTheDocument();
      expect(screen.getAllByText("Camden").length).toBeGreaterThan(0);
    },
    15000,
  );

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
    expect(screen.getAllByText("Ever Eligible for Free Meals").length).toBeGreaterThan(0);

    resolveTrends(TRENDS_RESPONSE);
    resolveDashboard(DASHBOARD_RESPONSE);

    await waitFor(() => {
      expect(screen.getByLabelText("Disadvantaged Pupils trend")).toBeInTheDocument();
    });
  });

  it("keeps the core profile visible when trend endpoints fail", async () => {
    trendsMock.mockRejectedValue(new ApiClientError(503));
    dashboardMock.mockRejectedValue(new ApiClientError(503));

    renderProfileAtUrn("100001");

    expect(
      await screen.findByRole("heading", { name: "Camden Bridge Primary School" })
    ).toBeInTheDocument();
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

  it("renders premium preview gates when analyst and neighbourhood data are locked", async () => {
    const lockedProfile = structuredClone(PROFILE_RESPONSE);
    lockedProfile.analyst = {
      access: {
        state: "locked",
        capability_key: "premium_ai_analyst",
        reason_code: "premium_capability_missing",
        product_codes: ["premium_launch"],
        requires_auth: false,
        requires_purchase: true,
        school_name: "Camden Bridge Primary School",
      },
      text: null,
      teaser_text: "The published profile points to a school with more stability than volatility.",
      disclaimer: PROFILE_RESPONSE.analyst.disclaimer,
    };
    lockedProfile.neighbourhood = {
      access: {
        state: "locked",
        capability_key: "premium_neighbourhood",
        reason_code: "premium_capability_missing",
        product_codes: ["premium_launch"],
        requires_auth: false,
        requires_purchase: true,
        school_name: "Camden Bridge Primary School",
      },
      area_context: null,
      teaser_text: "Premium neighbourhood context is available for Camden Bridge Primary School.",
    };
    profileMock.mockResolvedValueOnce(lockedProfile);

    renderProfileAtUrn("100001");

    expect(
      await screen.findByText(/Unlock the full analyst view for Camden Bridge Primary School/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/Premium neighbourhood context is available/i)).toBeInTheDocument();
    expect(screen.queryByText("Average Price")).not.toBeInTheDocument();
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
