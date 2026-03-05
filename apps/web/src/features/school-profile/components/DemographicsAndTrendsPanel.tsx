import { EthnicityBreakdown } from "../../../components/data/EthnicityBreakdown";
import { GlossaryTerm } from "../../../components/data/GlossaryTerm";
import { MetricGrid } from "../../../components/data/MetricGrid";
import { MetricUnavailable } from "../../../components/data/MetricUnavailable";
import { Sparkline } from "../../../components/data/Sparkline";
import { StatCard } from "../../../components/data/StatCard";
import { TrendIndicator } from "../../../components/data/TrendIndicator";
import { SectionCompletenessNotice } from "./SectionCompletenessNotice";
import type {
  DemographicMetricVM,
  DemographicsVM,
  SectionCompletenessVM,
  TrendSeriesVM,
  TrendsVM
} from "../types";

/* ------------------------------------------------------------------ */
/* Props                                                               */
/* ------------------------------------------------------------------ */

interface DemographicsAndTrendsPanelProps {
  demographics: DemographicsVM | null;
  trends: TrendsVM | null;
  demographicsCompleteness: SectionCompletenessVM;
  trendsCompleteness: SectionCompletenessVM;
}

/* ------------------------------------------------------------------ */
/* Glossary wiring                                                     */
/* ------------------------------------------------------------------ */

const METRIC_GLOSSARY_KEYS: Record<string, string> = {
  disadvantaged_pct: "disadvantaged",
  fsm_pct: "fsm",
  sen_pct: "sen",
  ehcp_pct: "ehcp",
  eal_pct: "eal",
  first_language_english_pct: "first_language_english",
  first_language_unclassified_pct: "first_language_unclassified"
};

function glossaryLabel(metricKey: string, fallbackLabel: string): React.ReactNode {
  const key = METRIC_GLOSSARY_KEYS[metricKey];
  return key ? <GlossaryTerm term={key}>{fallbackLabel}</GlossaryTerm> : fallbackLabel;
}

const ALL_METRIC_KEYS = [
  "disadvantaged_pct",
  "sen_pct",
  "ehcp_pct",
  "eal_pct",
  "first_language_english_pct",
  "first_language_unclassified_pct"
] as const;

const METRIC_LABEL_OVERRIDES: Record<string, string> = {
  disadvantaged_pct: "Disadvantaged (DfE measure)",
  eal_pct: "EAL"
};

function displayLabel(metric: DemographicMetricVM): string {
  return METRIC_LABEL_OVERRIDES[metric.metricKey] ?? metric.label;
}

function buildMetricLookup(
  demographics: DemographicsVM | null
): Map<string, DemographicMetricVM> {
  return new Map(demographics?.metrics.map((metric) => [metric.metricKey, metric]) ?? []);
}

function toSparkData(series: TrendSeriesVM): number[] {
  return series.points
    .map((point) => point.value)
    .filter((value): value is number => value !== null);
}

export function DemographicsAndTrendsPanel({
  demographics,
  trends,
  demographicsCompleteness,
  trendsCompleteness
}: DemographicsAndTrendsPanelProps): JSX.Element {
  const metricLookup = buildMetricLookup(demographics);

  const hasTrendableData = trends !== null && trends.yearsCount >= 2;
  const trendableSeries = hasTrendableData
    ? trends.series.filter((series) => series.points.length >= 2 && series.latestDelta !== null)
    : [];
  const trendSeriesByMetric = new Map(
    trendableSeries.map((series) => [series.metricKey, series] as const)
  );
  const trendYearRange =
    trends && trends.yearsAvailable.length > 1
      ? `${trends.yearsAvailable[0]}-${trends.yearsAvailable[trends.yearsAvailable.length - 1]}`
      : null;

  const visibleMetrics = ALL_METRIC_KEYS.map((key) => metricLookup.get(key)).filter(
    (m): m is DemographicMetricVM => m !== undefined && m.value !== null
  );

  return (
    <section
      aria-labelledby="demographics-heading"
      className="panel-surface rounded-lg space-y-5 p-5 sm:p-6"
    >
      <div className="flex items-baseline justify-between gap-3">
        <h2
          id="demographics-heading"
          className="flex items-center gap-2 text-lg font-semibold text-primary sm:text-xl"
        >
          <span className="inline-block h-5 w-[3px] rounded-full bg-brand" aria-hidden />
          Pupil Demographics
        </h2>
        <span
          className="text-xs text-secondary"
          style={{ opacity: "var(--text-opacity-muted)" }}
        >
          {[demographics?.academicYear, trendYearRange].filter(Boolean).join(" | ")}
        </span>
      </div>

      <SectionCompletenessNotice
        sectionLabel="Demographics"
        completeness={demographicsCompleteness}
      />
      {trendsCompleteness.status !== "available" ? (
        <SectionCompletenessNotice
          sectionLabel="Trends"
          completeness={trendsCompleteness}
        />
      ) : null}

      {visibleMetrics.length > 0 ? (
        <MetricGrid columns={3}>
          {visibleMetrics.map((metric) => {
            const series = trendSeriesByMetric.get(metric.metricKey);
            const sparkData = series ? toSparkData(series) : [];

            return (
              <StatCard
                key={metric.metricKey}
                label={glossaryLabel(metric.metricKey, displayLabel(metric))}
                value={metric.value!}
                footer={
                  series && series.latestDelta !== null ? (
                    <div className="flex items-center justify-between gap-2">
                      {sparkData.length > 1 ? (
                        <Sparkline
                          data={sparkData}
                          width={92}
                          height={30}
                          aria-label={`${metric.label} trend`}
                        />
                      ) : null}
                      <TrendIndicator
                        delta={series.latestDelta}
                        direction={series.latestDirection ?? undefined}
                        unit="pp"
                      />
                    </div>
                  ) : null
                }
              />
            );
          })}
        </MetricGrid>
      ) : (
        <MetricUnavailable metricLabel="Pupil demographics" />
      )}

      {demographics && demographics.ethnicityBreakdown.length > 0 ? (
        <EthnicityBreakdown groups={demographics.ethnicityBreakdown} />
      ) : null}
    </section>
  );
}
