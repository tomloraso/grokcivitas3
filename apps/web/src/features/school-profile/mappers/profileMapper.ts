import type {
  SchoolProfileDestinationStageLatest,
  SchoolProfileMetricBenchmark,
  SchoolProfileResponse,
  SchoolTrendBenchmarkPoint,
  SchoolProfileAnalystSection,
  SchoolProfileDestinationsLatest,
  SchoolProfileNeighbourhoodSection,
  SchoolTrendDashboardResponse,
  SchoolTrendsResponse
} from "../../../api/types";
import { mapSavedSchoolState } from "../../favourites/mappers";
import { mapSectionAccess } from "../../premium-access/mappers";
import { mapCompletenessReasonToMessageKey } from "../../../shared/completeness";
import {
  DEMOGRAPHICS_METRIC_KEYS,
  formatMetricKeyFallback,
  formatMetricValue,
  getMetricCatalogEntry,
  METRIC_SECTION_LABELS,
  METRIC_SECTION_ORDER,
  type MetricSectionKey,
  type MetricUnit
} from "../metricCatalog";
import type {
  AdmissionsLatestVM,
  AreaContextVM,
  AreaDeprivationDomainVM,
  BenchmarkContextVM,
  BenchmarkDashboardVM,
  BenchmarkMetricVM,
  BehaviourLatestVM,
  DemographicMetricVM,
  DemographicsCategoryVM,
  DemographicsEthnicityGroupVM,
  DemographicsVM,
  FinanceLatestVM,
  LeadershipSnapshotVM,
  OfstedTimelineVM,
  OfstedVM,
  PerformanceVM,
  PerformanceYearVM,
  ProfileCompletenessVM,
  SchoolDestinationsVM,
  SchoolDestinationStageLatestVM,
  SchoolIdentityVM,
  SchoolProfileVM,
  SectionCompletenessReasonCode,
  SectionCompletenessVM,
  TrendPointVM,
  TrendSeriesVM,
  TrendsVM,
  UnsupportedMetricVM,
  AttendanceLatestVM,
  AnalystSectionVM,
  WorkforceBreakdownItemVM,
  WorkforceLatestVM,
  SubjectPerformanceVM,
  SubjectPerformanceGroupVM,
  SubjectSummaryVM
} from "../types";

const DEPRIVATION_DOMAIN_LABELS: Record<string, string> = {
  income: "Income",
  employment: "Employment",
  education: "Education",
  health: "Health",
  crime: "Crime",
  barriers: "Barriers",
  living_environment: "Living Environment"
};

interface SectionCompletenessContract {
  status: "available" | "partial" | "unavailable";
  reason_code: SectionCompletenessReasonCode | null;
  last_updated_at: string | null;
  years_available?: string[] | null;
}

function fallbackSectionCompleteness(): SectionCompletenessVM {
  return {
    status: "unavailable",
    reasonCode: "pipeline_failed_recently",
    messageKey: mapCompletenessReasonToMessageKey("pipeline_failed_recently"),
    lastUpdatedAt: null,
    yearsAvailable: null
  };
}

interface DashboardMetricMeta {
  section: MetricSectionKey;
  label: string;
  unit: MetricUnit;
  points: {
    academic_year: string;
    school_value: number | null;
    national_value: number | null;
    local_value: number | null;
    school_vs_national_delta: number | null;
    school_vs_local_delta: number | null;
    contexts: BenchmarkContextVM[];
  }[];
}

function fallback(value: string | null | undefined, placeholder: string): string {
  return value?.trim() ? value : placeholder;
}

function toOptionalText(value: string | null | undefined): string | null {
  return value?.trim() ? value.trim() : null;
}

