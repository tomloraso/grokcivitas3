export type MetricUnit = "percent" | "count" | "ratio" | "score" | "currency" | "rate";

export type MetricSectionKey =
  | "demographics"
  | "finance"
  | "attendance"
  | "behaviour"
  | "workforce"
  | "performance"
  | "area";

export interface MetricCatalogEntry {
  key: string;
  label: string;
  description?: string;
  section: MetricSectionKey;
  unit: MetricUnit;
  decimals?: number;
}

export const METRIC_SECTION_ORDER: MetricSectionKey[] = [
  "demographics",
  "finance",
  "attendance",
  "behaviour",
  "workforce",
  "performance",
  "area"
];

export const METRIC_SECTION_LABELS: Record<MetricSectionKey, string> = {
  demographics: "Demographics",
  finance: "Finance",
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
    description: "Pupils eligible for Pupil Premium funding — includes those ever on free school meals, looked-after children, and children of service personnel.",
    section: "demographics",
    unit: "percent"
  },
  fsm_pct: {
    key: "fsm_pct",
    label: "Free School Meals",
    description: "Pupils currently registered as eligible for free school meals, used as a direct indicator of low household income.",
    section: "demographics",
    unit: "percent"
  },
  fsm6_pct: {
    key: "fsm6_pct",
    label: "Ever Eligible for Free Meals",
    description: "Pupils who have been eligible for free school meals at any point in the last 6 years — a wider measure of economic disadvantage than current eligibility alone.",
    section: "demographics",
    unit: "percent"
  },
  sen_pct: {
    key: "sen_pct",
    label: "Additional Needs Support",
    description: "Pupils receiving SEN (Special Educational Needs) support at school level, without a formal Education Health & Care Plan. The school provides targeted help within class or in small groups.",
    section: "demographics",
    unit: "percent"
  },
  ehcp_pct: {
    key: "ehcp_pct",
    label: "Education Health & Care Plan",
    description: "Pupils with a formal EHCP — a legal document that describes a child's special educational needs and specifies the support they must receive.",
    section: "demographics",
    unit: "percent"
  },
  eal_pct: {
    key: "eal_pct",
    label: "English as Additional Language",
    description: "Pupils whose first or home language is not English. This does not indicate English proficiency — many pupils with EAL are fluent English speakers.",
    section: "demographics",
    unit: "percent"
  },
  first_language_english_pct: {
    key: "first_language_english_pct",
    label: "First Language English",
    description: "Pupils whose home language is recorded as English.",
    section: "demographics",
    unit: "percent"
  },
  first_language_unclassified_pct: {
    key: "first_language_unclassified_pct",
    label: "Language Unrecorded",
    description: "Pupils whose home language has not been recorded or classified in the school census.",
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
    description: "Pupils who joined or left the school mid-year, excluding those who moved at the normal transition point. High mobility can indicate instability in the school community.",
    section: "demographics",
    unit: "percent"
  },
  income_per_pupil_gbp: {
    key: "income_per_pupil_gbp",
    label: "Income per Pupil",
    description: "Total income divided by full-time equivalent pupils. Helps compare school income levels on a like-for-like basis.",
    section: "finance",
    unit: "currency"
  },
  expenditure_per_pupil_gbp: {
    key: "expenditure_per_pupil_gbp",
    label: "Expenditure per Pupil",
    description: "Total expenditure divided by full-time equivalent pupils. Useful for comparing school spending levels across different school sizes.",
    section: "finance",
    unit: "currency"
  },
  staff_costs_pct_of_expenditure: {
    key: "staff_costs_pct_of_expenditure",
    label: "Staff Costs Share of Expenditure",
    description: "The proportion of total expenditure spent on staff costs. This shows how much of the school's spending goes on staffing.",
    section: "finance",
    unit: "percent"
  },
  revenue_reserve_per_pupil_gbp: {
    key: "revenue_reserve_per_pupil_gbp",
    label: "Revenue Reserve per Pupil",
    description: "Revenue reserves divided by full-time equivalent pupils. Gives context on retained financial headroom relative to school size.",
    section: "finance",
    unit: "currency"
  },
  teaching_staff_costs_per_pupil_gbp: {
    key: "teaching_staff_costs_per_pupil_gbp",
    label: "Teaching Staff Costs per Pupil",
    description: "Teaching staff costs divided by full-time equivalent pupils. Indicates direct classroom staffing spend relative to school size.",
    section: "finance",
    unit: "currency"
  },
  overall_attendance_pct: {
    key: "overall_attendance_pct",
    label: "Overall Attendance",
    description: "The percentage of possible school sessions attended by pupils. The national expected level is 96% or above.",
    section: "attendance",
    unit: "percent"
  },
  overall_absence_pct: {
    key: "overall_absence_pct",
    label: "Overall Absence",
    description: "The percentage of possible sessions missed, including both authorised (e.g. illness) and unauthorised absences.",
    section: "attendance",
    unit: "percent"
  },
  persistent_absence_pct: {
    key: "persistent_absence_pct",
    label: "Persistent Absence",
    description: "Pupils who miss 10% or more of possible school sessions across the year. Persistent absence is a key government indicator of disengagement.",
    section: "attendance",
    unit: "percent"
  },
  suspensions_count: {
    key: "suspensions_count",
    label: "Suspensions",
    description: "Total number of fixed-period suspensions issued during the year. One pupil can receive multiple suspensions.",
    section: "behaviour",
    unit: "count"
  },
  suspensions_rate: {
    key: "suspensions_rate",
    label: "Suspension Rate",
    description: "Suspensions per 100 pupils enrolled. Allows fair comparison between schools of different sizes.",
    section: "behaviour",
    unit: "rate",
    decimals: 2
  },
  permanent_exclusions_count: {
    key: "permanent_exclusions_count",
    label: "Permanent Exclusions",
    description: "Total number of pupils permanently excluded during the year — removed from the school roll and unable to return.",
    section: "behaviour",
    unit: "count"
  },
  permanent_exclusions_rate: {
    key: "permanent_exclusions_rate",
    label: "Permanent Exclusion Rate",
    description: "Permanent exclusions per 100 pupils. Allows fair comparison between schools of different sizes.",
    section: "behaviour",
    unit: "rate",
    decimals: 2
  },
  pupil_teacher_ratio: {
    key: "pupil_teacher_ratio",
    label: "Pupil to Teacher Ratio",
    description: "The number of pupils per full-time equivalent teacher. Lower ratios generally mean smaller class sizes and more teacher attention per pupil.",
    section: "workforce",
    unit: "ratio",
    decimals: 1
  },
  supply_staff_pct: {
    key: "supply_staff_pct",
    label: "Supply Staff",
    description: "The proportion of teaching covered by supply (temporary) teachers. Higher levels may indicate staffing challenges or high teacher turnover.",
    section: "workforce",
    unit: "percent"
  },
  teachers_3plus_years_pct: {
    key: "teachers_3plus_years_pct",
    label: "Experienced Teachers",
    description: "Teachers with 3 or more years of service at any school. Higher proportions generally indicate a stable, experienced workforce.",
    section: "workforce",
    unit: "percent"
  },
  teacher_turnover_pct: {
    key: "teacher_turnover_pct",
    label: "Teacher Turnover",
    description: "The proportion of teachers who left the school during the year. High turnover can affect continuity for pupils.",
    section: "workforce",
    unit: "percent"
  },
  qts_pct: {
    key: "qts_pct",
    label: "Qualified Teachers",
    description: "Proportion of teachers holding Qualified Teacher Status (QTS) — the formal qualification required to teach in state schools in England.",
    section: "workforce",
    unit: "percent"
  },
  qualifications_level6_plus_pct: {
    key: "qualifications_level6_plus_pct",
    label: "Degree-Level Staff",
    description: "Proportion of teachers holding a Level 6 or above qualification, equivalent to a bachelor's degree or higher.",
    section: "workforce",
    unit: "percent"
  },
  attainment8_average: {
    key: "attainment8_average",
    label: "Attainment 8",
    description: "Average total score across 8 GCSE subjects including English, maths, and chosen options. The national average is around 46. Higher is better.",
    section: "performance",
    unit: "score",
    decimals: 1
  },
  progress8_average: {
    key: "progress8_average",
    label: "Progress 8",
    description: "How much progress pupils made between age 11 and 16 compared to similar pupils nationally. 0 is average; positive means above average progress; negative means below.",
    section: "performance",
    unit: "score",
    decimals: 2
  },
  progress8_disadvantaged: {
    key: "progress8_disadvantaged",
    label: "Progress 8 (Disadvantaged)",
    description: "Progress 8 score for pupils who have been eligible for free school meals in the last 6 years.",
    section: "performance",
    unit: "score",
    decimals: 2
  },
  progress8_not_disadvantaged: {
    key: "progress8_not_disadvantaged",
    label: "Progress 8 (Non-Disadvantaged)",
    description: "Progress 8 score for pupils who have not been eligible for free school meals in the last 6 years.",
    section: "performance",
    unit: "score",
    decimals: 2
  },
  progress8_disadvantaged_gap: {
    key: "progress8_disadvantaged_gap",
    label: "Disadvantage Progress Gap",
    description: "The gap in Progress 8 scores between disadvantaged and non-disadvantaged pupils. Smaller gaps indicate more equitable outcomes across different backgrounds.",
    section: "performance",
    unit: "score",
    decimals: 2
  },
  engmath_5_plus_pct: {
    key: "engmath_5_plus_pct",
    label: "English & Maths Strong Pass",
    description: "Pupils achieving grade 5 or above in both English and maths GCSEs — considered a 'strong pass' and often required for sixth form or college entry.",
    section: "performance",
    unit: "percent"
  },
  engmath_4_plus_pct: {
    key: "engmath_4_plus_pct",
    label: "English & Maths Standard Pass",
    description: "Pupils achieving grade 4 or above in both English and maths GCSEs — the 'standard pass', equivalent to the old grade C.",
    section: "performance",
    unit: "percent"
  },
  ebacc_entry_pct: {
    key: "ebacc_entry_pct",
    label: "EBacc Entered",
    description: "English Baccalaureate — the percentage of pupils entered for a core set of academic GCSEs: English, maths, sciences, history or geography, and a language.",
    section: "performance",
    unit: "percent"
  },
  ebacc_5_plus_pct: {
    key: "ebacc_5_plus_pct",
    label: "EBacc Strong Pass",
    description: "Pupils achieving grade 5 or above across all English Baccalaureate subjects.",
    section: "performance",
    unit: "percent"
  },
  ebacc_4_plus_pct: {
    key: "ebacc_4_plus_pct",
    label: "EBacc Standard Pass",
    description: "Pupils achieving grade 4 or above across all English Baccalaureate subjects.",
    section: "performance",
    unit: "percent"
  },
  ks2_reading_expected_pct: {
    key: "ks2_reading_expected_pct",
    label: "Year 6 Reading (Expected)",
    description: "Pupils meeting the expected standard in Key Stage 2 reading assessments at the end of Year 6 (age 10–11).",
    section: "performance",
    unit: "percent"
  },
  ks2_writing_expected_pct: {
    key: "ks2_writing_expected_pct",
    label: "Year 6 Writing (Expected)",
    description: "Pupils meeting the expected standard in Key Stage 2 writing assessments at the end of Year 6 (age 10–11).",
    section: "performance",
    unit: "percent"
  },
  ks2_maths_expected_pct: {
    key: "ks2_maths_expected_pct",
    label: "Year 6 Maths (Expected)",
    description: "Pupils meeting the expected standard in Key Stage 2 maths assessments at the end of Year 6 (age 10–11).",
    section: "performance",
    unit: "percent"
  },
  ks2_combined_expected_pct: {
    key: "ks2_combined_expected_pct",
    label: "Year 6 All Subjects (Expected)",
    description: "Pupils meeting the expected standard in all three Key Stage 2 subjects: reading, writing and maths.",
    section: "performance",
    unit: "percent"
  },
  ks2_reading_higher_pct: {
    key: "ks2_reading_higher_pct",
    label: "Year 6 Reading (Higher)",
    description: "Pupils exceeding the expected standard in Key Stage 2 reading — achieving at a higher level than required.",
    section: "performance",
    unit: "percent"
  },
  ks2_writing_higher_pct: {
    key: "ks2_writing_higher_pct",
    label: "Year 6 Writing (Higher)",
    description: "Pupils exceeding the expected standard in Key Stage 2 writing — achieving at a higher level than required.",
    section: "performance",
    unit: "percent"
  },
  ks2_maths_higher_pct: {
    key: "ks2_maths_higher_pct",
    label: "Year 6 Maths (Higher)",
    description: "Pupils exceeding the expected standard in Key Stage 2 maths — achieving at a higher level than required.",
    section: "performance",
    unit: "percent"
  },
  ks2_combined_higher_pct: {
    key: "ks2_combined_higher_pct",
    label: "Year 6 All Subjects (Higher)",
    description: "Pupils exceeding the expected standard in all three Key Stage 2 subjects: reading, writing and maths.",
    section: "performance",
    unit: "percent"
  },
  area_crime_incidents_per_1000: {
    key: "area_crime_incidents_per_1000",
    label: "Crime Incidents per 1,000",
    description: "Recorded crime incidents per 1,000 residents in the school's local area, based on police data. Provides neighbourhood context.",
    section: "area",
    unit: "rate",
    decimals: 2
  },
  area_house_price_average: {
    key: "area_house_price_average",
    label: "Average House Price",
    description: "Average residential property sale price in the school's local area, based on Land Registry data. Gives a sense of the area's economic context.",
    section: "area",
    unit: "currency"
  },
  area_house_price_annual_change_pct: {
    key: "area_house_price_annual_change_pct",
    label: "House Price Annual Change",
    description: "Year-on-year change in average house prices in the local area.",
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
      if (value >= 1_000_000) return `£${(value / 1_000_000).toFixed(1)}m`;
      if (value >= 1_000) return `£${Math.round(value / 1_000)}k`;
      return `£${Math.round(value)}`;
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
      return `${prefix}${value.toFixed(1)}%`;
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
