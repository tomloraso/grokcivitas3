import { AlertTriangle, CircleOff } from "lucide-react";

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
  insufficientYearsPublished:
    "We currently have limited published years for this school.",
  sourceNotInCatalog:
    "This source is not currently in our approved school-data catalog.",
  sourceFileMissingForYear:
    "A published file for this year is not yet available for this school.",
  sourceSchemaIncompatibleForYear:
    "This year's published file couldn't be used because the format changed.",
  partialMetricCoverage:
    "Some measures are available, but other parts of this section are still missing.",
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

function resolveReasonCopy(completeness: SectionCompletenessVM): string | null {
  if (completeness.messageKey === null) {
    return null;
  }

  if (completeness.messageKey === "insufficientYearsPublished") {
    const publishedYears = completeness.yearsAvailable?.length ?? 0;
    if (publishedYears === 1) {
      return "We currently have one published year for this school.";
    }
    if (publishedYears > 1) {
      return `We currently have ${publishedYears} published years for this school.`;
    }
  }

  return REASON_COPY[completeness.messageKey];
}

export function SectionCompletenessNotice({
  sectionLabel,
  completeness,
  className
}: SectionCompletenessNoticeProps): JSX.Element | null {
  if (completeness.status === "available") {
    return null;
  }

  const reasonCopy = resolveReasonCopy(completeness);

  // Partial: lightweight inline indicator
  if (completeness.status === "partial") {
    return (
      <div
        className={cn(
          "flex items-center gap-1.5 text-xs text-disabled",
          className
        )}
        role="status"
        aria-label={`${sectionLabel} data is partially available`}
      >
        <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-warning" aria-hidden />
        <span>{reasonCopy ?? "Some data may be incomplete."}</span>
      </div>
    );
  }

  // Unavailable: same lightweight inline style
  return (
    <div
      className={cn(
        "flex items-center gap-1.5 text-xs text-disabled",
        className
      )}
      role="status"
      aria-label={`${sectionLabel} data is ${completeness.status}`}
    >
      <CircleOff className="h-3.5 w-3.5 shrink-0" aria-hidden />
      <span>{reasonCopy ?? "This section is not yet available."}</span>
    </div>
  );
}