function toOptionalNumber(value: number | null | undefined): number | null {
  return typeof value === "number" ? value : null;
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

function fmtPct(value: number | null): string | null {
  return formatMetricValue(value, "percent");
}

function dateKey(iso: string): number {
  const parsed = Date.parse(`${iso}T00:00:00Z`);
  return Number.isNaN(parsed) ? -1 : parsed;
}

function academicYearKey(academicYear: string): number {
  const match = /^(\d{4})/.exec(academicYear);
  return match ? Number(match[1]) : -1;
}

function mapSectionCompleteness(
  section: SectionCompletenessContract | null | undefined
): SectionCompletenessVM {
  if (!section) {
    return fallbackSectionCompleteness();
  }

  return {
    status: section.status,
    reasonCode: section.reason_code,
    messageKey: mapCompletenessReasonToMessageKey(section.reason_code),
    lastUpdatedAt: fmtDateTime(section.last_updated_at),
    yearsAvailable: section.years_available ?? null
  };
}

function mapSchool(profile: SchoolProfileResponse): SchoolIdentityVM {
  const school = profile.school;
  const headName = [school.head_title, school.head_first_name, school.head_last_name]
    .map((part) => part?.trim() ?? "")
    .filter((part) => part.length > 0)
    .join(" ");
  const addressLines = [
    school.address_street,
    school.address_locality,
    school.address_line3,
    school.address_town,
    school.address_county,
    school.postcode
  ]
    .map((line) => line?.trim() ?? "")
    .filter((line, index, values) => line.length > 0 && values.indexOf(line) === index);

  let ageRangeLabel: string | null = null;
  if (typeof school.statutory_low_age === "number" && typeof school.statutory_high_age === "number") {
    ageRangeLabel = `Ages ${school.statutory_low_age}-${school.statutory_high_age}`;
  } else if (typeof school.statutory_low_age === "number") {
    ageRangeLabel = `Starts at age ${school.statutory_low_age}`;
  } else if (typeof school.statutory_high_age === "number") {
    ageRangeLabel = `Up to age ${school.statutory_high_age}`;
  }

  return {
    urn: school.urn,
    name: school.name,
    phase: fallback(school.phase, "Unknown"),
    type: fallback(school.type, "Unknown"),
    status: fallback(school.status, "Unknown"),
    postcode: fallback(school.postcode, "Unknown"),
    lat: school.lat,
    lng: school.lng,
    website: toOptionalText(school.website),
    telephone: toOptionalText(school.telephone),
    headName: headName.length > 0 ? headName : null,
    headJobTitle: toOptionalText(school.head_job_title),
    addressLines,
    ageRangeLabel,
    gender: toOptionalText(school.gender),
    religiousCharacter: toOptionalText(school.religious_character),
    diocese: toOptionalText(school.diocese),
    admissionsPolicy: toOptionalText(school.admissions_policy),
    sixthForm: toOptionalText(school.sixth_form),
    nurseryProvision: toOptionalText(school.nursery_provision),
    boarders: toOptionalText(school.boarders),
    giasFsmPct: school.fsm_pct_gias ?? null,
    trustName: toOptionalText(school.trust_name),
    trustFlag: toOptionalText(school.trust_flag),
    federationName: toOptionalText(school.federation_name),
    federationFlag: toOptionalText(school.federation_flag),
    localAuthorityName: toOptionalText(school.la_name),
    localAuthorityCode: toOptionalText(school.la_code),
    urbanRural: toOptionalText(school.urban_rural),
    numberOfBoys: school.number_of_boys ?? null,
    numberOfGirls: school.number_of_girls ?? null,
    lsoaCode: toOptionalText(school.lsoa_code),
    lsoaName: toOptionalText(school.lsoa_name),
    lastChangedDate: fmtDate(school.last_changed_date)
  };
}

function mapDemographics(profile: SchoolProfileResponse): DemographicsVM | null {
  const demographics = profile.demographics_latest;
  if (!demographics) {
    return null;
  }

  const metrics: DemographicMetricVM[] = DEMOGRAPHICS_METRIC_KEYS.map((metricKey) => {
    const catalog = getMetricCatalogEntry(metricKey);
    const rawValue = demographics[metricKey as keyof typeof demographics];
    return {
      label: catalog?.label ?? formatMetricKeyFallback(metricKey),
      value:
        typeof rawValue === "number" || rawValue === null
          ? formatMetricValue(rawValue, catalog?.unit ?? "percent", catalog?.decimals)
          : null,
      raw: typeof rawValue === "number" ? rawValue : null,
      metricKey,
      unit: catalog?.unit ?? "percent"
    };
  });

  const ethnicityBreakdown: DemographicsEthnicityGroupVM[] = (demographics.ethnicity_breakdown ?? [])
    .filter((group) => (group.count ?? 0) > 0 || (group.percentage ?? 0) > 0)
    .sort((left, right) => (right.percentage ?? 0) - (left.percentage ?? 0))
    .map((group) => ({
      key: group.key,
      label: group.label,
      percentage: group.percentage,
      count: group.count,
      percentageLabel: fmtPct(group.percentage)
    }));

  const sendPrimaryNeeds: DemographicsCategoryVM[] = (demographics.send_primary_needs ?? [])
    .filter((need) => (need.count ?? 0) > 0 || (need.percentage ?? 0) > 0)
    .sort((left, right) => (right.percentage ?? 0) - (left.percentage ?? 0))
    .slice(0, 5)
    .map((need) => ({
      key: need.key,
      label: need.label,
      percentage: need.percentage,
      count: need.count,
      percentageLabel: fmtPct(need.percentage)
    }));

  const topHomeLanguages: DemographicsCategoryVM[] = (demographics.top_home_languages ?? [])
    .filter((language) => (language.count ?? 0) > 0 || (language.percentage ?? 0) > 0)
    .sort((left, right) => left.rank - right.rank)
    .slice(0, 5)
    .map((language) => ({
      key: language.key,
      label: language.label,
      rank: language.rank,
      percentage: language.percentage,
      count: language.count,
      percentageLabel: fmtPct(language.percentage)
    }));

  return {
    academicYear: demographics.academic_year,
    metrics,
    coverage: {
      fsmSupported: demographics.coverage.fsm_supported,
      fsm6Supported: demographics.coverage.fsm6_supported,
      genderSupported: demographics.coverage.gender_supported,
      mobilitySupported: demographics.coverage.mobility_supported,
      sendPrimaryNeedSupported: demographics.coverage.send_primary_need_supported,
      ethnicitySupported: demographics.coverage.ethnicity_supported,
      topLanguagesSupported: demographics.coverage.top_languages_supported
    },
    ethnicityBreakdown,
    sendPrimaryNeeds,
    topHomeLanguages
  };
}

function mapAttendance(profile: SchoolProfileResponse): AttendanceLatestVM | null {
  const attendance = profile.attendance_latest;
  if (!attendance) {
    return null;
  }

  return {
    academicYear: attendance.academic_year,
    overallAttendancePct: attendance.overall_attendance_pct,
    overallAbsencePct: attendance.overall_absence_pct,
    persistentAbsencePct: attendance.persistent_absence_pct
  };
}

function mapBehaviour(profile: SchoolProfileResponse): BehaviourLatestVM | null {
  const behaviour = profile.behaviour_latest;
  if (!behaviour) {
    return null;
  }

  return {
    academicYear: behaviour.academic_year,
    suspensionsCount: behaviour.suspensions_count,
    suspensionsRate: behaviour.suspensions_rate,
    permanentExclusionsCount: behaviour.permanent_exclusions_count,
    permanentExclusionsRate: behaviour.permanent_exclusions_rate
  };
}

function mapWorkforceBreakdownItems(
  items: NonNullable<SchoolProfileResponse["workforce_latest"]>["teacher_sex_breakdown"]
): WorkforceBreakdownItemVM[] {
  return (items ?? []).map((item) => ({
    key: item.key,
    label: item.label,
    headcount: item.headcount,
    fte: item.fte ?? null,
    headcountPct: item.headcount_pct ?? null,
    ftePct: item.fte_pct ?? null
  }));
}

function mapWorkforce(profile: SchoolProfileResponse): WorkforceLatestVM | null {
  const workforce = profile.workforce_latest;
  if (!workforce) {
    return null;
  }

  return {
    academicYear: workforce.academic_year,
    pupilTeacherRatio: workforce.pupil_teacher_ratio,
    supplyStaffPct: workforce.supply_staff_pct,
    teachers3plusYearsPct: workforce.teachers_3plus_years_pct,
    teacherTurnoverPct: workforce.teacher_turnover_pct,
    qtsPct: workforce.qts_pct,
    qualificationsLevel6PlusPct: workforce.qualifications_level6_plus_pct,
    teacherHeadcountTotal: workforce.teacher_headcount_total,
    teacherFteTotal: workforce.teacher_fte_total,
    supportStaffHeadcountTotal: workforce.support_staff_headcount_total,
    supportStaffFteTotal: workforce.support_staff_fte_total,
    leadershipHeadcount: workforce.leadership_headcount,
    teacherAverageMeanSalaryGbp: workforce.teacher_average_mean_salary_gbp,
    teacherAbsencePct: workforce.teacher_absence_pct,
    teacherVacancyRate: workforce.teacher_vacancy_rate,
    thirdPartySupportStaffHeadcount: workforce.third_party_support_staff_headcount,
    teacherSexBreakdown: mapWorkforceBreakdownItems(workforce.teacher_sex_breakdown),
    teacherAgeBreakdown: mapWorkforceBreakdownItems(workforce.teacher_age_breakdown),
    teacherEthnicityBreakdown: mapWorkforceBreakdownItems(workforce.teacher_ethnicity_breakdown),
    teacherQualificationBreakdown: mapWorkforceBreakdownItems(
      workforce.teacher_qualification_breakdown
    ),
    supportStaffPostMix: mapWorkforceBreakdownItems(workforce.support_staff_post_mix)
  };
}

function mapFinance(profile: SchoolProfileResponse): FinanceLatestVM | null {
  const finance = profile.finance_latest;
  if (!finance) {
    return null;
  }

  return {
    academicYear: finance.academic_year,
    totalIncomeGbp: toOptionalNumber(finance.total_income_gbp),
    totalExpenditureGbp: toOptionalNumber(finance.total_expenditure_gbp),
    incomePerPupilGbp: toOptionalNumber(finance.income_per_pupil_gbp),
    expenditurePerPupilGbp: toOptionalNumber(finance.expenditure_per_pupil_gbp),
    totalStaffCostsGbp: toOptionalNumber(finance.total_staff_costs_gbp),
    staffCostsPctOfExpenditure: toOptionalNumber(finance.staff_costs_pct_of_expenditure),
    revenueReserveGbp: toOptionalNumber(finance.revenue_reserve_gbp),
    revenueReservePerPupilGbp: toOptionalNumber(finance.revenue_reserve_per_pupil_gbp),
    inYearBalanceGbp: toOptionalNumber(finance.in_year_balance_gbp),
    totalGrantFundingGbp: toOptionalNumber(finance.total_grant_funding_gbp),
    totalSelfGeneratedFundingGbp: toOptionalNumber(finance.total_self_generated_funding_gbp),
    teachingStaffCostsGbp: toOptionalNumber(finance.teaching_staff_costs_gbp),
    supplyTeachingStaffCostsGbp: toOptionalNumber(finance.supply_teaching_staff_costs_gbp),
    educationSupportStaffCostsGbp: toOptionalNumber(
      finance.education_support_staff_costs_gbp
    ),
    otherStaffCostsGbp: toOptionalNumber(finance.other_staff_costs_gbp),
    premisesCostsGbp: toOptionalNumber(finance.premises_costs_gbp),
    educationalSuppliesCostsGbp: toOptionalNumber(
      finance.educational_supplies_costs_gbp
    ),
    boughtInProfessionalServicesCostsGbp: toOptionalNumber(
      finance.bought_in_professional_services_costs_gbp
    ),
    cateringCostsGbp: toOptionalNumber(finance.catering_costs_gbp),
    supplyStaffCostsPctOfStaffCosts: toOptionalNumber(
      finance.supply_staff_costs_pct_of_staff_costs
    )
  };
}

function mapAdmissions(profile: SchoolProfileResponse): AdmissionsLatestVM | null {
  const admissions = profile.admissions_latest;
  if (!admissions) {
    return null;
  }

  return {
    academicYear: admissions.academic_year,
    placesOfferedTotal: admissions.places_offered_total,
    applicationsAnyPreference: admissions.applications_any_preference,
    applicationsFirstPreference: admissions.applications_first_preference,
    oversubscriptionRatio: admissions.oversubscription_ratio,
    firstPreferenceOfferRate: admissions.first_preference_offer_rate,
    anyPreferenceOfferRate: admissions.any_preference_offer_rate,
    admissionsPolicy: toOptionalText(admissions.admissions_policy)
  };
}

function mapDestinationStage(
  stage: SchoolProfileDestinationStageLatest | null | undefined
): SchoolDestinationStageLatestVM | null {
  if (!stage) {
    return null;
  }

  return {
    academicYear: stage.academic_year,
    cohortCount: toOptionalNumber(stage.cohort_count),
    qualificationGroup: toOptionalText(stage.qualification_group),
    qualificationLevel: toOptionalText(stage.qualification_level),
    overallPct: toOptionalNumber(stage.overall_pct),
    educationPct: toOptionalNumber(stage.education_pct),
    apprenticeshipPct: toOptionalNumber(stage.apprenticeship_pct),
    employmentPct: toOptionalNumber(stage.employment_pct),
    notSustainedPct: toOptionalNumber(stage.not_sustained_pct),
    activityUnknownPct: toOptionalNumber(stage.activity_unknown_pct),
    fePct: toOptionalNumber(stage.fe_pct),
    otherEducationPct: toOptionalNumber(stage.other_education_pct),
    schoolSixthFormPct: toOptionalNumber(stage.school_sixth_form_pct),
    sixthFormCollegePct: toOptionalNumber(stage.sixth_form_college_pct),
    higherEducationPct: toOptionalNumber(stage.higher_education_pct)
  };
}

function mapDestinations(profile: SchoolProfileResponse): SchoolDestinationsVM | null {
  const destinations = profile.destinations_latest as SchoolProfileDestinationsLatest | null;
  if (!destinations) {
    return null;
  }

  return {
    ks4: mapDestinationStage(destinations.ks4),
    study16To18: mapDestinationStage(destinations.study_16_18)
  };
}

function mapLeadership(profile: SchoolProfileResponse): LeadershipSnapshotVM | null {
  const leadership = profile.leadership_snapshot;
  if (!leadership) {
    return null;
  }

  return {
    headteacherName: leadership.headteacher_name,
    headteacherStartDate: fmtDate(leadership.headteacher_start_date),
    headteacherTenureYears: leadership.headteacher_tenure_years,
    leadershipTurnoverScore: leadership.leadership_turnover_score
  };
}

function mapOfsted(profile: SchoolProfileResponse): OfstedVM | null {
  const ofsted = profile.ofsted_latest;
  if (!ofsted) {
    return null;
  }

  return {
    ratingCode: ofsted.overall_effectiveness_code,
    ratingLabel: ofsted.overall_effectiveness_label,
    inspectionDate: fmtDate(ofsted.inspection_start_date),
    publicationDate: fmtDate(ofsted.publication_date),
    latestOeifInspectionDate: fmtDate(ofsted.latest_oeif_inspection_start_date),
    latestOeifPublicationDate: fmtDate(ofsted.latest_oeif_publication_date),
    latestUngradedInspectionDate: fmtDate(ofsted.latest_ungraded_inspection_date),
    latestUngradedPublicationDate: fmtDate(ofsted.latest_ungraded_publication_date),
    mostRecentInspectionDate: fmtDate(ofsted.most_recent_inspection_date),
    daysSinceMostRecentInspection: ofsted.days_since_most_recent_inspection,
    qualityOfEducationCode: ofsted.quality_of_education_code,
    qualityOfEducationLabel: ofsted.quality_of_education_label,
    behaviourAndAttitudesCode: ofsted.behaviour_and_attitudes_code,
    behaviourAndAttitudesLabel: ofsted.behaviour_and_attitudes_label,
    personalDevelopmentCode: ofsted.personal_development_code,
    personalDevelopmentLabel: ofsted.personal_development_label,
    leadershipAndManagementCode: ofsted.leadership_and_management_code,
    leadershipAndManagementLabel: ofsted.leadership_and_management_label,
    isGraded: ofsted.is_graded,
    ungradedOutcome: ofsted.ungraded_outcome,
    effectiveRatingCode: ofsted.effective_overall_effectiveness_code ?? null,
    effectiveRatingLabel: ofsted.effective_overall_effectiveness_label ?? null,
    providerPageUrl: toOptionalText(ofsted.provider_page_url)
  };
}

function mapOfstedTimeline(profile: SchoolProfileResponse): OfstedTimelineVM {
  const timeline = profile.ofsted_timeline;

  const events = [...(timeline?.events ?? [])]
    .sort((left, right) => dateKey(right.inspection_start_date) - dateKey(left.inspection_start_date))
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
      isPartialHistory: timeline?.coverage.is_partial_history ?? true,
      earliestEventDate: fmtDate(timeline?.coverage.earliest_event_date ?? null),
      latestEventDate: fmtDate(timeline?.coverage.latest_event_date ?? null),
      eventsCount: timeline?.coverage.events_count ?? 0
    }
  };
}

