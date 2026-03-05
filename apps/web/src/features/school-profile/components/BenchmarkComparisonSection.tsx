import { MetricGrid } from "../../../components/data/MetricGrid";
import { MetricUnavailable } from "../../../components/data/MetricUnavailable";
import { Sparkline } from "../../../components/data/Sparkline";
import { Card } from "../../../components/ui/Card";
import { formatMetricDelta, formatMetricValue } from "../metricCatalog";
import { SectionCompletenessNotice } from "./SectionCompletenessNotice";
import type { BenchmarkDashboardVM, BenchmarkMetricVM } from "../types";

interface BenchmarkComparisonSectionProps {
  benchmarkDashboard: BenchmarkDashboardVM | null;
}

function DeltaLabel({
  label,
  value,
  unit
}: {
  label: string;
  value: number | null;
  unit: BenchmarkMetricVM["unit"];
}): JSX.Element | null {
  const formatted = formatMetricDelta(value, unit);
  if (!formatted) {
    return null;
  }

  const colorClass =
    value === null ? "text-secondary" : value > 0 ? "text-trend-up" : value < 0 ? "text-trend-down" : "text-trend-flat";

  return (
    <p className={`text-xs font-medium ${colorClass}`}>
      {label}: {formatted}
    </p>
  );
}

function BenchmarkCard({ metric }: { metric: BenchmarkMetricVM }): JSX.Element {
  const schoolSparkline = metric.trendPoints
    .map((point) => point.schoolValue)
    .filter((value): value is number => value !== null);

  return (
    <Card className="space-y-4">
      <div className="space-y-1">
        <p className="text-xs font-medium uppercase tracking-[0.08em] text-secondary">
          {metric.label}
        </p>
        <p className="font-display text-3xl font-bold leading-tight tracking-tight text-primary">
          {formatMetricValue(metric.schoolValue, metric.unit) ?? "Not available"}
        </p>
        <p className="text-xs text-secondary">{metric.academicYear}</p>
      </div>

      {schoolSparkline.length > 1 ? (
        <Sparkline
          data={schoolSparkline}
          width={132}
          height={34}
          aria-label={`${metric.label} benchmark trend`}
        />
      ) : null}

      <div className="space-y-2 text-sm text-secondary">
        <div className="flex items-center justify-between gap-2">
          <span>{metric.localAreaLabel}</span>
          <span className="font-medium text-primary">
            {formatMetricValue(metric.localValue, metric.unit) ?? "n/a"}
          </span>
        </div>
        <div className="flex items-center justify-between gap-2">
          <span>England</span>
          <span className="font-medium text-primary">
            {formatMetricValue(metric.nationalValue, metric.unit) ?? "n/a"}
          </span>
        </div>
      </div>

      <div className="space-y-1 border-t border-border-subtle/50 pt-3">
        <DeltaLabel label={`Vs ${metric.localAreaLabel}`} value={metric.schoolVsLocalDelta} unit={metric.unit} />
        <DeltaLabel label="Vs England" value={metric.schoolVsNationalDelta} unit={metric.unit} />
      </div>
    </Card>
  );
}

export function BenchmarkComparisonSection({
  benchmarkDashboard
}: BenchmarkComparisonSectionProps): JSX.Element {
  return (
    <section
      aria-labelledby="benchmarks-heading"
      className="panel-surface rounded-lg space-y-6 p-5 sm:p-6"
    >
      <div className="space-y-1">
        <h2
          id="benchmarks-heading"
          className="flex items-center gap-2 text-lg font-semibold text-primary sm:text-xl"
        >
          <span className="inline-block h-5 w-[3px] rounded-full bg-brand" aria-hidden />
          Benchmark Comparison
        </h2>
        <p className="text-sm text-secondary">
          Latest school values compared with England and the relevant local benchmark.
        </p>
      </div>

      {benchmarkDashboard?.completeness ? (
        <SectionCompletenessNotice
          sectionLabel="Benchmark trends"
          completeness={benchmarkDashboard.completeness}
        />
      ) : null}

      {!benchmarkDashboard || benchmarkDashboard.sections.length === 0 ? (
        <MetricUnavailable metricLabel="Benchmark comparison" />
      ) : (
        <div className="space-y-6">
          {benchmarkDashboard.sections.map((section) => (
            <div key={section.key} className="space-y-3">
              <div className="flex items-baseline justify-between gap-3">
                <h3 className="text-base font-semibold text-primary">{section.label}</h3>
                {benchmarkDashboard.yearsAvailable.length > 0 ? (
                  <span className="text-xs text-secondary">
                    {benchmarkDashboard.yearsAvailable[0]}-
                    {benchmarkDashboard.yearsAvailable[benchmarkDashboard.yearsAvailable.length - 1]}
                  </span>
                ) : null}
              </div>
              <MetricGrid columns={3}>
                {section.metrics.map((metric) => (
                  <BenchmarkCard key={metric.metricKey} metric={metric} />
                ))}
              </MetricGrid>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
