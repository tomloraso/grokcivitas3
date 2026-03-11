import { MetricGrid } from "../../../components/data/MetricGrid";
import { MetricUnavailable } from "../../../components/data/MetricUnavailable";
import { Sparkline } from "../../../components/data/Sparkline";
import { TrendIndicator } from "../../../components/data/TrendIndicator";
import { StatCard } from "../../../components/ui/stat-card";
import {
  formatMetricValue,
  getMetricCatalogEntry
} from "../metricCatalog";
import { siteConfig } from "../../../shared/config/site";
import { SectionCompletenessNotice } from "./SectionCompletenessNotice";
import type {
  SchoolDestinationStageLatestVM,
  SchoolDestinationsVM,
  SectionCompletenessVM,
  TrendSeriesVM,
  TrendsVM
} from "../types";

interface SchoolDestinationsSectionProps {
  destinations: SchoolDestinationsVM | null;
  trends: TrendsVM | null;
  completeness: SectionCompletenessVM;
  trendsCompleteness: SectionCompletenessVM;
}

interface DestinationMetricDef {
  metricKey: string;
  value: (stage: SchoolDestinationStageLatestVM) => number | null;
}

const KS4_SUMMARY_METRICS: DestinationMetricDef[] = [
  { metricKey: "ks4_overall_pct", value: (stage) => stage.overallPct },
  { metricKey: "ks4_education_pct", value: (stage) => stage.educationPct },
  { metricKey: "ks4_apprenticeship_pct", value: (stage) => stage.apprenticeshipPct },
  { metricKey: "ks4_employment_pct", value: (stage) => stage.employmentPct },
  { metricKey: "ks4_not_sustained_pct", value: (stage) => stage.notSustainedPct },
  { metricKey: "ks4_activity_unknown_pct", value: (stage) => stage.activityUnknownPct }
];

const KS4_EDUCATION_BREAKDOWN_METRICS: DestinationMetricDef[] = [
  { metricKey: "ks4_fe_pct", value: (stage) => stage.fePct },
  { metricKey: "ks4_other_education_pct", value: (stage) => stage.otherEducationPct },
  { metricKey: "ks4_school_sixth_form_pct", value: (stage) => stage.schoolSixthFormPct },
  { metricKey: "ks4_sixth_form_college_pct", value: (stage) => stage.sixthFormCollegePct }
];

const STUDY_16_18_SUMMARY_METRICS: DestinationMetricDef[] = [
  { metricKey: "study_16_18_overall_pct", value: (stage) => stage.overallPct },
  { metricKey: "study_16_18_education_pct", value: (stage) => stage.educationPct },
  { metricKey: "study_16_18_apprenticeship_pct", value: (stage) => stage.apprenticeshipPct },
  { metricKey: "study_16_18_employment_pct", value: (stage) => stage.employmentPct },
  { metricKey: "study_16_18_not_sustained_pct", value: (stage) => stage.notSustainedPct },
  { metricKey: "study_16_18_activity_unknown_pct", value: (stage) => stage.activityUnknownPct }
];

const STUDY_16_18_EDUCATION_BREAKDOWN_METRICS: DestinationMetricDef[] = [
  { metricKey: "study_16_18_fe_pct", value: (stage) => stage.fePct },
  { metricKey: "study_16_18_other_education_pct", value: (stage) => stage.otherEducationPct },
  { metricKey: "study_16_18_higher_education_pct", value: (stage) => stage.higherEducationPct }
];

function renderTrendFooter(series: TrendSeriesVM | undefined) {
  if (!series || series.latestDelta === null) {
    return null;
  }

  const sparkData = series.points
    .map((point) => point.value)
    .filter((value): value is number => value !== null);
  const period = sparkData.length > 1 ? `${sparkData.length}-yr trend` : undefined;

  return (
    <div className="space-y-1.5">
      {sparkData.length > 1 ? (
        <Sparkline
          data={sparkData}
          height={30}
          className="w-full"
          aria-label={`${series.label} trend`}
        />
      ) : null}
      <TrendIndicator
        delta={series.latestDelta}
        direction={series.latestDirection ?? undefined}
        unit="%"
        period={period}
      />
    </div>
  );
}

function renderMetricCards(
  metrics: DestinationMetricDef[],
  stage: SchoolDestinationStageLatestVM,
  trendLookup: Map<string, TrendSeriesVM>
): JSX.Element[] {
  return metrics.flatMap(({ metricKey, value }) => {
    const catalog = getMetricCatalogEntry(metricKey);
    const rawValue = value(stage);
    if (!catalog || rawValue === null) {
      return [];
    }

    return (
      <StatCard
        key={metricKey}
        label={catalog.label}
        description={catalog.description}
        value={formatMetricValue(rawValue, catalog.unit, catalog.decimals) ?? "n/a"}
        footer={renderTrendFooter(trendLookup.get(metricKey))}
        variant={metricKey.endsWith("overall_pct") ? "hero" : "default"}
      />
    );
  });
}

