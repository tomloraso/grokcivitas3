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
  PerformanceVM,
  PerformanceYearVM,
  SectionCompletenessVM,
  TrendSeriesVM,
  TrendsVM
} from "../types";

/* ------------------------------------------------------------------ */
/* Props                                                               */
/* ------------------------------------------------------------------ */

interface DemographicsAndTrendsPanelProps {
  demographics: DemographicsVM | null;
  performance: PerformanceVM | null;
  trends: TrendsVM | null;
  demographicsCompleteness: SectionCompletenessVM;
  performanceCompleteness: SectionCompletenessVM;
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

type PerformanceValueType = "score_1dp" | "score_2dp" | "pct";

interface PerformanceMetricDefinition {
  key: string;
  label: string;
  valueType: PerformanceValueType;
  value: (year: PerformanceYearVM) => number | null;
}

const PERFORMANCE_METRICS: PerformanceMetricDefinition[] = [
  {
    key: "attainment8_average",
    label: "Attainment 8",
    valueType: "score_1dp",
    value: (year) => year.attainment8Average
  },
  {
    key: "progress8_average",
    label: "Progress 8",
    valueType: "score_2dp",
    value: (year) => year.progress8Average
  },
  {
    key: "progress8_disadvantaged_gap",
    label: "Progress 8 disadvantaged gap",
    valueType: "score_2dp",
    value: (year) => year.progress8DisadvantagedGap
  },
  {
    key: "engmath_5_plus_pct",
    label: "Grade 5+ English & Maths",
    valueType: "pct",
    value: (year) => year.engmath5PlusPct
  },
  {
    key: "engmath_4_plus_pct",
    label: "Grade 4+ English & Maths",
    valueType: "pct",
    value: (year) => year.engmath4PlusPct
  },
  {
    key: "ebacc_entry_pct",
    label: "EBacc entry",
    valueType: "pct",
    value: (year) => year.ebaccEntryPct
  },
  {
    key: "ebacc_5_plus_pct",
    label: "EBacc grade 5+",
    valueType: "pct",
    value: (year) => year.ebacc5PlusPct
  },
  {
    key: "ks2_reading_expected_pct",
    label: "KS2 reading expected standard",
    valueType: "pct",
    value: (year) => year.ks2ReadingExpectedPct
  },
  {
    key: "ks2_writing_expected_pct",
    label: "KS2 writing expected standard",
    valueType: "pct",
    value: (year) => year.ks2WritingExpectedPct
  },
  {
    key: "ks2_maths_expected_pct",
    label: "KS2 maths expected standard",
    valueType: "pct",
    value: (year) => year.ks2MathsExpectedPct
  },
  {
    key: "ks2_combined_expected_pct",
    label: "KS2 combined expected standard",
    valueType: "pct",
    value: (year) => year.ks2CombinedExpectedPct
  }
];

function formatPerformanceValue(value: number | null, valueType: PerformanceValueType): string | null {
  if (value === null) {
    return null;
  }

  if (valueType === "pct") {
    return `${value.toFixed(1)}%`;
  }
  if (valueType === "score_1dp") {
    return value.toFixed(1);
  }
  return value.toFixed(2);
}

function directionFromDelta(delta: number): "up" | "down" | "flat" {
  if (delta > 0) {
    return "up";
  }
  if (delta < 0) {
    return "down";
  }
  return "flat";
}

export function DemographicsAndTrendsPanel({
  demographics,
  performance,
  trends,
  demographicsCompleteness,
  performanceCompleteness,
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
  const performanceYearRange =
    performance && performance.history.length > 1
      ? `${performance.history[0]?.academicYear ?? ""}-${
          performance.history[performance.history.length - 1]?.academicYear ?? ""
        }`
      : performance?.latest?.academicYear ?? null;
  const performanceLatest = performance?.latest ?? null;

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

      <div className="space-y-4 border-t border-border-subtle/50 pt-4">
        <div className="flex items-baseline justify-between gap-3">
          <h3 className="text-base font-semibold text-primary">School Performance</h3>
          <span
            className="text-xs text-secondary"
            style={{ opacity: "var(--text-opacity-muted)" }}
          >
            {performanceYearRange}
          </span>
        </div>

        <SectionCompletenessNotice
          sectionLabel="Performance"
          completeness={performanceCompleteness}
        />

        {performance && performanceLatest ? (
          <MetricGrid columns={3}>
            {PERFORMANCE_METRICS.map((definition) => {
              const latestValue = definition.value(performanceLatest);
              if (latestValue === null) {
                return null;
              }

              const historyValues = performance.history
                .map((year) => definition.value(year))
                .filter((value): value is number => value !== null);
              const previousYear =
                performance.history.length >= 2
                  ? performance.history[performance.history.length - 2]
                  : null;
              const previousValue = previousYear ? definition.value(previousYear) : null;
              const delta =
                previousValue !== null ? Number((latestValue - previousValue).toFixed(2)) : null;

              return (
                <StatCard
                  key={definition.key}
                  label={definition.label}
                  value={formatPerformanceValue(latestValue, definition.valueType) ?? "Not published"}
                  footer={
                    delta !== null ? (
                      <div className="flex items-center justify-between gap-2">
                        {historyValues.length > 1 ? (
                          <Sparkline
                            data={historyValues}
                            width={92}
                            height={30}
                            aria-label={`${definition.label} trend`}
                          />
                        ) : null}
                        {definition.valueType === "pct" ? (
                          <TrendIndicator
                            delta={delta}
                            direction={directionFromDelta(delta)}
                            unit="pp"
                          />
                        ) : (
                          <TrendIndicator
                            delta={delta}
                            direction={directionFromDelta(delta)}
                            asPercentage={false}
                          />
                        )}
                      </div>
                    ) : null
                  }
                />
              );
            }).filter((card): card is JSX.Element => card !== null)}
          </MetricGrid>
        ) : (
          <MetricUnavailable metricLabel="School performance" />
        )}
      </div>
    </section>
  );
}
