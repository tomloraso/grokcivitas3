import { MetricUnavailable } from "../../../components/data/MetricUnavailable";
import type { UnsupportedMetricVM } from "../types";

interface CoverageNoticeProps {
  unsupportedMetrics: UnsupportedMetricVM[];
}

export function CoverageNotice({
  unsupportedMetrics
}: CoverageNoticeProps): JSX.Element | null {
  if (unsupportedMetrics.length === 0) return null;

  return (
    <section aria-labelledby="coverage-heading">
      <h2
        id="coverage-heading"
        className="mb-3 text-sm font-medium uppercase tracking-[0.08em] text-secondary"
      >
        Data Coverage
      </h2>
      <div className="space-y-2">
        {unsupportedMetrics.map((metric) => (
          <MetricUnavailable key={metric.label} metricLabel={metric.label} />
        ))}
      </div>
    </section>
  );
}
