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

export type SchoolProfileResponse =
  components["schemas"]["SchoolProfileResponse"];

export type SchoolProfileSchool =
  components["schemas"]["SchoolProfileSchoolResponse"];

export type SchoolProfileDemographicsLatest =
  components["schemas"]["SchoolProfileDemographicsLatestResponse"];

export type SchoolProfileDemographicsCoverage =
  components["schemas"]["SchoolProfileDemographicsCoverageResponse"];

export type SchoolProfileOfstedLatest =
  components["schemas"]["SchoolProfileOfstedLatestResponse"];

export type SchoolProfileAttendanceLatest =
  components["schemas"]["SchoolProfileAttendanceLatestResponse"];

export type SchoolProfileBehaviourLatest =
  components["schemas"]["SchoolProfileBehaviourLatestResponse"];

export type SchoolProfileWorkforceLatest =
  components["schemas"]["SchoolProfileWorkforceLatestResponse"];

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
  components["schemas"]["SchoolTrendsResponse"];

export type SchoolTrendsSeries =
  components["schemas"]["SchoolTrendsSeriesResponse"];

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
