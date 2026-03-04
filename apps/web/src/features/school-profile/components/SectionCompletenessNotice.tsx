import { AlertTriangle, Info } from "lucide-react";

import { DataStatusBadge } from "../../../components/data/DataStatusBadge";
import { cn } from "../../../shared/utils/cn";
import type { SectionCompletenessVM } from "../types";

interface SectionCompletenessNoticeProps {
  sectionLabel: string;
  completeness: SectionCompletenessVM;
  className?: string;
}

/**
 * Parent-friendly copy for completeness reason codes.
 * Technical detail is intentionally removed; if a "Learn more"
 * link is needed later it can be added per-reason.
 */
const REASON_COPY: Record<NonNullable<SectionCompletenessVM["messageKey"]>, string> = {
  missing:
    "This information hasn't been published by the data source yet.",
  notProvided:
    "The data source only records some of this information for this school.",
  validationRejected:
    "Some information was excluded because it didn't pass our quality checks.",
  notJoinedYet:
    "We're still connecting this information to the school's location.",
  pipelineFailedRecently:
    "This information is temporarily unavailable while we update our records.",
  notApplicable:
    "This section doesn't apply to this type of school.",
  sourceCoverageGap:
    "The source currently has limited coverage for this information.",
  staleAfterSchoolRefresh:
    "This section will refresh after the next local-area data update.",
  noIncidentsInRadius:
    "No incidents were recorded in this area for the latest reporting window."
};

export function SectionCompletenessNotice({
  sectionLabel,
  completeness,
  className
}: SectionCompletenessNoticeProps): JSX.Element | null {
  if (completeness.status === "available") {
    return null;
  }

  const reasonCopy = completeness.messageKey ? REASON_COPY[completeness.messageKey] : null;

  // Partial: lightweight inline indicator (icon + badge)
  if (completeness.status === "partial") {
    return (
      <div
        className={cn(
          "flex items-center gap-2 text-xs text-secondary",
          className
        )}
        role="status"
        aria-label={`${sectionLabel} data is partially available`}
      >
        <AlertTriangle className="h-3.5 w-3.5 text-warning" aria-hidden />
        <span>{reasonCopy ?? "Some data may be incomplete."}</span>
        <DataStatusBadge status={completeness.status} />
      </div>
    );
  }

  // Unavailable: full notice block
  return (
    <div
      className={cn(
        "space-y-1 rounded-md border border-border-subtle/80 bg-surface/60 px-3 py-2.5 text-sm text-secondary",
        className
      )}
      role="status"
      aria-label={`${sectionLabel} data is ${completeness.status}`}
    >
      <div className="flex items-center justify-between gap-2">
        <p className="inline-flex items-center gap-1.5 font-medium text-primary">
          <Info className="h-4 w-4 text-info" aria-hidden />
          <span>This section is currently unavailable.</span>
        </p>
        <DataStatusBadge status={completeness.status} />
      </div>
      {reasonCopy ? <p>{reasonCopy}</p> : null}
      {completeness.lastUpdatedAt ? (
        <p className="text-xs text-disabled">Last refreshed: {completeness.lastUpdatedAt}</p>
      ) : null}
    </div>
  );
}
