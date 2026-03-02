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

export interface DemographicsVM {
  academicYear: string;
  metrics: DemographicMetricVM[];
  coverage: DemographicsCoverageVM;
}

/* ------------------------------------------------------------------ */
/* Ofsted                                                              */
/* ------------------------------------------------------------------ */

export interface OfstedVM {
  ratingCode: string | null;
  ratingLabel: string | null;
  inspectionDate: string | null;
  publicationDate: string | null;
  isGraded: boolean;
  ungradedOutcome: string | null;
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
  ofsted: OfstedVM | null;
  trends: TrendsVM | null;
  unsupportedMetrics: UnsupportedMetricVM[];
}
