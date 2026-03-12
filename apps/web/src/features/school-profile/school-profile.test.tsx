import { render, screen, waitFor, within } from "@testing-library/react";
import { HelmetProvider } from "react-helmet-async";
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
    <HelmetProvider>
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
    </HelmetProvider>
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
      expect(screen.getAllByRole("button", { name: "Save for later" })[0]).toBeInTheDocument();

      expect(screen.getByRole("heading", { name: "Pupil Demographics" })).toBeInTheDocument();
      expect(screen.getByRole("heading", { name: "School Overview" })).toBeInTheDocument();
      expect(screen.getByRole("heading", { name: "Analyst View" })).toBeInTheDocument();
      expect(screen.getByRole("heading", { name: "Day-to-Day at School" })).toBeInTheDocument();
      expect(screen.getByRole("heading", { name: "Teachers & Staff" })).toBeInTheDocument();
      expect(screen.getByRole("heading", { name: "School Admissions" })).toBeInTheDocument();
      expect(screen.getByRole("heading", { name: "Leaver Destinations" })).toBeInTheDocument();
      expect(screen.getByRole("heading", { name: "School Finance" })).toBeInTheDocument();
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
      expect(screen.getAllByText("Oversubscription Ratio").length).toBeGreaterThan(0);
      expect(screen.getByText("Places Offered")).toBeInTheDocument();
      expect(screen.getByText("Cross-LA Offers")).toBeInTheDocument();
      expect(screen.getAllByText("Overall Sustained Destinations").length).toBeGreaterThan(0);
      expect(screen.getByText("School Sixth Form")).toBeInTheDocument();
      expect(screen.getAllByText("Teacher Headcount").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Average Teacher Salary").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Income per Pupil").length).toBeGreaterThan(0);
      expect(screen.getByRole("heading", { name: "Teacher Mix by Sex" })).toBeInTheDocument();
      expect(screen.getByRole("heading", { name: "Support Staff Roles" })).toBeInTheDocument();
      expect(screen.getAllByText("Headteacher").length).toBeGreaterThan(0);
      expect(screen.getByText("House Prices")).toBeInTheDocument();
      expect(
        screen.getByText(/16 to 18 study destinations are present in the source data/i)
      ).toBeInTheDocument();
      expect(screen.getByText(/Limited in this view: Destinations/i)).toBeInTheDocument();
      expect(screen.getAllByText("Camden").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Similar Schools").length).toBeGreaterThan(0);
      const similarSchoolSummary = screen.getByText(
        /32nd percentile in a cohort of 566 schools/i
      );
      expect(similarSchoolSummary).toBeInTheDocument();
      const similarSchoolBlock = similarSchoolSummary.closest("div");
      expect(similarSchoolBlock).not.toBeNull();
      expect(within(similarSchoolBlock as HTMLElement).getByText("18.40%")).toBeInTheDocument();
    },
    15000,
  );

  it(
    "renders the profile before background trend/dashboard hydration completes",
    async () => {
      let resolveTrends: (value: typeof TRENDS_RESPONSE) => void = () => undefined;
      let resolveDashboard: (value: typeof DASHBOARD_RESPONSE) => void = () => undefined;

      trendsMock.mockReturnValue(
        new Promise((resolve) => {
          resolveTrends = resolve;
        }),
      );
      dashboardMock.mockReturnValue(
        new Promise((resolve) => {
          resolveDashboard = resolve;
        }),
      );

      renderProfileAtUrn("100001");

      expect(
        await screen.findByRole("heading", { name: "Camden Bridge Primary School" }),
      ).toBeInTheDocument();
      expect(screen.getAllByText("Ever Eligible for Free Meals").length).toBeGreaterThan(0);

      resolveTrends(TRENDS_RESPONSE);
      resolveDashboard(DASHBOARD_RESPONSE);

      await waitFor(() => {
        expect(screen.getByLabelText("Disadvantaged Pupils trend")).toBeInTheDocument();
      });
    },
    10000,
  );

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

  it("renders a not-applicable finance state for non-academy schools", async () => {
    const nonAcademyProfile = structuredClone(PROFILE_RESPONSE);
    nonAcademyProfile.school.type = "Community School";
    nonAcademyProfile.finance_latest = null;
    nonAcademyProfile.completeness.finance = {
      status: "unavailable",
      reason_code: "not_applicable",
      last_updated_at: null,
      years_available: null
    };

    const nonAcademyTrends = structuredClone(TRENDS_RESPONSE);
    nonAcademyTrends.series.income_per_pupil_gbp = [];
    nonAcademyTrends.series.expenditure_per_pupil_gbp = [];
    nonAcademyTrends.series.staff_costs_pct_of_expenditure = [];
    nonAcademyTrends.series.revenue_reserve_per_pupil_gbp = [];
    nonAcademyTrends.series.teaching_staff_costs_per_pupil_gbp = [];
    nonAcademyTrends.benchmarks.income_per_pupil_gbp = [];
    nonAcademyTrends.benchmarks.expenditure_per_pupil_gbp = [];
    nonAcademyTrends.benchmarks.staff_costs_pct_of_expenditure = [];
    nonAcademyTrends.benchmarks.revenue_reserve_per_pupil_gbp = [];
    nonAcademyTrends.benchmarks.teaching_staff_costs_per_pupil_gbp = [];
    nonAcademyTrends.section_completeness.finance = {
      status: "unavailable",
      reason_code: "not_applicable",
      last_updated_at: null,
      years_available: null
    };

    const nonAcademyDashboard = structuredClone(DASHBOARD_RESPONSE);
    nonAcademyDashboard.sections = nonAcademyDashboard.sections.filter(
      (section) => section.key !== "finance"
    );

    profileMock.mockResolvedValueOnce(nonAcademyProfile);
    trendsMock.mockResolvedValueOnce(nonAcademyTrends);
    dashboardMock.mockResolvedValueOnce(nonAcademyDashboard);

    renderProfileAtUrn("100001");

    expect(
      await screen.findByRole("heading", { name: "Camden Bridge Primary School" })
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("This section doesn't apply to this type of school.").length
    ).toBeGreaterThan(0);
  });

  it("renders the finance section when the profile payload omits optional finance fields", async () => {
    const partialFinanceProfile = structuredClone(PROFILE_RESPONSE);
    const financeLatest = partialFinanceProfile.finance_latest as Record<string, unknown>;

    delete financeLatest.in_year_balance_gbp;
    delete financeLatest.total_grant_funding_gbp;
    delete financeLatest.total_self_generated_funding_gbp;
    delete financeLatest.supply_teaching_staff_costs_gbp;
    delete financeLatest.education_support_staff_costs_gbp;
    delete financeLatest.other_staff_costs_gbp;
    delete financeLatest.premises_costs_gbp;
    delete financeLatest.educational_supplies_costs_gbp;
    delete financeLatest.bought_in_professional_services_costs_gbp;
    delete financeLatest.catering_costs_gbp;
    delete financeLatest.supply_staff_costs_pct_of_staff_costs;

    profileMock.mockResolvedValueOnce(partialFinanceProfile);

    renderProfileAtUrn("100001");

    expect(
      await screen.findByRole("heading", { name: "Camden Bridge Primary School" })
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "School Finance" })).toBeInTheDocument();
    expect(screen.queryByText("Supply Staff Costs Share")).not.toBeInTheDocument();
    expect(screen.getAllByText("Income per Pupil").length).toBeGreaterThan(0);
  });

  it("renders the destinations empty state when the profile omits destination data", async () => {
    const profileWithoutDestinations = structuredClone(PROFILE_RESPONSE);
    profileWithoutDestinations.destinations_latest = null;
    profileWithoutDestinations.completeness.destinations = {
      status: "unavailable",
      reason_code: "source_file_missing_for_year",
      last_updated_at: null,
      years_available: null
    };

    const trendsWithoutDestinations = structuredClone(TRENDS_RESPONSE);
    trendsWithoutDestinations.series.ks4_overall_pct = [];
    trendsWithoutDestinations.series.ks4_education_pct = [];
    trendsWithoutDestinations.series.ks4_apprenticeship_pct = [];
    trendsWithoutDestinations.series.ks4_employment_pct = [];
    trendsWithoutDestinations.series.ks4_not_sustained_pct = [];
    trendsWithoutDestinations.series.ks4_activity_unknown_pct = [];
    trendsWithoutDestinations.series.study_16_18_overall_pct = [];
    trendsWithoutDestinations.series.study_16_18_education_pct = [];
    trendsWithoutDestinations.series.study_16_18_apprenticeship_pct = [];
    trendsWithoutDestinations.series.study_16_18_employment_pct = [];
    trendsWithoutDestinations.series.study_16_18_not_sustained_pct = [];
    trendsWithoutDestinations.series.study_16_18_activity_unknown_pct = [];
    trendsWithoutDestinations.section_completeness.destinations = {
      status: "unavailable",
      reason_code: "source_file_missing_for_year",
      last_updated_at: null,
      years_available: null
    };

    profileMock.mockResolvedValueOnce(profileWithoutDestinations);
    trendsMock.mockResolvedValueOnce(trendsWithoutDestinations);

    renderProfileAtUrn("100001");

    expect(
      await screen.findByRole("heading", { name: "Camden Bridge Primary School" })
    ).toBeInTheDocument();
    expect(
      screen.getByText("School leaver destinations data is not available")
    ).toBeInTheDocument();
    expect(
      screen.queryByText(/16 to 18 study destinations are present in the source data/i)
    ).not.toBeInTheDocument();
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
