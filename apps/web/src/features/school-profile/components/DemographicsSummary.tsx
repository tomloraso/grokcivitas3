import { MetricGrid } from "../../../components/data/MetricGrid";
import { StatCard } from "../../../components/data/StatCard";
import { TrendIndicator } from "../../../components/data/TrendIndicator";
import type { DemographicsVM, TrendsVM } from "../types";

interface DemographicsSummaryProps {
  demographics: DemographicsVM;
  trends: TrendsVM | null;
}

export function DemographicsSummary({
  demographics,
  trends
}: DemographicsSummaryProps): JSX.Element {
  return (
    <section aria-labelledby="demographics-heading">
      <div className="mb-5 flex items-baseline justify-between gap-3">
        <h2
          id="demographics-heading"
          className="text-lg font-semibold text-primary sm:text-xl"
        >
          Demographics
        </h2>
        <span className="text-xs text-secondary" style={{ opacity: "var(--text-opacity-muted)" }}>
          {demographics.academicYear}
        </span>
      </div>

      <MetricGrid columns={3}>
        {demographics.metrics
          .filter((m) => m.value !== null)
          .map((metric) => {
            // Find matching trend series for this metric
            const trendSeries = trends?.series.find(
              (s) => s.metricKey === metric.metricKey
            );

            const footer =
              trendSeries?.latestDelta !== null && trendSeries?.latestDelta !== undefined ? (
                <TrendIndicator
                  delta={trendSeries.latestDelta}
                  direction={trendSeries.latestDirection ?? undefined}
                />
              ) : null;

            return (
              <StatCard
                key={metric.metricKey}
                label={metric.label}
                value={metric.value!}
                footer={footer}
              />
            );
          })}
      </MetricGrid>
    </section>
  );
}
