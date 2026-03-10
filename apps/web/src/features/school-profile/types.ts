import type { MetricSectionKey, MetricUnit } from "./metricCatalog";
import type { SectionAccessVM } from "../premium-access/types";
import type { SavedSchoolStateVM } from "../favourites/types";

export interface SchoolIdentityVM {
  urn: string;
  name: string;
  phase: string;
  type: string;
  status: string;
  postcode: string;
  lat: number;
  lng: number;
  website: string | null;
  telephone: string | null;
  headName: string | null;
  headJobTitle: string | null;
  addressLines: string[];
  ageRangeLabel: string | null;
  gender: string | null;
  religiousCharacter: string | null;
  diocese: string | null;
  admissionsPolicy: string | null;
  sixthForm: string | null;
  nurseryProvision: string | null;
  boarders: string | null;
  giasFsmPct: number | null;
  trustName: string | null;
  trustFlag: string | null;
  federationName: string | null;
  federationFlag: string | null;
  localAuthorityName: string | null;
  localAuthorityCode: string | null;
  urbanRural: string | null;
  numberOfBoys: number | null;
  numberOfGirls: number | null;
  lsoaCode: string | null;
  lsoaName: string | null;
  lastChangedDate: string | null;
}

export interface DemographicMetricVM {
  label: string;
  value: string | null;
  raw: number | null;
  metricKey: string;
  unit: MetricUnit;
}

export interface DemographicsCoverageVM {
  fsmSupported: boolean;
  fsm6Supported: boolean;
  genderSupported: boolean;
  mobilitySupported: boolean;
  sendPrimaryNeedSupported: boolean;
  ethnicitySupported: boolean;
  topLanguagesSupported: boolean;
}

export interface DemographicsEthnicityGroupVM {
  key: string;
  label: string;
  percentage: number | null;
  count: number | null;
  percentageLabel: string | null;
}

export interface DemographicsCategoryVM {
  key: string;
  label: string;
  percentage: number | null;
  count: number | null;
  percentageLabel: string | null;
  rank?: number;
}

export interface DemographicsVM {
  academicYear: string;
  metrics: DemographicMetricVM[];
  coverage: DemographicsCoverageVM;
  ethnicityBreakdown: DemographicsEthnicityGroupVM[];
  sendPrimaryNeeds: DemographicsCategoryVM[];
  topHomeLanguages: DemographicsCategoryVM[];
}

export interface AttendanceLatestVM {
  academicYear: string;
  overallAttendancePct: number | null;
  overallAbsencePct: number | null;
  persistentAbsencePct: number | null;
}

export interface BehaviourLatestVM {
  academicYear: string;
  suspensionsCount: number | null;
  suspensionsRate: number | null;
  permanentExclusionsCount: number | null;
  permanentExclusionsRate: number | null;
}

export interface WorkforceLatestVM {
  academicYear: string;
  pupilTeacherRatio: number | null;
  supplyStaffPct: number | null;
  teachers3plusYearsPct: number | null;
  teacherTurnoverPct: number | null;
  qtsPct: number | null;
  qualificationsLevel6PlusPct: number | null;
}

export interface FinanceLatestVM {
  academicYear: string;
  totalIncomeGbp: number | null;
  totalExpenditureGbp: number | null;
  incomePerPupilGbp: number | null;
  expenditurePerPupilGbp: number | null;
  totalStaffCostsGbp: number | null;
  staffCostsPctOfExpenditure: number | null;
  revenueReserveGbp: number | null;
  revenueReservePerPupilGbp: number | null;
}

export interface LeadershipSnapshotVM {
  headteacherName: string | null;
  headteacherStartDate: string | null;
  headteacherTenureYears: number | null;
  leadershipTurnoverScore: number | null;
}

export interface PerformanceYearVM {
  academicYear: string;
  attainment8Average: number | null;
  progress8Average: number | null;
  progress8Disadvantaged: number | null;
  progress8NotDisadvantaged: number | null;
  progress8DisadvantagedGap: number | null;
  engmath5PlusPct: number | null;
  engmath4PlusPct: number | null;
  ebaccEntryPct: number | null;
  ebacc5PlusPct: number | null;
  ebacc4PlusPct: number | null;
  ks2ReadingExpectedPct: number | null;
  ks2WritingExpectedPct: number | null;
  ks2MathsExpectedPct: number | null;
  ks2CombinedExpectedPct: number | null;
  ks2ReadingHigherPct: number | null;
  ks2WritingHigherPct: number | null;
  ks2MathsHigherPct: number | null;
  ks2CombinedHigherPct: number | null;
}

