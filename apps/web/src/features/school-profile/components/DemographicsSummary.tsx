import { MetricGrid } from "../../../components/data/MetricGrid";
import { MetricUnavailable } from "../../../components/data/MetricUnavailable";
import { StatCard } from "../../../components/data/StatCard";
import { TrendIndicator } from "../../../components/data/TrendIndicator";
import { SectionCompletenessNotice } from "./SectionCompletenessNotice";
import type { DemographicsVM, SectionCompletenessVM, TrendsVM } from "../types";

interface DemographicsSummaryProps {
  demographics: DemographicsVM | null;
  trends: TrendsVM | null;
  completeness: SectionCompletenessVM;
}

export function DemographicsSummary({
  demographics,
  trends,
  completeness
}: DemographicsSummaryProps): JSX.Element {
  if (!demographics) {
    return (
      <section aria-labelledby="demographics-heading">
        <div className="mb-5 flex items-baseline justify-between gap-3">
          <h2
            id="demographics-heading"
            className="text-lg font-semibold text-primary sm:text-xl"
          >
            Demographics
          </h2>
        </div>
        <div className="space-y-3">
          <SectionCompletenessNotice sectionLabel="Demographics" completeness={completeness} />
          <MetricUnavailable metricLabel="Demographics" />
        </div>
      </section>
    );
  }

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
      <SectionCompletenessNotice sectionLabel="Demographics" completeness={completeness} />

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
