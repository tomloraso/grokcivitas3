/**
 * Maps backend wire contracts to profile view models.
 * Owns translation from API contracts to UI presentation.
 */
import type { SchoolProfileResponse, SchoolTrendsResponse } from "../../../api/types";
import type {
  DemographicMetricVM,
  DemographicsVM,
  OfstedVM,
  SchoolIdentityVM,
  SchoolProfileVM,
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
    trends: mapTrends(trends),
    unsupportedMetrics: mapUnsupported(profile)
  };
}

export { fallback, fmtDate, fmtPct };
