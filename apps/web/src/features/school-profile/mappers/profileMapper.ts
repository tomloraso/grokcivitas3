/**
 * Maps backend wire contracts to profile view models.
 * Owns translation from API contracts to UI presentation.
 */
import type { SchoolProfileResponse, SchoolTrendsResponse } from "../../../api/types";
import type {
  AreaContextVM,
  DemographicMetricVM,
  DemographicsVM,
  OfstedVM,
  OfstedTimelineVM,
  ProfileCompletenessVM,
  SchoolIdentityVM,
  SchoolProfileVM,
  SectionCompletenessMessageKey,
  SectionCompletenessReasonCode,
  SectionCompletenessVM,
  TrendPointVM,
  TrendSeriesVM,
  TrendsVM,
  UnsupportedMetricVM
} from "../types";

function fmtPct(value: number | null): string | null {
  if (value === null) {
    return null;
  }
  return `${value.toFixed(1)}%`;
}

function fallback(value: string | null | undefined, placeholder: string): string {
  return value?.trim() ? value : placeholder;
}

function fmtDate(iso: string | null): string | null {
  if (!iso) {
    return null;
  }

  const date = new Date(`${iso}T00:00:00Z`);
  if (Number.isNaN(date.getTime())) {
    return iso;
  }

  return date.toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC"
  });
}

function fmtMonth(month: string): string {
  const match = /^(\d{4})-(\d{2})$/.exec(month);
  if (!match) {
    return month;
  }

  const year = Number(match[1]);
  const monthIndex = Number(match[2]) - 1;
  const date = new Date(Date.UTC(year, monthIndex, 1));
  if (Number.isNaN(date.getTime())) {
    return month;
  }

  return date.toLocaleDateString("en-GB", {
    month: "short",
    year: "numeric",
    timeZone: "UTC"
  });
}

function fmtDateTime(iso: string | null | undefined): string | null {
  if (!iso) {
    return null;
  }

  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return iso;
  }

  return date.toLocaleString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC"
  });
}

function dateKey(iso: string): number {
  const parsed = Date.parse(`${iso}T00:00:00Z`);
  return Number.isNaN(parsed) ? -1 : parsed;
}

function formatCrimeCategory(category: string): string {
  return category
    .split(/[-_]/g)
    .filter(Boolean)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
}

interface MetricDef {
  key: string;
  label: string;
  field:
    | "disadvantaged_pct"
    | "fsm_pct"
    | "sen_pct"
    | "ehcp_pct"
    | "eal_pct"
    | "first_language_english_pct"
    | "first_language_unclassified_pct";
}

const DEMOGRAPHIC_METRICS: MetricDef[] = [
  { key: "disadvantaged_pct", label: "Disadvantaged", field: "disadvantaged_pct" },
  { key: "fsm_pct", label: "Free School Meals", field: "fsm_pct" },
  { key: "sen_pct", label: "SEN Support", field: "sen_pct" },
  { key: "ehcp_pct", label: "EHCP", field: "ehcp_pct" },
  { key: "eal_pct", label: "English as Additional Language", field: "eal_pct" },
  {
    key: "first_language_english_pct",
    label: "First Language English",
    field: "first_language_english_pct"
  },
  {
    key: "first_language_unclassified_pct",
    label: "First Language Unclassified",
    field: "first_language_unclassified_pct"
  }
];

const TREND_METRIC_LABELS: Record<string, string> = {
  disadvantaged_pct: "Disadvantaged",
  sen_pct: "SEN Support",
  ehcp_pct: "EHCP",
  eal_pct: "English as Additional Language"
};

const REASON_MESSAGE_KEYS: Record<SectionCompletenessReasonCode, SectionCompletenessMessageKey> = {
  source_missing: "missing",
  source_not_provided: "notProvided",
  rejected_by_validation: "validationRejected",
  not_joined_yet: "notJoinedYet",
  pipeline_failed_recently: "pipelineFailedRecently",
  not_applicable: "notApplicable"
};

interface SectionCompletenessContract {
  status: "available" | "partial" | "unavailable";
  reason_code: SectionCompletenessReasonCode | null;
  last_updated_at: string | null;
  years_available?: string[] | null;
}

