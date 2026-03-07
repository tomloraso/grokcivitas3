import { EthnicityBreakdown } from "../../../components/data/EthnicityBreakdown";
import { MetricGrid } from "../../../components/data/MetricGrid";
import { MetricUnavailable } from "../../../components/data/MetricUnavailable";
import { Sparkline } from "../../../components/data/Sparkline";
import { StatCard } from "../../../components/data/StatCard";
import { TrendIndicator } from "../../../components/data/TrendIndicator";
import { Card } from "../../../components/ui/Card";
import {
  DEMOGRAPHICS_METRIC_KEYS,
  getMetricCatalogEntry
} from "../metricCatalog";
import { SectionCompletenessNotice } from "./SectionCompletenessNotice";
import type {
  DemographicMetricVM,
  DemographicsCategoryVM,
  DemographicsVM,
  SectionCompletenessVM,
  TrendSeriesVM,
  TrendsVM
} from "../types";

interface DemographicsAndTrendsPanelProps {
  demographics: DemographicsVM | null;
  trends: TrendsVM | null;
  demographicsCompleteness: SectionCompletenessVM;
  trendsCompleteness: SectionCompletenessVM;
}

function toSparkData(series: TrendSeriesVM | undefined): number[] {
  if (!series) {
    return [];
  }

  return series.points
    .map((point) => point.value)
    .filter((value): value is number => value !== null);
}

function renderTrendFooter(metric: DemographicMetricVM, series: TrendSeriesVM | undefined) {
  if (!series || series.latestDelta === null) {
    return null;
  }

  const sparkData = toSparkData(series);
  const period = sparkData.length > 1 ? `${sparkData.length}yr` : undefined;
  return (
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
        unit="%"
        period={period}
      />
    </div>
  );
}

function RankedListCard({
  title,
  items,
  emptyLabel
}: {
  title: string;
  items: DemographicsCategoryVM[];
  emptyLabel: string;
}): JSX.Element {
  return (
    <Card className="space-y-4">
      <div className="space-y-1">
        <h3 className="text-base font-semibold text-primary">{title}</h3>
        <p className="text-xs text-secondary">Highest published categories for the latest year.</p>
      </div>

      {items.length === 0 ? (
        <MetricUnavailable metricLabel={emptyLabel} />
      ) : (
        <ol className="space-y-2">
          {items.map((item, index) => (
            <li
              key={item.key}
              className="flex items-center justify-between gap-3 rounded-md border border-border-subtle/60 bg-surface/50 px-3 py-2"
            >
              <div className="min-w-0">
                <p className="text-sm font-medium text-primary">
                  {item.rank ?? index + 1}. {item.label}
                </p>
                <p className="text-xs text-secondary">
                  {(item.count ?? 0).toLocaleString("en-GB")} pupils
                </p>
              </div>
              <span className="text-sm font-semibold text-primary">
                {item.percentageLabel ?? "n/a"}
              </span>
            </li>
          ))}
        </ol>
      )}
    </Card>
  );
}

export function DemographicsAndTrendsPanel({
  demographics,
  trends,
  demographicsCompleteness,
  trendsCompleteness
}: DemographicsAndTrendsPanelProps): JSX.Element {
  const metricLookup = new Map(
    demographics?.metrics.map((metric) => [metric.metricKey, metric] as const) ?? []
  );
  const trendLookup = new Map(
    trends?.series.map((series) => [series.metricKey, series] as const) ?? []
  );
  const yearRange =
    trends && trends.yearsAvailable.length > 1
      ? `${trends.yearsAvailable[0]}-${trends.yearsAvailable[trends.yearsAvailable.length - 1]}`
      : demographics?.academicYear ?? null;

  const hasAnyMetrics = DEMOGRAPHICS_METRIC_KEYS.some((metricKey) => {
    const metric = metricLookup.get(metricKey);
    return metric?.value !== null;
  });

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
        {yearRange ? (
          <span className="text-xs text-secondary" style={{ opacity: "var(--text-opacity-muted)" }}>
            {yearRange}
          </span>
        ) : null}
      </div>

      <SectionCompletenessNotice
        sectionLabel="Demographics"
        completeness={demographicsCompleteness}
      />
      {trendsCompleteness.status !== "available" ? (
        <SectionCompletenessNotice sectionLabel="Demographic trends" completeness={trendsCompleteness} />
      ) : null}

      {!hasAnyMetrics ? (
        <MetricUnavailable metricLabel="Pupil demographics" />
      ) : (
        <MetricGrid columns={4}>
          {DEMOGRAPHICS_METRIC_KEYS.map((metricKey) => {
            const metric = metricLookup.get(metricKey);
            const catalog = getMetricCatalogEntry(metricKey);
            if (!metric || !catalog) {
              return null;
            }

            if (metric.value === null) {
              return <MetricUnavailable key={metricKey} metricLabel={catalog.label} />;
            }

            return (
              <StatCard
                key={metricKey}
                label={metric.label}
                description={catalog.description}
                value={metric.value}
                footer={renderTrendFooter(metric, trendLookup.get(metricKey))}
              />
            );
          })}
        </MetricGrid>
      )}

      {demographics && demographics.ethnicityBreakdown.length > 0 ? (
        <EthnicityBreakdown groups={demographics.ethnicityBreakdown} />
      ) : null}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <RankedListCard
          title="Special Educational Needs"
          items={demographics?.sendPrimaryNeeds ?? []}
          emptyLabel="Special educational needs breakdown"
        />
        <RankedListCard
          title="Top Home Languages"
          items={demographics?.topHomeLanguages ?? []}
          emptyLabel="Top non-English languages"
        />
      </div>
    </section>
  );
}