type PerformanceYearContract = NonNullable<
  NonNullable<SchoolProfileResponse["performance"]>["latest"]
>;

function mapPerformanceYear(year: PerformanceYearContract): PerformanceYearVM {
  return {
    academicYear: year.academic_year,
    attainment8Average: year.attainment8_average,
    progress8Average: year.progress8_average,
    progress8Disadvantaged: year.progress8_disadvantaged,
    progress8NotDisadvantaged: year.progress8_not_disadvantaged,
    progress8DisadvantagedGap: year.progress8_disadvantaged_gap,
    engmath5PlusPct: year.engmath_5_plus_pct,
    engmath4PlusPct: year.engmath_4_plus_pct,
    ebaccEntryPct: year.ebacc_entry_pct,
    ebacc5PlusPct: year.ebacc_5_plus_pct,
    ebacc4PlusPct: year.ebacc_4_plus_pct,
    ks2ReadingExpectedPct: year.ks2_reading_expected_pct,
    ks2WritingExpectedPct: year.ks2_writing_expected_pct,
    ks2MathsExpectedPct: year.ks2_maths_expected_pct,
    ks2CombinedExpectedPct: year.ks2_combined_expected_pct,
    ks2ReadingHigherPct: year.ks2_reading_higher_pct,
    ks2WritingHigherPct: year.ks2_writing_higher_pct,
    ks2MathsHigherPct: year.ks2_maths_higher_pct,
    ks2CombinedHigherPct: year.ks2_combined_higher_pct
  };
}

