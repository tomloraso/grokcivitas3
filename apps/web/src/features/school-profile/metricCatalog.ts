export type MetricUnit = "percent" | "count" | "ratio" | "score" | "currency" | "rate";

export type MetricSectionKey =
  | "demographics"
  | "attendance"
  | "behaviour"
  | "workforce"
  | "performance"
  | "area";

export interface MetricCatalogEntry {
  key: string;
  label: string;
  section: MetricSectionKey;
  unit: MetricUnit;
  decimals?: number;
}

export const METRIC_SECTION_ORDER: MetricSectionKey[] = [
  "demographics",
  "attendance",
  "behaviour",
  "workforce",
  "performance",
  "area"
];

export const METRIC_SECTION_LABELS: Record<MetricSectionKey, string> = {
  demographics: "Demographics",
  attendance: "Attendance",
  behaviour: "Behaviour",
  workforce: "Workforce",
  performance: "Performance",
  area: "Area"
};

export const METRIC_CATALOG: Record<string, MetricCatalogEntry> = {
  disadvantaged_pct: {
    key: "disadvantaged_pct",
    label: "Disadvantaged Pupils",
    section: "demographics",
    unit: "percent"
  },
  fsm_pct: {
    key: "fsm_pct",
    label: "Free School Meals",
    section: "demographics",
    unit: "percent"
  },
  fsm6_pct: {
    key: "fsm6_pct",
    label: "FSM6",
    section: "demographics",
    unit: "percent"
  },
  sen_pct: {
    key: "sen_pct",
    label: "SEN Support",
    section: "demographics",
    unit: "percent"
  },
  ehcp_pct: {
    key: "ehcp_pct",
    label: "EHCP",
    section: "demographics",
    unit: "percent"
  },
  eal_pct: {
    key: "eal_pct",
    label: "EAL",
    section: "demographics",
    unit: "percent"
  },
  first_language_english_pct: {
    key: "first_language_english_pct",
    label: "First Language English",
    section: "demographics",
    unit: "percent"
  },
  first_language_unclassified_pct: {
    key: "first_language_unclassified_pct",
    label: "First Language Unclassified",
    section: "demographics",
    unit: "percent"
  },
  male_pct: {
    key: "male_pct",
    label: "Male Pupils",
    section: "demographics",
    unit: "percent"
  },
  female_pct: {
    key: "female_pct",
    label: "Female Pupils",
    section: "demographics",
    unit: "percent"
  },
  pupil_mobility_pct: {
    key: "pupil_mobility_pct",
    label: "Pupil Mobility",
    section: "demographics",
    unit: "percent"
  },
  overall_attendance_pct: {
    key: "overall_attendance_pct",
    label: "Overall Attendance",
    section: "attendance",
    unit: "percent"
  },
  overall_absence_pct: {
    key: "overall_absence_pct",
    label: "Overall Absence",
    section: "attendance",
    unit: "percent"
  },
  persistent_absence_pct: {
    key: "persistent_absence_pct",
    label: "Persistent Absence",
    section: "attendance",
    unit: "percent"
  },
  suspensions_count: {
    key: "suspensions_count",
    label: "Suspensions",
    section: "behaviour",
    unit: "count"
  },
  suspensions_rate: {
    key: "suspensions_rate",
    label: "Suspensions Rate",
    section: "behaviour",
    unit: "rate",
    decimals: 2
  },
  permanent_exclusions_count: {
    key: "permanent_exclusions_count",
    label: "Permanent Exclusions",
    section: "behaviour",
    unit: "count"
  },
  permanent_exclusions_rate: {
    key: "permanent_exclusions_rate",
    label: "Permanent Exclusions Rate",
    section: "behaviour",
    unit: "rate",
    decimals: 2
  },
  pupil_teacher_ratio: {
    key: "pupil_teacher_ratio",
    label: "Pupil to Teacher Ratio",
    section: "workforce",
    unit: "ratio",
    decimals: 1
  },
  supply_staff_pct: {
    key: "supply_staff_pct",
    label: "Supply Staff",
    section: "workforce",
    unit: "percent"
  },
  teachers_3plus_years_pct: {
    key: "teachers_3plus_years_pct",
    label: "Teachers 3+ Years Experience",
    section: "workforce",
    unit: "percent"
  },
  teacher_turnover_pct: {
    key: "teacher_turnover_pct",
    label: "Teacher Turnover",
    section: "workforce",
    unit: "percent"
  },
  qts_pct: {
    key: "qts_pct",
    label: "Qualified Teacher Status",
    section: "workforce",
    unit: "percent"
  },
  qualifications_level6_plus_pct: {
    key: "qualifications_level6_plus_pct",
    label: "Level 6+ Qualifications",
    section: "workforce",
    unit: "percent"
  },
  attainment8_average: {
    key: "attainment8_average",
    label: "Attainment 8",
    section: "performance",
    unit: "score",
    decimals: 1
  },
  progress8_average: {
    key: "progress8_average",
    label: "Progress 8",
    section: "performance",
    unit: "score",
    decimals: 2
  },
  progress8_disadvantaged: {
    key: "progress8_disadvantaged",
    label: "Progress 8 Disadvantaged",
    section: "performance",
    unit: "score",
    decimals: 2
  },
  progress8_not_disadvantaged: {
    key: "progress8_not_disadvantaged",
    label: "Progress 8 Not Disadvantaged",
    section: "performance",
    unit: "score",
    decimals: 2
  },
  progress8_disadvantaged_gap: {
    key: "progress8_disadvantaged_gap",
    label: "Progress 8 Disadvantaged Gap",
    section: "performance",
    unit: "score",
    decimals: 2
  },
  engmath_5_plus_pct: {
    key: "engmath_5_plus_pct",
    label: "English & Maths Grade 5+",
    section: "performance",
    unit: "percent"
  },
  engmath_4_plus_pct: {
    key: "engmath_4_plus_pct",
    label: "English & Maths Grade 4+",
    section: "performance",
    unit: "percent"
  },
  ebacc_entry_pct: {
    key: "ebacc_entry_pct",
    label: "EBacc Entry",
    section: "performance",
    unit: "percent"
  },
  ebacc_5_plus_pct: {
    key: "ebacc_5_plus_pct",
    label: "EBacc Grade 5+",
    section: "performance",
    unit: "percent"
  },
  ebacc_4_plus_pct: {
    key: "ebacc_4_plus_pct",
    label: "EBacc Grade 4+",
    section: "performance",
    unit: "percent"
  },
  ks2_reading_expected_pct: {
    key: "ks2_reading_expected_pct",
    label: "KS2 Reading Expected",
    section: "performance",
    unit: "percent"
  },
  ks2_writing_expected_pct: {
    key: "ks2_writing_expected_pct",
    label: "KS2 Writing Expected",
    section: "performance",
    unit: "percent"
  },
  ks2_maths_expected_pct: {
    key: "ks2_maths_expected_pct",
    label: "KS2 Maths Expected",
    section: "performance",
    unit: "percent"
  },
  ks2_combined_expected_pct: {
    key: "ks2_combined_expected_pct",
    label: "KS2 Combined Expected",
    section: "performance",
    unit: "percent"
  },
  ks2_reading_higher_pct: {
    key: "ks2_reading_higher_pct",
    label: "KS2 Reading Higher",
    section: "performance",
    unit: "percent"
  },
  ks2_writing_higher_pct: {
    key: "ks2_writing_higher_pct",
    label: "KS2 Writing Higher",
    section: "performance",
    unit: "percent"
  },
  ks2_maths_higher_pct: {
    key: "ks2_maths_higher_pct",
    label: "KS2 Maths Higher",
    section: "performance",
    unit: "percent"
  },
  ks2_combined_higher_pct: {
    key: "ks2_combined_higher_pct",
    label: "KS2 Combined Higher",
    section: "performance",
    unit: "percent"
  },
  area_crime_incidents_per_1000: {
    key: "area_crime_incidents_per_1000",
    label: "Crime Incidents per 1,000",
    section: "area",
    unit: "rate",
    decimals: 2
  },
  area_house_price_average: {
    key: "area_house_price_average",
    label: "Average House Price",
    section: "area",
    unit: "currency"
  },
  area_house_price_annual_change_pct: {
    key: "area_house_price_annual_change_pct",
    label: "House Price Annual Change",
    section: "area",
    unit: "percent"
  }
};