export function mapCompletenessReasonToMessageKey(
  reasonCode: SectionCompletenessReasonCode | null
): SectionCompletenessMessageKey | null {
  if (!reasonCode) {
    return null;
  }
  return REASON_MESSAGE_KEYS[reasonCode];
}

function mapSectionCompleteness(section: SectionCompletenessContract): SectionCompletenessVM {
  return {
    status: section.status,
    reasonCode: section.reason_code,
    messageKey: mapCompletenessReasonToMessageKey(section.reason_code),
    lastUpdatedAt: fmtDateTime(section.last_updated_at),
    yearsAvailable: section.years_available ?? null
  };
}

function mapSchool(profile: SchoolProfileResponse): SchoolIdentityVM {
  const s = profile.school;
  return {
    urn: s.urn,
    name: s.name,
    phase: fallback(s.phase, "Unknown"),
    type: fallback(s.type, "Unknown"),
    status: fallback(s.status, "Unknown"),
    postcode: fallback(s.postcode, "Unknown"),
    lat: s.lat,
    lng: s.lng
  };
}

function mapDemographics(profile: SchoolProfileResponse): DemographicsVM | null {
  const d = profile.demographics_latest;
  if (!d) {
    return null;
  }

  const metrics: DemographicMetricVM[] = DEMOGRAPHIC_METRICS.map((def) => ({
    label: def.label,
    value: fmtPct(d[def.field]),
    raw: d[def.field],
    metricKey: def.key
  }));

  return {
    academicYear: d.academic_year,
    metrics,
    coverage: {
      fsmSupported: d.coverage.fsm_supported,
      ethnicitySupported: d.coverage.ethnicity_supported,
      topLanguagesSupported: d.coverage.top_languages_supported
    }
  };
}

function mapOfsted(profile: SchoolProfileResponse): OfstedVM | null {
  const o = profile.ofsted_latest;
  if (!o) {
    return null;
  }

  return {
    ratingCode: o.overall_effectiveness_code,
    ratingLabel: o.overall_effectiveness_label,
    inspectionDate: fmtDate(o.inspection_start_date),
    publicationDate: fmtDate(o.publication_date),
    isGraded: o.is_graded,
    ungradedOutcome: o.ungraded_outcome
  };
}

function mapOfstedTimeline(profile: SchoolProfileResponse): OfstedTimelineVM {
  const timeline = profile.ofsted_timeline;

  if (!timeline) {
    return {
      events: [],
      coverage: {
        isPartialHistory: true,
        earliestEventDate: null,
        latestEventDate: null,
        eventsCount: 0
      }
    };
  }

  const events = [...(timeline.events || [])]
    .sort(
      (left, right) =>
        dateKey(right.inspection_start_date) - dateKey(left.inspection_start_date)
    )
    .map((event) => ({
      inspectionNumber: event.inspection_number,
      inspectionDate: fmtDate(event.inspection_start_date) ?? event.inspection_start_date,
      publicationDate: fmtDate(event.publication_date),
      inspectionType: fallback(event.inspection_type, "Inspection"),
      outcomeLabel: event.overall_effectiveness_label,
      headlineOutcome: event.headline_outcome_text,
      categoryOfConcern: event.category_of_concern
    }));

  return {
    events,
    coverage: {
      isPartialHistory: timeline.coverage.is_partial_history,
      earliestEventDate: fmtDate(timeline.coverage.earliest_event_date),
      latestEventDate: fmtDate(timeline.coverage.latest_event_date),
      eventsCount: timeline.coverage.events_count
    }
  };
}