export interface PerformanceVM {
  latest: PerformanceYearVM | null;
  history: PerformanceYearVM[];
}

export interface OfstedVM {
  ratingCode: string | null;
  ratingLabel: string | null;
  inspectionDate: string | null;
  publicationDate: string | null;
  latestOeifInspectionDate: string | null;
  latestOeifPublicationDate: string | null;
  latestUngradedInspectionDate: string | null;
  latestUngradedPublicationDate: string | null;
  mostRecentInspectionDate: string | null;
  daysSinceMostRecentInspection: number | null;
  qualityOfEducationCode: string | null;
  qualityOfEducationLabel: string | null;
  behaviourAndAttitudesCode: string | null;
  behaviourAndAttitudesLabel: string | null;
  personalDevelopmentCode: string | null;
  personalDevelopmentLabel: string | null;
  leadershipAndManagementCode: string | null;
  leadershipAndManagementLabel: string | null;
  isGraded: boolean;
  ungradedOutcome: string | null;
  providerPageUrl: string | null;
}

export interface OfstedTimelineEventVM {
  inspectionNumber: string;
  inspectionDate: string;
  publicationDate: string | null;
  inspectionType: string;
  outcomeLabel: string | null;
  headlineOutcome: string | null;
  categoryOfConcern: string | null;
}

export interface OfstedTimelineCoverageVM {
  isPartialHistory: boolean;
  earliestEventDate: string | null;
  latestEventDate: string | null;
  eventsCount: number;
}

export interface OfstedTimelineVM {
  events: OfstedTimelineEventVM[];
  coverage: OfstedTimelineCoverageVM;
}

export interface AreaDeprivationDomainVM {
  key: string;
  label: string;
  score: number | null;
  rank: number | null;
  decile: number | null;
}

export interface AreaDeprivationVM {
  lsoaCode: string;
  imdScore: number;
  imdRank: number;
  imdDecile: number;
  idaciScore: number;
  idaciDecile: number;
  populationTotal: number | null;
  localAuthorityDistrictCode: string | null;
  localAuthorityDistrictName: string | null;
  sourceRelease: string;
  domains: AreaDeprivationDomainVM[];
}

export interface AreaCrimeCategoryVM {
  category: string;
  incidentCount: number;
}

export interface AreaCrimeAnnualRateVM {
  year: number;
  totalIncidents: number;
  incidentsPer1000: number | null;
}

export interface AreaCrimeVM {
  radiusMiles: number;
  latestMonth: string;
  totalIncidents: number;
  populationDenominator: number | null;
  incidentsPer1000: number | null;
  annualIncidentsPer1000: AreaCrimeAnnualRateVM[];
  categories: AreaCrimeCategoryVM[];
}

export interface AreaHousePricePointVM {
  month: string;
  averagePrice: number;
  annualChangePct: number | null;
  monthlyChangePct: number | null;
}

export interface AreaHousePricesVM {
  areaCode: string;
  areaName: string;
  latestMonth: string;
  averagePrice: number;
  annualChangePct: number | null;
  monthlyChangePct: number | null;
  threeYearChangePct: number | null;
  trend: AreaHousePricePointVM[];
}

export interface AreaContextCoverageVM {
  hasDeprivation: boolean;
  hasCrime: boolean;
  crimeMonthsAvailable: number;
  hasHousePrices: boolean;
  housePriceMonthsAvailable: number;
}

export interface AreaContextVM {
  deprivation: AreaDeprivationVM | null;
  crime: AreaCrimeVM | null;
  housePrices: AreaHousePricesVM | null;
  coverage: AreaContextCoverageVM;
}

export interface TrendPointVM {
  year: string;
  value: number | null;
  delta: number | null;
  direction: "up" | "down" | "flat" | null;
}

export interface TrendSeriesVM {
  label: string;
  metricKey: string;
  unit: MetricUnit;
  points: TrendPointVM[];
  latestDelta: number | null;
  latestDirection: "up" | "down" | "flat" | null;
}

export interface TrendsSectionCompletenessVM {
  demographics: SectionCompletenessVM;
  attendance: SectionCompletenessVM;
  behaviour: SectionCompletenessVM;
  workforce: SectionCompletenessVM;
  finance: SectionCompletenessVM;
}