function mapPerformance(profile: SchoolProfileResponse): PerformanceVM | null {
  if (!profile.performance) {
    return null;
  }

  return {
    latest: profile.performance.latest ? mapPerformanceYear(profile.performance.latest) : null,
    history: (profile.performance.history ?? []).map((year) => mapPerformanceYear(year))
  };
}

function mapAreaDeprivationDomains(
  deprivation: NonNullable<
    NonNullable<SchoolProfileNeighbourhoodSection["area_context"]>["deprivation"]
  >
): AreaDeprivationDomainVM[] {
  return Object.entries(DEPRIVATION_DOMAIN_LABELS).map(([key, label]) => ({
    key,
    label,
    score: deprivation[`${key}_score` as keyof typeof deprivation] as number | null,
    rank: deprivation[`${key}_rank` as keyof typeof deprivation] as number | null,
    decile: deprivation[`${key}_decile` as keyof typeof deprivation] as number | null
  }));
}

function mapAreaContext(
  area: SchoolProfileNeighbourhoodSection["area_context"]
): AreaContextVM | null {
  if (!area) {
    return null;
  }

  return {
    deprivation: area.deprivation
      ? {
          lsoaCode: area.deprivation.lsoa_code,
          imdScore: area.deprivation.imd_score,
          imdRank: area.deprivation.imd_rank,
          imdDecile: area.deprivation.imd_decile,
          idaciScore: area.deprivation.idaci_score,
          idaciDecile: area.deprivation.idaci_decile,
          populationTotal: area.deprivation.population_total,
          localAuthorityDistrictCode: area.deprivation.local_authority_district_code,
          localAuthorityDistrictName: area.deprivation.local_authority_district_name,
          sourceRelease: area.deprivation.source_release,
          domains: mapAreaDeprivationDomains(area.deprivation)
        }
      : null,
    crime: area.crime
      ? {
          radiusMiles: area.crime.radius_miles,
          latestMonth: fmtMonth(area.crime.latest_month),
          totalIncidents: area.crime.total_incidents,
          populationDenominator: area.crime.population_denominator,
          incidentsPer1000: area.crime.incidents_per_1000,
          annualIncidentsPer1000: (area.crime.annual_incidents_per_1000 ?? []).map((entry) => ({
            year: entry.year,
            totalIncidents: entry.total_incidents,
            incidentsPer1000: entry.incidents_per_1000
          })),
          categories: [...area.crime.categories]
            .sort(
              (left, right) =>
                right.incident_count - left.incident_count ||
                left.category.localeCompare(right.category)
            )
            .map((category) => ({
              category: category.category,
              incidentCount: category.incident_count
            }))
        }
      : null,
    housePrices: area.house_prices
      ? {
          areaCode: area.house_prices.area_code,
          areaName: area.house_prices.area_name,
          latestMonth: fmtMonth(area.house_prices.latest_month),
          averagePrice: area.house_prices.average_price,
          annualChangePct: area.house_prices.annual_change_pct,
          monthlyChangePct: area.house_prices.monthly_change_pct,
          threeYearChangePct: area.house_prices.three_year_change_pct,
          trend: (area.house_prices.trend ?? []).map((point) => ({
            month: fmtMonth(point.month),
            averagePrice: point.average_price,
            annualChangePct: point.annual_change_pct,
            monthlyChangePct: point.monthly_change_pct
          }))
        }
      : null,
    coverage: {
      hasDeprivation: area.coverage.has_deprivation,
      hasCrime: area.coverage.has_crime,
      crimeMonthsAvailable: area.coverage.crime_months_available,
      hasHousePrices: area.coverage.has_house_prices,
      housePriceMonthsAvailable: area.coverage.house_price_months_available
    }
  };
}