export const DEMOGRAPHICS_METRIC_KEYS = [
  "disadvantaged_pct",
  "fsm_pct",
  "fsm6_pct",
  "sen_pct",
  "ehcp_pct",
  "eal_pct",
  "male_pct",
  "female_pct",
  "pupil_mobility_pct",
  "first_language_english_pct",
  "first_language_unclassified_pct"
];

export const ATTENDANCE_METRIC_KEYS = [
  "overall_attendance_pct",
  "overall_absence_pct",
  "persistent_absence_pct"
];

export const BEHAVIOUR_METRIC_KEYS = [
  "suspensions_count",
  "suspensions_rate",
  "permanent_exclusions_count",
  "permanent_exclusions_rate"
];

export const WORKFORCE_METRIC_KEYS = [
  "pupil_teacher_ratio",
  "supply_staff_pct",
  "teachers_3plus_years_pct",
  "teacher_turnover_pct",
  "qts_pct",
  "qualifications_level6_plus_pct"
];

export function getMetricCatalogEntry(metricKey: string): MetricCatalogEntry | null {
  return METRIC_CATALOG[metricKey] ?? null;
}

export function formatMetricValue(
  value: number | null,
  unit: MetricUnit,
  decimalsOverride?: number
): string | null {
  if (value === null) {
    return null;
  }

  switch (unit) {
    case "count":
      return Math.round(value).toLocaleString("en-GB");
    case "currency":
      return new Intl.NumberFormat("en-GB", {
        style: "currency",
        currency: "GBP",
        maximumFractionDigits: 0
      }).format(value);
    case "percent":
      return `${value.toFixed(decimalsOverride ?? 1)}%`;
    case "ratio":
      return value.toFixed(decimalsOverride ?? 1);
    case "rate":
      return value.toFixed(decimalsOverride ?? 2);
    case "score":
      return value.toFixed(decimalsOverride ?? 2);
    default:
      return `${value}`;
  }
}

export function formatMetricDelta(value: number | null, unit: MetricUnit): string | null {
  if (value === null) {
    return null;
  }

  const prefix = value > 0 ? "+" : "";
  switch (unit) {
    case "percent":
      return `${prefix}${value.toFixed(1)} pp`;
    case "currency":
      return `${prefix}${formatMetricValue(value, unit)}`;
    case "count":
      return `${prefix}${Math.round(value).toLocaleString("en-GB")}`;
    case "ratio":
      return `${prefix}${value.toFixed(1)}`;
    case "rate":
      return `${prefix}${value.toFixed(2)}`;
    case "score":
      return `${prefix}${value.toFixed(2)}`;
    default:
      return `${prefix}${value}`;
  }
}

export function formatMetricKeyFallback(metricKey: string): string {
  return metricKey
    .split("_")
    .filter(Boolean)
    .map((token) => token.charAt(0).toUpperCase() + token.slice(1))
    .join(" ");
}
