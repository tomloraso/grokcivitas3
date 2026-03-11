import type { components, operations } from "./generated-types";

export type AuthStartRequest = components["schemas"]["AuthStartRequest"];

export type AuthStartResponse = components["schemas"]["AuthStartResponse"];

export type HealthResponse =
  operations["health_api_v1_health_get"]["responses"][200]["content"]["application/json"];

export type BillingProductsResponse =
  components["schemas"]["BillingProductsResponse"];

export type BillingProduct = components["schemas"]["BillingProductResponse"];

export type CheckoutSessionCreateRequest =
  components["schemas"]["CheckoutSessionCreateRequest"];

export type CheckoutSessionCreateResponse =
  components["schemas"]["CheckoutSessionCreateResponse"];

export type CheckoutSessionStatusResponse =
  components["schemas"]["CheckoutSessionStatusResponse"];

export type BillingPortalSessionCreateRequest =
  components["schemas"]["BillingPortalSessionCreateRequest"];

export type BillingPortalSessionCreateResponse =
  components["schemas"]["BillingPortalSessionCreateResponse"];

export type AccountAccessResponse =
  components["schemas"]["AccountAccessResponse"];

export type AccountEntitlementResponse =
  components["schemas"]["AccountEntitlementResponse"];

export type AccountFavouritesResponse =
  components["schemas"]["AccountFavouritesResponse"];

export type AccountFavouriteSchoolResponse =
  components["schemas"]["AccountFavouriteSchoolResponse"];

export type SavedSchoolStateResponse =
  components["schemas"]["SavedSchoolStateResponse"];

export type SessionResponse = components["schemas"]["SessionResponse"];

export type SessionUser = components["schemas"]["SessionUserResponse"];

export type SectionAccessResponse =
  components["schemas"]["SectionAccessResponse"];

export type Task = components["schemas"]["TaskResponse"];

export type CreateTaskRequest = components["schemas"]["TaskCreateRequest"];

export type SchoolsSearchResponse =
  components["schemas"]["SchoolsSearchResponse"];

export type PostcodeSchoolSearchResultItem =
  components["schemas"]["PostcodeSchoolSearchItemResponse"];

export type SchoolNameSearchResultItem =
  components["schemas"]["SchoolSearchItemResponse"];

export type SchoolSearchResultItem = SchoolNameSearchResultItem;

export type SchoolSearchAcademicMetric =
  components["schemas"]["SchoolSearchAcademicMetricResponse"];

export type SchoolSearchLatestOfsted =
  components["schemas"]["SchoolSearchLatestOfstedResponse"];

export type SchoolNameSearchResponse =
  components["schemas"]["SchoolNameSearchResponse"];

export type SearchSchoolsQuery =
  operations["search_schools_api_v1_schools_get"]["parameters"]["query"];

/* ------------------------------------------------------------------ */
/* School profile + trends (Phase 1D / 1E)                             */
/* ------------------------------------------------------------------ */

type SchoolProfileWorkforceBreakdownItemContract =
  components["schemas"]["SchoolProfileWorkforceBreakdownItemResponse"];

type SchoolTrendPointContract =
  components["schemas"]["SchoolTrendPointResponse"];

type SchoolTrendBenchmarkPointContract =
  components["schemas"]["SchoolTrendBenchmarkPointResponse"];

type WorkforceDepthProfileFields = {
  teacher_headcount_total: number | null;
  teacher_fte_total: number | null;
  support_staff_headcount_total: number | null;
  support_staff_fte_total: number | null;
  leadership_headcount: number | null;
  teacher_average_mean_salary_gbp: number | null;
  teacher_absence_pct: number | null;
  teacher_vacancy_rate: number | null;
  third_party_support_staff_headcount: number | null;
  teacher_sex_breakdown: SchoolProfileWorkforceBreakdownItemContract[];
  teacher_age_breakdown: SchoolProfileWorkforceBreakdownItemContract[];
  teacher_ethnicity_breakdown: SchoolProfileWorkforceBreakdownItemContract[];
  teacher_qualification_breakdown: SchoolProfileWorkforceBreakdownItemContract[];
  support_staff_post_mix: SchoolProfileWorkforceBreakdownItemContract[];
};

type WorkforceDepthTrendSeriesFields = {
  teacher_headcount_total: SchoolTrendPointContract[];
  teacher_fte_total: SchoolTrendPointContract[];
  support_staff_headcount_total: SchoolTrendPointContract[];
  support_staff_fte_total: SchoolTrendPointContract[];
  leadership_share_of_teachers: SchoolTrendPointContract[];
  teacher_average_mean_salary_gbp: SchoolTrendPointContract[];
  teacher_average_median_salary_gbp: SchoolTrendPointContract[];
  teachers_on_leadership_pay_range_pct: SchoolTrendPointContract[];
  teacher_absence_pct: SchoolTrendPointContract[];
  teacher_absence_days_total: SchoolTrendPointContract[];
  teacher_absence_days_average: SchoolTrendPointContract[];
  teacher_absence_days_average_all_teachers: SchoolTrendPointContract[];
  teacher_vacancy_count: SchoolTrendPointContract[];
  teacher_vacancy_rate: SchoolTrendPointContract[];
  teacher_tempfilled_vacancy_count: SchoolTrendPointContract[];
  teacher_tempfilled_vacancy_rate: SchoolTrendPointContract[];
  third_party_support_staff_headcount: SchoolTrendPointContract[];
};