function mapAnalystSection(
  analyst: SchoolProfileAnalystSection
): AnalystSectionVM {
  return {
    access: mapSectionAccess(analyst.access),
    text: toOptionalText(analyst.text),
    teaserText: toOptionalText(analyst.teaser_text),
    disclaimer: toOptionalText(analyst.disclaimer),
  };
}

function mapNeighbourhoodSection(
  neighbourhood: SchoolProfileNeighbourhoodSection
) {
  return {
    access: mapSectionAccess(neighbourhood.access),
    areaContext: mapAreaContext(neighbourhood.area_context),
    teaserText: toOptionalText(neighbourhood.teaser_text),
  };
}

function mapTrends(trends: SchoolTrendsResponse | null): TrendsVM | null {
  if (!trends) {
    return null;
  }

  const series: TrendSeriesVM[] = Object.entries(trends.series)
    .map(([metricKey, points]) => {
      const catalog = getMetricCatalogEntry(metricKey);
      if (!catalog) {
        return null;
      }

      const mappedPoints: TrendPointVM[] = points.map((point) => ({
        year: point.academic_year,
        value: typeof point.value === "number" ? point.value : null,
        delta: point.delta,
        direction: point.direction
      }));
      const latestPoint = mappedPoints.length > 0 ? mappedPoints[mappedPoints.length - 1] : null;

      return {
        label: catalog.label,
        metricKey,
        unit: catalog.unit,
        points: mappedPoints,
        latestDelta: latestPoint?.delta ?? null,
        latestDirection: latestPoint?.direction ?? null
      };
    })
    .filter((entry): entry is TrendSeriesVM => entry !== null);

  return {
    yearsAvailable: trends.years_available,
    isPartialHistory: trends.history_quality.is_partial_history,
    yearsCount: trends.history_quality.years_count,
    series,
    sectionCompleteness: {
      demographics: mapSectionCompleteness(trends.section_completeness.demographics),
      attendance: mapSectionCompleteness(trends.section_completeness.attendance),
      behaviour: mapSectionCompleteness(trends.section_completeness.behaviour),
      workforce: mapSectionCompleteness(trends.section_completeness.workforce),
      admissions: mapSectionCompleteness(trends.section_completeness.admissions),
      destinations: mapSectionCompleteness(trends.section_completeness.destinations),
      finance: mapSectionCompleteness(trends.section_completeness.finance)
    }
  };
}