function mapAreaContext(profile: SchoolProfileResponse): AreaContextVM {
  const area = profile.area_context;

  if (!area) {
    return {
      deprivation: null,
      crime: null,
      coverage: {
        hasDeprivation: false,
        hasCrime: false,
        crimeMonthsAvailable: 0
      }
    };
  }

  return {
    deprivation: area.deprivation
      ? {
          lsoaCode: area.deprivation.lsoa_code,
          imdDecile: area.deprivation.imd_decile,
          idaciScore: area.deprivation.idaci_score,
          idaciDecile: area.deprivation.idaci_decile,
          sourceRelease: area.deprivation.source_release
        }
      : null,
    crime: area.crime
      ? {
          radiusMiles: area.crime.radius_miles,
          latestMonth: fmtMonth(area.crime.latest_month),
          totalIncidents: area.crime.total_incidents,
          categories: [...area.crime.categories]
            .sort(
              (left, right) =>
                right.incident_count - left.incident_count ||
                left.category.localeCompare(right.category)
            )
            .map((category) => ({
              category: formatCrimeCategory(category.category),
              incidentCount: category.incident_count
            }))
        }
      : null,
    coverage: {
      hasDeprivation: area.coverage.has_deprivation,
      hasCrime: area.coverage.has_crime,
      crimeMonthsAvailable: area.coverage.crime_months_available
    }
  };
}

function mapTrends(trends: SchoolTrendsResponse | null): TrendsVM | null {
  if (!trends) {
    return null;
  }

  const series: TrendSeriesVM[] = Object.entries(trends.series)
    .filter(([key]) => key in TREND_METRIC_LABELS)
    .map(([key, points]) => {
      const mappedPoints: TrendPointVM[] = points.map((p) => ({
        year: p.academic_year,
        value: p.value,
        delta: p.delta,
        direction: p.direction
      }));

      const latest = mappedPoints.length > 0 ? mappedPoints[mappedPoints.length - 1] : null;

      return {
        label: TREND_METRIC_LABELS[key],
        metricKey: key,
        points: mappedPoints,
        latestDelta: latest?.delta ?? null,
        latestDirection: latest?.direction ?? null
      };
    });

  return {
    yearsAvailable: trends.years_available,
    isPartialHistory: trends.history_quality.is_partial_history,
    yearsCount: trends.history_quality.years_count,
    series
  };
}

function mapCompleteness(
  profile: SchoolProfileResponse,
  trends: SchoolTrendsResponse | null
): ProfileCompletenessVM {
  const trendsCompleteness: SectionCompletenessVM = trends
    ? mapSectionCompleteness(trends.completeness)
    : {
        status: "unavailable",
        reasonCode: "pipeline_failed_recently",
        messageKey: mapCompletenessReasonToMessageKey("pipeline_failed_recently"),
        lastUpdatedAt: null,
        yearsAvailable: null
      };

  return {
    demographics: mapSectionCompleteness(profile.completeness.demographics),
    trends: trendsCompleteness,
    ofstedLatest: mapSectionCompleteness(profile.completeness.ofsted_latest),
    ofstedTimeline: mapSectionCompleteness(profile.completeness.ofsted_timeline),
    areaDeprivation: mapSectionCompleteness(profile.completeness.area_deprivation),
    areaCrime: mapSectionCompleteness(profile.completeness.area_crime)
  };
}

function mapUnsupported(profile: SchoolProfileResponse): UnsupportedMetricVM[] {
  const coverage = profile.demographics_latest?.coverage;
  if (!coverage) {
    return [];
  }

  const unsupported: UnsupportedMetricVM[] = [];
  if (!coverage.fsm_supported) {
    unsupported.push({ label: "Free School Meals (direct)" });
  }
  if (!coverage.ethnicity_supported) {
    unsupported.push({ label: "Ethnicity breakdown" });
  }
  if (!coverage.top_languages_supported) {
    unsupported.push({ label: "Top non-English languages" });
  }
  return unsupported;
}

export function mapProfileToVM(
  profile: SchoolProfileResponse,
  trends: SchoolTrendsResponse | null
): SchoolProfileVM {
  return {
    school: mapSchool(profile),
    demographics: mapDemographics(profile),
    ofsted: mapOfsted(profile),
    ofstedTimeline: mapOfstedTimeline(profile),
    areaContext: mapAreaContext(profile),
    trends: mapTrends(trends),
    completeness: mapCompleteness(profile, trends),
    unsupportedMetrics: mapUnsupported(profile)
  };
}

export { fallback, fmtDate, fmtDateTime, fmtMonth, fmtPct };
