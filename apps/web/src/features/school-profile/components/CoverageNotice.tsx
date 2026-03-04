import { CircleOff, Clock } from "lucide-react";

import type { ProfileCompletenessVM, UnsupportedMetricVM } from "../types";

interface CoverageNoticeProps {
  unsupportedMetrics: UnsupportedMetricVM[];
  completeness: ProfileCompletenessVM;
}

/**
 * Parent-friendly labels for why a dataset may not be shown.
 */
const COVERAGE_REASON_LABELS: Record<string, string> = {
  fsm: "Free School Meals figures are reported differently for this school type.",
  ethnicity: "Ethnicity breakdown hasn't been published for this school yet.",
  languages: "Language data hasn't been published for this school yet."
};

/**
 * Map unsupported metric labels to a reason key for parent-friendly copy.
 */
function reasonKeyForLabel(label: string): string | null {
  if (label.toLowerCase().includes("free school meals")) return "fsm";
  if (label.toLowerCase().includes("ethnicity")) return "ethnicity";
  if (label.toLowerCase().includes("language")) return "languages";
  return null;
}

function formatRefreshed(completeness: ProfileCompletenessVM): string | null {
  // Find the most recent refresh across all sections
  const dates = [
    completeness.demographics.lastUpdatedAt,
    completeness.trends.lastUpdatedAt,
    completeness.ofstedLatest.lastUpdatedAt,
    completeness.ofstedTimeline.lastUpdatedAt,
    completeness.areaDeprivation.lastUpdatedAt,
    completeness.areaCrime.lastUpdatedAt
  ].filter((d): d is string => d !== null);

  if (dates.length === 0) return null;
  // Dates are already formatted by the mapper, pick the latest by string sort
  return dates.sort().reverse()[0];
}

export function CoverageNotice({
  unsupportedMetrics,
  completeness
}: CoverageNoticeProps): JSX.Element | null {
  if (unsupportedMetrics.length === 0) return null;

  const latestRefresh = formatRefreshed(completeness);

  return (
    <section aria-labelledby="coverage-heading">
      <h2
        id="coverage-heading"
        className="mb-3 text-sm font-medium uppercase tracking-[0.08em] text-secondary"
      >
        Data Coverage
      </h2>
      <div className="space-y-2">
        {unsupportedMetrics.map((metric) => {
          const reasonKey = reasonKeyForLabel(metric.label);
          const reason = reasonKey ? COVERAGE_REASON_LABELS[reasonKey] : null;

          return (
            <div
              key={metric.label}
              className="flex flex-col gap-0.5 rounded-lg border border-dashed border-border bg-surface/50 px-4 py-3 text-sm text-disabled"
              role="status"
              aria-label={`${metric.label} data is not available`}
            >
              <span className="inline-flex items-center gap-2">
                <CircleOff className="h-4 w-4 shrink-0" aria-hidden />
                {metric.label}
              </span>
              {reason ? (
                <span className="pl-6 text-xs text-secondary">{reason}</span>
              ) : null}
            </div>
          );
        })}
      </div>
      {latestRefresh ? (
        <p className="mt-3 inline-flex items-center gap-1.5 text-xs text-disabled">
          <Clock className="h-3 w-3" aria-hidden />
          Profile last refreshed: {latestRefresh}
        </p>
      ) : null}
    </section>
  );
}