function normalizeDashboardUnit(unit: string): MetricUnit {
  switch (unit) {
    case "count":
    case "currency":
    case "percent":
    case "ratio":
    case "rate":
    case "score":
      return unit;
    default:
      return "score";
  }
}

function mapBenchmarkContexts(
  contexts:
    | SchoolProfileMetricBenchmark["contexts"]
    | SchoolTrendBenchmarkPoint["contexts"]
    | undefined
): BenchmarkContextVM[] {
  return (contexts ?? []).map((context) => ({
    scope: context.scope,
    label: context.label,
    value: context.value,
    percentileRank: context.percentile_rank,
    schoolCount: context.school_count,
    areaCode: context.area_code ?? null,
  }));
}

function buildDashboardMetricMap(
  dashboard: SchoolTrendDashboardResponse | null
): Map<string, DashboardMetricMeta> {
  const metricMap = new Map<string, DashboardMetricMeta>();
  if (!dashboard) {
    return metricMap;
  }

  for (const section of dashboard.sections) {
    for (const metric of section.metrics) {
      metricMap.set(metric.metric_key, {
        section: section.key,
        label: metric.label,
        unit: normalizeDashboardUnit(metric.unit),
        points: metric.points.map((point) => ({
          academic_year: point.academic_year,
          school_value: point.school_value,
          national_value: point.national_value,
          local_value: point.local_value,
          school_vs_national_delta: point.school_vs_national_delta,
          school_vs_local_delta: point.school_vs_local_delta,
          contexts: mapBenchmarkContexts(point.contexts),
        }))
      });
    }
  }

  return metricMap;
}

