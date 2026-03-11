import { Clock, Info } from "lucide-react";

import type { ProfileCompletenessVM, UnsupportedMetricVM } from "../types";

interface CoverageNoticeProps {
  unsupportedMetrics: UnsupportedMetricVM[];
  completeness: ProfileCompletenessVM;
}

/* ------------------------------------------------------------------ */
/* Helpers                                                             */
/* ------------------------------------------------------------------ */

const SECTION_LABELS: { key: keyof ProfileCompletenessVM; label: string }[] = [
  { key: "demographics", label: "Demographics" },
  { key: "attendance", label: "Attendance" },
  { key: "behaviour", label: "Behaviour" },
  { key: "workforce", label: "Workforce" },
  { key: "admissions", label: "Admissions" },
  { key: "finance", label: "Finance" },
  { key: "leadership", label: "Leadership" },
  { key: "performance", label: "Performance" },
  { key: "trends", label: "Trends" },
  { key: "ofstedLatest", label: "Ofsted" },
  { key: "ofstedTimeline", label: "Ofsted history" },
  { key: "areaDeprivation", label: "Area deprivation" },
  { key: "areaCrime", label: "Area crime" },
  { key: "areaHousePrices", label: "Area house prices" }
];

function formatRefreshed(completeness: ProfileCompletenessVM): string | null {
  const dates = SECTION_LABELS
    .map(({ key }) => completeness[key].lastUpdatedAt)
    .filter((d): d is string => d !== null);

  if (dates.length === 0) return null;
  return dates.sort().reverse()[0];
}

/* ------------------------------------------------------------------ */
/* Component                                                           */
/* ------------------------------------------------------------------ */

/**
 * Unified profile footer combining data-gap summary and refresh
 * timestamp into a single subtle line. Avoids breaking the data
 * narrative with heavy banners.
 */
export function CoverageNotice({
  unsupportedMetrics,
  completeness
}: CoverageNoticeProps): JSX.Element | null {
  const incompleteNames = SECTION_LABELS
    .filter(({ key }) => completeness[key].status !== "available")
    .map(({ label }) => label);

  const latestRefresh = formatRefreshed(completeness);

  // Nothing to report at all
  if (incompleteNames.length === 0 && unsupportedMetrics.length === 0 && !latestRefresh) {
    return null;
  }

  return (
    <footer
      className="flex flex-wrap items-center gap-x-3 gap-y-1 border-t border-border-subtle/40 pt-4 text-xs text-disabled"
      role="contentinfo"
      aria-label="Profile data status"
    >
      {incompleteNames.length > 0 ? (
        <span className="inline-flex items-center gap-1.5">
          <Info className="h-3.5 w-3.5 shrink-0" aria-hidden />
          Not yet published: {incompleteNames.join(", ")}
        </span>
      ) : null}

      {latestRefresh ? (
        <span className="inline-flex items-center gap-1.5">
          <Clock className="h-3 w-3 shrink-0" aria-hidden />
          {latestRefresh}
        </span>
      ) : null}

      {unsupportedMetrics.length > 0 ? (
        <span className="inline-flex flex-wrap items-center gap-x-2 gap-y-1">
          <Info className="h-3.5 w-3.5 shrink-0" aria-hidden />
          <span>Coverage gaps:</span>
          {unsupportedMetrics.map((metric, index) => (
            <span
              key={metric.label}
              aria-label={`${metric.label} data is not available`}
            >
              {index === unsupportedMetrics.length - 1 ? metric.label : `${metric.label},`}
            </span>
          ))}
        </span>
      ) : null}
    </footer>
  );
}