type WorkforceDepthTrendBenchmarkFields = {
  teacher_headcount_total: SchoolTrendBenchmarkPointContract[];
  teacher_fte_total: SchoolTrendBenchmarkPointContract[];
  support_staff_headcount_total: SchoolTrendBenchmarkPointContract[];
  support_staff_fte_total: SchoolTrendBenchmarkPointContract[];
  leadership_share_of_teachers: SchoolTrendBenchmarkPointContract[];
  teacher_average_mean_salary_gbp: SchoolTrendBenchmarkPointContract[];
  teacher_average_median_salary_gbp: SchoolTrendBenchmarkPointContract[];
  teachers_on_leadership_pay_range_pct: SchoolTrendBenchmarkPointContract[];
  teacher_absence_pct: SchoolTrendBenchmarkPointContract[];
  teacher_absence_days_total: SchoolTrendBenchmarkPointContract[];
  teacher_absence_days_average: SchoolTrendBenchmarkPointContract[];
  teacher_absence_days_average_all_teachers: SchoolTrendBenchmarkPointContract[];
  teacher_vacancy_count: SchoolTrendBenchmarkPointContract[];
  teacher_vacancy_rate: SchoolTrendBenchmarkPointContract[];
  teacher_tempfilled_vacancy_count: SchoolTrendBenchmarkPointContract[];
  teacher_tempfilled_vacancy_rate: SchoolTrendBenchmarkPointContract[];
  third_party_support_staff_headcount: SchoolTrendBenchmarkPointContract[];
};

export type SchoolProfileResponse =
  Omit<components["schemas"]["SchoolProfileResponse"], "workforce_latest"> & {
    workforce_latest: SchoolProfileWorkforceLatest | null;
  };

export type SchoolProfileSchool =
  components["schemas"]["SchoolProfileSchoolResponse"];

export type SchoolProfileDemographicsLatest =
  components["schemas"]["SchoolProfileDemographicsLatestResponse"];

export type SchoolProfileDemographicsCoverage =
  components["schemas"]["SchoolProfileDemographicsCoverageResponse"];

export type SchoolProfileDestinationStageLatest =
  components["schemas"]["SchoolProfileDestinationStageLatestResponse"];

export type SchoolProfileDestinationsLatest =
  components["schemas"]["SchoolProfileDestinationsLatestResponse"];

export type SchoolProfileOfstedLatest =
  components["schemas"]["SchoolProfileOfstedLatestResponse"];

export type SchoolProfileAttendanceLatest =
  components["schemas"]["SchoolProfileAttendanceLatestResponse"];

export type SchoolProfileBehaviourLatest =
  components["schemas"]["SchoolProfileBehaviourLatestResponse"];

export type SchoolProfileWorkforceLatest =
  components["schemas"]["SchoolProfileWorkforceLatestResponse"] &
    WorkforceDepthProfileFields;

export type SchoolProfileWorkforceBreakdownItem =
  SchoolProfileWorkforceBreakdownItemContract;

export type SchoolProfileLeadershipSnapshot =
  components["schemas"]["SchoolProfileLeadershipSnapshotResponse"];

export type SchoolProfileBenchmarks =
  components["schemas"]["SchoolProfileBenchmarksResponse"];

export type SchoolProfileMetricBenchmark =
  components["schemas"]["SchoolProfileMetricBenchmarkResponse"];

export type SchoolProfileAreaContext =
  components["schemas"]["SchoolProfileAreaContextResponse"];

export type SchoolProfileAreaHousePrices =
  components["schemas"]["SchoolProfileAreaHousePricesResponse"];

export type SchoolProfileAnalystSection =
  components["schemas"]["SchoolProfileAnalystSectionResponse"];

export type SchoolProfileNeighbourhoodSection =
  components["schemas"]["SchoolProfileNeighbourhoodSectionResponse"];

export type SchoolCompareResponse =
  components["schemas"]["SchoolCompareResponse"];

export type SchoolCompareSchool =
  components["schemas"]["SchoolCompareSchoolResponse"];

export type SchoolCompareSection =
  components["schemas"]["SchoolCompareSectionResponse"];

export type SchoolCompareRow =
  components["schemas"]["SchoolCompareRowResponse"];

export type SchoolCompareCell =
  components["schemas"]["SchoolCompareCellResponse"];

export type SchoolCompareBenchmark =
  components["schemas"]["SchoolCompareBenchmarkResponse"];

export type SchoolTrendsResponse =
  Omit<components["schemas"]["SchoolTrendsResponse"], "series" | "benchmarks"> & {
    series: SchoolTrendsSeries;
    benchmarks: SchoolTrendsBenchmarks;
  };

export type SchoolTrendsSeries =
  components["schemas"]["SchoolTrendsSeriesResponse"] &
    WorkforceDepthTrendSeriesFields;

export type SchoolTrendsBenchmarks =
  components["schemas"]["SchoolTrendsBenchmarksResponse"] &
    WorkforceDepthTrendBenchmarkFields;

export type SchoolTrendPoint =
  components["schemas"]["SchoolTrendPointResponse"];

export type SchoolTrendBenchmarkPoint =
  components["schemas"]["SchoolTrendBenchmarkPointResponse"];

export type SchoolTrendsHistoryQuality =
  components["schemas"]["SchoolTrendsHistoryQualityResponse"];

export type SchoolTrendDashboardResponse =
  components["schemas"]["SchoolTrendDashboardResponse"];

export type SchoolTrendDashboardSection =
  components["schemas"]["SchoolTrendDashboardSectionResponse"];

export type SchoolTrendDashboardMetric =
  components["schemas"]["SchoolTrendDashboardMetricResponse"];