function buildBenchmarkDashboard(
  profile: SchoolProfileResponse,
  dashboard: SchoolTrendDashboardResponse | null
): BenchmarkDashboardVM | null {
  const snapshotMetrics = profile.benchmarks?.metrics ?? [];
  if (snapshotMetrics.length === 0 && !dashboard) {
    return null;
  }

  const dashboardMetricMap = buildDashboardMetricMap(dashboard);
  const sectionBuckets = new Map<MetricSectionKey, BenchmarkMetricVM[]>(
    METRIC_SECTION_ORDER.map((section) => [section, []])
  );

  for (const snapshotMetric of snapshotMetrics) {
    const dashboardMetric = dashboardMetricMap.get(snapshotMetric.metric_key);
    const catalogEntry = getMetricCatalogEntry(snapshotMetric.metric_key);
    const section = dashboardMetric?.section ?? catalogEntry?.section ?? "performance";
    const label =
      dashboardMetric?.label ??
      catalogEntry?.label ??
      formatMetricKeyFallback(snapshotMetric.metric_key);
    const unit = dashboardMetric?.unit ?? catalogEntry?.unit ?? "score";

    sectionBuckets.get(section)?.push({
      metricKey: snapshotMetric.metric_key,
      label,
      section,
      unit,
      academicYear: snapshotMetric.academic_year,
      schoolValue:
        typeof snapshotMetric.school_value === "number" ? snapshotMetric.school_value : null,
      nationalValue: snapshotMetric.national_value,
      localValue: snapshotMetric.local_value,
      schoolVsNationalDelta: snapshotMetric.school_vs_national_delta,
      schoolVsLocalDelta: snapshotMetric.school_vs_local_delta,
      localScope: snapshotMetric.local_scope,
      localAreaCode: snapshotMetric.local_area_code,
      localAreaLabel: snapshotMetric.local_area_label,
      contexts: mapBenchmarkContexts(snapshotMetric.contexts),
      trendPoints:
        dashboardMetric?.points.map((point) => ({
          academicYear: point.academic_year,
          schoolValue: point.school_value,
          nationalValue: point.national_value,
          localValue: point.local_value,
          schoolVsNationalDelta: point.school_vs_national_delta,
          schoolVsLocalDelta: point.school_vs_local_delta,
          contexts: point.contexts,
        })) ?? []
    });
  }

  const sections = METRIC_SECTION_ORDER.map((section) => {
    const metrics = sectionBuckets.get(section) ?? [];
    metrics.sort((left, right) => {
      const leftCatalog = getMetricCatalogEntry(left.metricKey);
      const rightCatalog = getMetricCatalogEntry(right.metricKey);
      if (leftCatalog && rightCatalog) {
        return Object.keys(METRIC_SECTION_LABELS).includes(section)
          ? academicYearKey(right.academicYear) - academicYearKey(left.academicYear) ||
              left.label.localeCompare(right.label)
          : left.label.localeCompare(right.label);
      }
      return left.label.localeCompare(right.label);
    });

    return {
      key: section,
      label: METRIC_SECTION_LABELS[section],
      metrics
    };
  }).filter((section) => section.metrics.length > 0);

  if (sections.length === 0) {
    return null;
  }

  return {
    yearsAvailable:
      dashboard?.years_available ??
      Array.from(new Set(snapshotMetrics.map((metric) => metric.academic_year))).sort(
        (left, right) => academicYearKey(left) - academicYearKey(right)
      ),
    sections,
    completeness: dashboard ? mapSectionCompleteness(dashboard.completeness) : null
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
    attendance: mapSectionCompleteness(profile.completeness.attendance),
    behaviour: mapSectionCompleteness(profile.completeness.behaviour),
    workforce: mapSectionCompleteness(profile.completeness.workforce),
    admissions: mapSectionCompleteness(profile.completeness.admissions),
    destinations: mapSectionCompleteness(profile.completeness.destinations),
    finance: mapSectionCompleteness(profile.completeness.finance),
    leadership: mapSectionCompleteness(profile.completeness.leadership),
    performance: mapSectionCompleteness(profile.completeness.performance),
    trends: trendsCompleteness,
    ofstedLatest: mapSectionCompleteness(profile.completeness.ofsted_latest),
    ofstedTimeline: mapSectionCompleteness(profile.completeness.ofsted_timeline),
    areaDeprivation: mapSectionCompleteness(profile.completeness.area_deprivation),
    areaCrime: mapSectionCompleteness(profile.completeness.area_crime),
    areaHousePrices: mapSectionCompleteness(profile.completeness.area_house_prices)
  };
}

