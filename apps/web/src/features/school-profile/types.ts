/**
 * View-model types for the school profile feature.
 * Mapped from backend wire contracts at the feature boundary.
 */

/* ------------------------------------------------------------------ */
/* School identity                                                     */
/* ------------------------------------------------------------------ */

export interface SchoolIdentityVM {
  urn: string;
  name: string;
  phase: string;
  type: string;
  status: string;
  postcode: string;
  lat: number;
  lng: number;
}

/* ------------------------------------------------------------------ */
/* Demographics                                                        */
/* ------------------------------------------------------------------ */

export interface DemographicMetricVM {
  label: string;
  /** Formatted display value (e.g. "17.2%") or null when data unavailable */
  value: string | null;
  /** Raw numeric value for sparkline / delta use */
  raw: number | null;
  /** Metric key for matching to trends series */
  metricKey: string;
}

export interface DemographicsCoverageVM {
  fsmSupported: boolean;
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

export interface DemographicsVM {
  academicYear: string;
  metrics: DemographicMetricVM[];
  coverage: DemographicsCoverageVM;
  ethnicityBreakdown: DemographicsEthnicityGroupVM[];
}

/* ------------------------------------------------------------------ */
/* School performance                                                  */
/* ------------------------------------------------------------------ */

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

/* ------------------------------------------------------------------ */
/* Ofsted                                                              */
/* ------------------------------------------------------------------ */

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

/* ------------------------------------------------------------------ */
/* Area context                                                        */
/* ------------------------------------------------------------------ */

export interface AreaDeprivationVM {
  lsoaCode: string;
  imdScore: number;
  imdRank: number;
  imdDecile: number;
  idaciScore: number;
  idaciDecile: number;
  sourceRelease: string;
}

export interface AreaCrimeCategoryVM {
  category: string;
  incidentCount: number;
}

export interface AreaCrimeVM {
  radiusMiles: number;
  latestMonth: string;
  totalIncidents: number;
  categories: AreaCrimeCategoryVM[];
}

export interface AreaContextCoverageVM {
  hasDeprivation: boolean;
  hasCrime: boolean;
  crimeMonthsAvailable: number;
}

export interface AreaContextVM {
  deprivation: AreaDeprivationVM | null;
  crime: AreaCrimeVM | null;
  coverage: AreaContextCoverageVM;
}

/* ------------------------------------------------------------------ */
/* Trends                                                              */
/* ------------------------------------------------------------------ */

export interface TrendPointVM {
  year: string;
  value: number | null;
  delta: number | null;
  direction: "up" | "down" | "flat" | null;
}

export interface TrendSeriesVM {
  label: string;
  metricKey: string;
  points: TrendPointVM[];
  /** Latest delta for stat card footer */
  latestDelta: number | null;
  latestDirection: "up" | "down" | "flat" | null;
}

export interface TrendsVM {
  yearsAvailable: string[];
  isPartialHistory: boolean;
  yearsCount: number;
  series: TrendSeriesVM[];
}

/* ------------------------------------------------------------------ */
/* Completeness                                                        */
/* ------------------------------------------------------------------ */

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
  performance: SectionCompletenessVM;
  trends: SectionCompletenessVM;
  ofstedLatest: SectionCompletenessVM;
  ofstedTimeline: SectionCompletenessVM;
  areaDeprivation: SectionCompletenessVM;
  areaCrime: SectionCompletenessVM;
}

/* ------------------------------------------------------------------ */
/* Unsupported metrics                                                 */
/* ------------------------------------------------------------------ */

export interface UnsupportedMetricVM {
  label: string;
}

/* ------------------------------------------------------------------ */
/* Composite profile VM                                                */
/* ------------------------------------------------------------------ */

export interface SchoolProfileVM {
  school: SchoolIdentityVM;
  demographics: DemographicsVM | null;
  performance: PerformanceVM | null;
  ofsted: OfstedVM | null;
  ofstedTimeline: OfstedTimelineVM;
  areaContext: AreaContextVM;
  trends: TrendsVM | null;
  completeness: ProfileCompletenessVM;
  unsupportedMetrics: UnsupportedMetricVM[];
}