function renderStageBlock({
  title,
  description,
  stage,
  trendLookup,
  summaryMetrics,
  breakdownMetrics
}: {
  title: string;
  description: string;
  stage: SchoolDestinationStageLatestVM;
  trendLookup: Map<string, TrendSeriesVM>;
  summaryMetrics: DestinationMetricDef[];
  breakdownMetrics: DestinationMetricDef[];
}): JSX.Element {
  const summaryCards = renderMetricCards(summaryMetrics, stage, trendLookup);
  const breakdownCards = renderMetricCards(breakdownMetrics, stage, trendLookup);
  const cohortLabel = formatMetricValue(stage.cohortCount, "count");
  const qualificationLabel = [stage.qualificationGroup, stage.qualificationLevel]
    .filter((value): value is string => Boolean(value))
    .join(" - ");

  return (
    <div className="space-y-4 rounded-lg border border-border-subtle/50 bg-surface/30 p-4 sm:space-y-5 sm:p-5">
      <div className="space-y-1">
        <div className="flex flex-wrap items-baseline justify-between gap-3">
          <h3 className="text-base font-semibold text-primary">{title}</h3>
          <div className="flex flex-wrap items-center gap-2 text-xs text-secondary">
            <span>{stage.academicYear}</span>
            {cohortLabel ? <span>{`${cohortLabel} pupils`}</span> : null}
            {qualificationLabel ? <span>{qualificationLabel}</span> : null}
          </div>
        </div>
        <p className="text-sm text-secondary">{description}</p>
      </div>

      {summaryCards.length === 0 && breakdownCards.length === 0 ? (
        <MetricUnavailable metricLabel={`${title} destinations`} />
      ) : (
        <div className="space-y-5">
          {summaryCards.length > 0 ? (
            <MetricGrid columns={3} mobileTwo>
              {summaryCards}
            </MetricGrid>
          ) : null}
          {breakdownCards.length > 0 ? (
            <div className="space-y-3">
              <h4 className="text-sm font-medium text-secondary">
                Education Breakdown
              </h4>
              <MetricGrid columns={4} mobileTwo>
                {breakdownCards}
              </MetricGrid>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}

export function SchoolDestinationsSection({
  destinations,
  trends,
  completeness,
  trendsCompleteness
}: SchoolDestinationsSectionProps): JSX.Element {
  const trendLookup = new Map(
    trends?.series.map((series) => [series.metricKey, series] as const) ?? []
  );
  const yearRange =
    trends && trends.yearsAvailable.length > 1
      ? `${trends.yearsAvailable[0]}-${trends.yearsAvailable[trends.yearsAvailable.length - 1]}`
      : destinations?.ks4?.academicYear ?? destinations?.study16To18?.academicYear ?? null;
  const hasVisibleStage = destinations?.ks4 != null || destinations?.study16To18 != null;

  return (
    <section
      aria-labelledby="leaver-destinations-heading"
      className="panel-surface rounded-lg space-y-4 p-4 sm:space-y-5 sm:p-6"
    >
      <div className="flex items-baseline justify-between gap-3">
        <h2
          id="leaver-destinations-heading"
          className="flex items-center gap-2 text-lg font-semibold text-primary sm:text-xl"
        >
          <span className="inline-block h-5 w-[3px] rounded-full bg-brand" aria-hidden />
          Leaver Destinations
        </h2>
        {yearRange ? <span className="text-xs text-secondary">{yearRange}</span> : null}
      </div>

      <p className="text-sm text-secondary">
        Published sustained destinations after pupils leave the school, broken out by stage where available.
      </p>

      <SectionCompletenessNotice
        sectionLabel="Leaver destinations"
        completeness={completeness}
      />
      {trendsCompleteness.status !== "available" ? (
        <SectionCompletenessNotice
          sectionLabel="Leaver destination trends"
          completeness={trendsCompleteness}
        />
      ) : null}

      {!hasVisibleStage ? (
        <MetricUnavailable metricLabel="School leaver destinations" />
      ) : (
        <div className="space-y-4">
          {destinations?.ks4 ? (
            renderStageBlock({
              title: "KS4 Destinations",
              description:
                "Sustained destinations after pupils complete key stage 4 study.",
              stage: destinations.ks4,
              trendLookup,
              summaryMetrics: KS4_SUMMARY_METRICS,
              breakdownMetrics: KS4_EDUCATION_BREAKDOWN_METRICS
            })
          ) : null}

          {destinations?.study16To18 ? (
            renderStageBlock({
              title: "16 to 18 Study Destinations",
              description:
                "Sustained destinations after pupils finish 16 to 18 study programmes.",
              stage: destinations.study16To18,
              trendLookup,
              summaryMetrics: STUDY_16_18_SUMMARY_METRICS,
              breakdownMetrics: STUDY_16_18_EDUCATION_BREAKDOWN_METRICS
            })
          ) : null}
        </div>
      )}

      {completeness.reasonCode === "unsupported_stage" && destinations?.study16To18 === null ? (
        <div className="rounded-lg border border-border-subtle/60 bg-surface/40 px-4 py-3 text-sm text-secondary">
          16 to 18 study destinations are present in the source data for some schools,
          but this stage is not yet shown in {siteConfig.productName}.
        </div>
      ) : null}
    </section>
  );
}
