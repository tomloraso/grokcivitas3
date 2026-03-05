import { Info } from "lucide-react";

import type { ProfileCompletenessVM } from "../types";

interface PageCompletenessBarProps {
  completeness: ProfileCompletenessVM;
}

/**
 * Subtle page-level hint about data gaps.
 * Designed to inform without dominating the page or breaking the
 * data narrative. Renders as a muted inline line rather than a
 * bordered banner.
 */
export function PageCompletenessBar({
  completeness
}: PageCompletenessBarProps): JSX.Element | null {
  const sections = [
    { label: "Demographics", ...completeness.demographics },
    { label: "Attendance", ...completeness.attendance },
    { label: "Behaviour", ...completeness.behaviour },
    { label: "Workforce", ...completeness.workforce },
    { label: "Leadership", ...completeness.leadership },
    { label: "Performance", ...completeness.performance },
    { label: "Trends", ...completeness.trends },
    { label: "Ofsted", ...completeness.ofstedLatest },
    { label: "Ofsted history", ...completeness.ofstedTimeline },
    { label: "Area deprivation", ...completeness.areaDeprivation },
    { label: "Area crime", ...completeness.areaCrime },
    { label: "Area house prices", ...completeness.areaHousePrices }
  ];

  const incomplete = sections.filter((s) => s.status !== "available");
  if (incomplete.length === 0) {
    return null;
  }

  const dates = sections.map((s) => s.lastUpdatedAt).filter((d): d is string => d !== null);
  const latestRefresh = dates.length > 0 ? dates.sort().reverse()[0] : null;

  const incompleteNames = incomplete.map((s) => s.label);

  return (
    <p
      className="flex flex-wrap items-center gap-1.5 text-xs text-disabled"
      role="status"
      aria-label="Some data is incomplete"
    >
      <Info className="h-3.5 w-3.5 shrink-0" aria-hidden />
      <span>Not yet published: {incompleteNames.join(", ")}</span>
      {latestRefresh ? <span className="before:content-['|'] before:mr-1.5">{latestRefresh}</span> : null}
    </p>
  );
}
