import { MetricUnavailable } from "../../../components/data/MetricUnavailable";
import { StatCard } from "../../../components/data/StatCard";
import { Card } from "../../../components/ui/Card";
import type { AreaContextVM } from "../types";

interface AreaCrimeSummaryCardProps {
  areaContext: AreaContextVM;
}

export function AreaCrimeSummaryCard({
  areaContext
}: AreaCrimeSummaryCardProps): JSX.Element {
  const crime = areaContext.coverage.hasCrime && areaContext.crime ? areaContext.crime : null;

  return (
    <Card className="space-y-5 p-5 sm:p-6">
      <div className="space-y-1">
        <h2 className="text-lg font-semibold text-primary sm:text-xl">Area Crime</h2>
        <p className="text-xs text-secondary">
          Within {crime ? crime.radiusMiles : 1} mile radius
        </p>
      </div>

      {crime ? (
        <>
          <StatCard
            label={`Total incidents (${crime.latestMonth})`}
            value={crime.totalIncidents.toLocaleString("en-GB")}
          />

          {crime.categories.length > 0 ? (
            <div className="space-y-2" aria-label="Crime categories">
              {crime.categories.slice(0, 5).map((category) => (
                <div
                  key={category.category}
                  className="flex items-center justify-between rounded-md border border-border-subtle/60 bg-surface/50 px-3 py-2"
                >
                  <span className="text-sm text-primary">{category.category}</span>
                  <span className="text-sm font-medium text-secondary">
                    {category.incidentCount.toLocaleString("en-GB")}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <MetricUnavailable metricLabel="Crime category breakdown" />
          )}
        </>
      ) : (
        <MetricUnavailable metricLabel="Area crime context" />
      )}
    </Card>
  );
}