function mapUnsupported(profile: SchoolProfileResponse): UnsupportedMetricVM[] {
  const demographics = profile.demographics_latest;
  const coverage = demographics?.coverage;
  if (!coverage || !demographics) {
    return [];
  }

  const unsupported: UnsupportedMetricVM[] = [];
  if (!coverage.fsm_supported) {
    unsupported.push({ label: "Free School Meals (direct)" });
  }
  if (!coverage.fsm6_supported) {
    unsupported.push({ label: "FSM6" });
  }
  if (!coverage.gender_supported) {
    unsupported.push({ label: "Gender split" });
  }
  if (!coverage.mobility_supported) {
    unsupported.push({ label: "Pupil mobility / turnover" });
  }
  if (!coverage.send_primary_need_supported && (demographics.send_primary_needs ?? []).length === 0) {
    unsupported.push({ label: "SEND primary need breakdown" });
  }
  if (!coverage.ethnicity_supported && (demographics.ethnicity_breakdown ?? []).length === 0) {
    unsupported.push({ label: "Ethnicity breakdown" });
  }
  if (!coverage.top_languages_supported && (demographics.top_home_languages ?? []).length === 0) {
    unsupported.push({ label: "Top non-English languages" });
  }
  return unsupported;
}

/* ------------------------------------------------------------------ */
/* Subject Performance                                                 */
/* ------------------------------------------------------------------ */

function mapSubjectSummary(raw: {
  academic_year: string;
  key_stage: "ks4" | "16_to_18";
  qualification_family: string;
  exam_cohort: string | null;
  subject: string;
  entries_count_total: number;
  high_grade_count: number | null;
  high_grade_share_pct: number | null;
  pass_grade_count: number | null;
  pass_grade_share_pct: number | null;
  ranking_eligible: boolean;
}): SubjectSummaryVM {
  return {
    academicYear: raw.academic_year,
    keyStage: raw.key_stage,
    qualificationFamily: raw.qualification_family,
    examCohort: raw.exam_cohort ?? null,
    subject: raw.subject,
    entriesCountTotal: raw.entries_count_total,
    highGradeCount: raw.high_grade_count ?? null,
    highGradeSharePct: raw.high_grade_share_pct ?? null,
    passGradeCount: raw.pass_grade_count ?? null,
    passGradeSharePct: raw.pass_grade_share_pct ?? null,
  };
}

function mapSubjectPerformance(profile: SchoolProfileResponse): SubjectPerformanceVM | null {
  const sp = (profile as Record<string, unknown>).subject_performance as {
    strongest_subjects?: unknown[];
    weakest_subjects?: unknown[];
    stage_breakdowns?: unknown[];
    latest_updated_at?: string | null;
  } | null | undefined;

  if (!sp) return null;

  const strongest = (sp.strongest_subjects ?? []) as Parameters<typeof mapSubjectSummary>[0][];
  const weakest = (sp.weakest_subjects ?? []) as Parameters<typeof mapSubjectSummary>[0][];
  const breakdowns = (sp.stage_breakdowns ?? []) as Array<{
    academic_year: string;
    key_stage: "ks4" | "16_to_18";
    qualification_family: string;
    exam_cohort: string | null;
    subjects: Parameters<typeof mapSubjectSummary>[0][];
  }>;

  if (strongest.length === 0 && weakest.length === 0 && breakdowns.length === 0) {
    return null;
  }

  return {
    strongestSubjects: strongest.map(mapSubjectSummary),
    weakestSubjects: weakest.map(mapSubjectSummary),
    stageBreakdowns: breakdowns.map((b): SubjectPerformanceGroupVM => ({
      academicYear: b.academic_year,
      keyStage: b.key_stage,
      qualificationFamily: b.qualification_family,
      examCohort: b.exam_cohort ?? null,
      subjects: (b.subjects ?? []).map(mapSubjectSummary),
    })),
    latestUpdatedAt: sp.latest_updated_at ?? null,
  };
}

export function mapProfileToVM(
  profile: SchoolProfileResponse,
  trends: SchoolTrendsResponse | null,
  dashboard: SchoolTrendDashboardResponse | null
): SchoolProfileVM {
  return {
    school: mapSchool(profile),
    savedState: mapSavedSchoolState(profile.saved_state),
    overviewText: toOptionalText(profile.overview_text),
    analyst: mapAnalystSection(profile.analyst),
    demographics: mapDemographics(profile),
    attendance: mapAttendance(profile),
    behaviour: mapBehaviour(profile),
    workforce: mapWorkforce(profile),
    admissions: mapAdmissions(profile),
    destinations: mapDestinations(profile),
    finance: mapFinance(profile),
    leadership: mapLeadership(profile),
    performance: mapPerformance(profile),
    subjectPerformance: mapSubjectPerformance(profile),
    ofsted: mapOfsted(profile),
    ofstedTimeline: mapOfstedTimeline(profile),
    neighbourhood: mapNeighbourhoodSection(profile.neighbourhood),
    trends: mapTrends(trends),
    benchmarkDashboard: buildBenchmarkDashboard(profile, dashboard),
    completeness: mapCompleteness(profile, trends),
    unsupportedMetrics: mapUnsupported(profile)
  };
}

export {
  fallback,
  fmtDate,
  fmtDateTime,
  fmtMonth,
  fmtPct,
  mapCompletenessReasonToMessageKey
};
