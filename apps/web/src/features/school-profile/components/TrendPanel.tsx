import { AlertTriangle } from "lucide-react";

import { MetricGrid } from "../../../components/data/MetricGrid";
import { Sparkline } from "../../../components/data/Sparkline";
import { StatCard } from "../../../components/data/StatCard";
import { TrendIndicator } from "../../../components/data/TrendIndicator";
import type { TrendsVM } from "../types";

interface TrendPanelProps {
  trends: TrendsVM;
}

export function TrendPanel({ trends }: TrendPanelProps): JSX.Element {
  const hasData = trends.series.some((s) => s.points.length > 0);

  return (
    <section aria-labelledby="trends-heading">
      <div className="mb-4 flex items-baseline justify-between gap-3">
        <h2 id="trends-heading" className="text-lg font-semibold text-primary sm:text-xl">
          Trends
        </h2>
        {trends.yearsAvailable.length > 0 ? (
          <span className="text-xs text-secondary">
            {trends.yearsAvailable[0]}
            {trends.yearsAvailable.length > 1
              ? ` - ${trends.yearsAvailable[trends.yearsAvailable.length - 1]}`
              : ""}
          </span>
        ) : null}
      </div>

      {trends.isPartialHistory ? (
        <div
          className="mb-4 flex items-center gap-2 rounded-lg border border-warning/30 bg-warning/10 px-4 py-2.5 text-sm text-secondary"
          role="status"
        >
          <AlertTriangle className="h-4 w-4 shrink-0 text-warning" aria-hidden />
          <span>
            Limited history available ({trends.yearsCount} {trends.yearsCount === 1 ? "year" : "years"}).
            Trend deltas require at least 2 years of data.
          </span>
        </div>
      ) : null}

      {hasData ? (
        <MetricGrid columns={2}>
          {trends.series
            .filter((s) => s.points.length > 0)
            .map((series) => {
              const sparkData = series.points
                .map((p) => p.value)
                .filter((v): v is number => v !== null);

              const latestPoint =
                series.points.length > 0 ? series.points[series.points.length - 1] : null;

              const displayValue =
                latestPoint?.value !== null && latestPoint?.value !== undefined
                  ? `${latestPoint.value.toFixed(1)}%`
                  : "N/A";

              const footer = (
                <div className="flex items-center gap-3">
                  {sparkData.length > 1 ? (
                    <Sparkline
                      data={sparkData}
                      width={72}
                      height={24}
                      aria-label={`${series.label} trend line`}
                    />
                  ) : null}
                  {series.latestDelta !== null ? (
                    <TrendIndicator
                      delta={series.latestDelta}
                      direction={series.latestDirection ?? undefined}
                    />
                  ) : null}
                </div>
              );

              return (
                <StatCard
                  key={series.metricKey}
                  label={series.label}
                  value={displayValue}
                  footer={footer}
                />
              );
            })}
        </MetricGrid>
      ) : (
        <p className="text-sm text-secondary">No trend data available for this school.</p>
      )}
    </section>
  );
}
