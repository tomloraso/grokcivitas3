import { Info } from "lucide-react";

import type { ProfileCompletenessVM } from "../types";

interface PageCompletenessBarProps {
  completeness: ProfileCompletenessVM;
}

/**
 * A single, consolidated page-level banner summarising data gaps.
 * Replaces the per-section wall-of-warnings pattern with one
 * calm notice that doesn't erode trust.
 */
export function PageCompletenessBar({
  completeness,
}: PageCompletenessBarProps): JSX.Element | null {
  const sections = [
    { label: "Demographics", ...completeness.demographics },
    { label: "Trends", ...completeness.trends },
    { label: "Ofsted", ...completeness.ofstedLatest },
    { label: "Ofsted history", ...completeness.ofstedTimeline },
    { label: "Area deprivation", ...completeness.areaDeprivation },
    { label: "Area crime", ...completeness.areaCrime },
  ];

  const incomplete = sections.filter((s) => s.status !== "available");
  if (incomplete.length === 0) return null;

  // Find the most recent refresh
  const dates = sections
    .map((s) => s.lastUpdatedAt)
    .filter((d): d is string => d !== null);
  const latestRefresh = dates.length > 0 ? dates.sort().reverse()[0] : null;

  const incompleteNames = incomplete.map((s) => s.label);

  return (
    <div
      className="flex items-start gap-2.5 rounded-lg border border-border-subtle/60 bg-surface/50 px-4 py-3 text-sm text-secondary"
      role="status"
      aria-label="Some data is incomplete"
    >
      <Info className="mt-0.5 h-4 w-4 shrink-0 text-info" aria-hidden />
      <div className="space-y-0.5">
        <p>
          Some information hasn&apos;t been published yet.{" "}
          <span className="text-disabled">
            Affected: {incompleteNames.join(", ")}.
          </span>
        </p>
        {latestRefresh ? (
          <p className="text-xs text-disabled">
            Last checked: {latestRefresh}
          </p>
        ) : null}
      </div>
    </div>
  );
}