export interface TrendsVM {
  yearsAvailable: string[];
  isPartialHistory: boolean;
  yearsCount: number;
  series: TrendSeriesVM[];
  sectionCompleteness: TrendsSectionCompletenessVM;
}

export interface BenchmarkTrendPointVM {
  academicYear: string;
  schoolValue: number | null;
  nationalValue: number | null;
  localValue: number | null;
  schoolVsNationalDelta: number | null;
  schoolVsLocalDelta: number | null;
}

export interface BenchmarkMetricVM {
  metricKey: string;
  label: string;
  section: MetricSectionKey;
  unit: MetricUnit;
  academicYear: string;
  schoolValue: number | null;
  nationalValue: number | null;
  localValue: number | null;
  schoolVsNationalDelta: number | null;
  schoolVsLocalDelta: number | null;
  localScope: "local_authority_district" | "phase";
  localAreaCode: string;
  localAreaLabel: string;
  trendPoints: BenchmarkTrendPointVM[];
}

export interface BenchmarkSectionVM {
  key: MetricSectionKey;
  label: string;
  metrics: BenchmarkMetricVM[];
}

export interface BenchmarkDashboardVM {
  yearsAvailable: string[];
  sections: BenchmarkSectionVM[];
  completeness: SectionCompletenessVM | null;
}

export type SectionCompletenessStatus = "available" | "partial" | "unavailable";

export type SectionCompletenessReasonCode =
  | "source_missing"
  | "insufficient_years_published"
  | "source_not_in_catalog"
  | "source_file_missing_for_year"
  | "source_schema_incompatible_for_year"
  | "partial_metric_coverage"
  | "source_not_provided"
  | "rejected_by_validation"
  | "not_joined_yet"
  | "pipeline_failed_recently"
  | "not_applicable"
  | "source_coverage_gap"
  | "stale_after_school_refresh"
  | "no_incidents_in_radius";

export type SectionCompletenessMessageKey =
  | "missing"
  | "insufficientYearsPublished"
  | "sourceNotInCatalog"
  | "sourceFileMissingForYear"
  | "sourceSchemaIncompatibleForYear"
  | "partialMetricCoverage"
  | "notProvided"
  | "validationRejected"
  | "notJoinedYet"
  | "pipelineFailedRecently"
  | "notApplicable"
  | "sourceCoverageGap"
  | "staleAfterSchoolRefresh"
  | "noIncidentsInRadius";

export interface SectionCompletenessVM {
  status: SectionCompletenessStatus;
  reasonCode: SectionCompletenessReasonCode | null;
  messageKey: SectionCompletenessMessageKey | null;
  lastUpdatedAt: string | null;
  yearsAvailable: string[] | null;
}

export interface ProfileCompletenessVM {
  demographics: SectionCompletenessVM;
  attendance: SectionCompletenessVM;
  behaviour: SectionCompletenessVM;
  workforce: SectionCompletenessVM;
  finance: SectionCompletenessVM;
  leadership: SectionCompletenessVM;
  performance: SectionCompletenessVM;
  trends: SectionCompletenessVM;
  ofstedLatest: SectionCompletenessVM;
  ofstedTimeline: SectionCompletenessVM;
  areaDeprivation: SectionCompletenessVM;
  areaCrime: SectionCompletenessVM;
  areaHousePrices: SectionCompletenessVM;
}

export interface UnsupportedMetricVM {
  label: string;
}

export interface AnalystSectionVM {
  access: SectionAccessVM;
  text: string | null;
  teaserText: string | null;
  disclaimer: string | null;
}

export interface NeighbourhoodSectionVM {
  access: SectionAccessVM;
  areaContext: AreaContextVM | null;
  teaserText: string | null;
}

export interface SchoolProfileVM {
  school: SchoolIdentityVM;
  savedState: SavedSchoolStateVM;
  overviewText: string | null;
  analyst: AnalystSectionVM;
  demographics: DemographicsVM | null;
  attendance: AttendanceLatestVM | null;
  behaviour: BehaviourLatestVM | null;
  workforce: WorkforceLatestVM | null;
  finance: FinanceLatestVM | null;
  leadership: LeadershipSnapshotVM | null;
  performance: PerformanceVM | null;
  ofsted: OfstedVM | null;
  ofstedTimeline: OfstedTimelineVM;
  neighbourhood: NeighbourhoodSectionVM;
  trends: TrendsVM | null;
  benchmarkDashboard: BenchmarkDashboardVM | null;
  completeness: ProfileCompletenessVM;
  unsupportedMetrics: UnsupportedMetricVM[];
}
