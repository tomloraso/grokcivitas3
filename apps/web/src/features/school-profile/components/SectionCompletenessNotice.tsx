import { AlertTriangle, Info } from "lucide-react";

import { cn } from "../../../shared/utils/cn";
import type { SectionCompletenessVM } from "../types";

interface SectionCompletenessNoticeProps {
  sectionLabel: string;
  completeness: SectionCompletenessVM;
  className?: string;
}

const REASON_COPY: Record<NonNullable<SectionCompletenessVM["messageKey"]>, string> = {
  missing: "Some source data has not yet been published for this section.",
  notProvided: "The source publishes only part of this section for this school.",
  validationRejected: "Some source records were excluded because they did not meet quality checks.",
  notJoinedYet: "We are still linking this section to the school location.",
  pipelineFailedRecently: "This section is temporarily unavailable while data refresh catches up.",
  notApplicable: "This section does not apply to this school."
};

function statusLead(status: SectionCompletenessVM["status"]): string {
  if (status === "partial") {
    return "Some data is available now.";
  }
  return "This section is currently unavailable.";
}

export function SectionCompletenessNotice({
  sectionLabel,
  completeness,
  className
}: SectionCompletenessNoticeProps): JSX.Element | null {
  if (completeness.status === "available") {
    return null;
  }

  const Icon = completeness.status === "partial" ? AlertTriangle : Info;
  const reasonCopy = completeness.messageKey ? REASON_COPY[completeness.messageKey] : null;
  const yearsCopy =
    completeness.yearsAvailable && completeness.yearsAvailable.length > 0
      ? `${completeness.yearsAvailable.length} ${completeness.yearsAvailable.length === 1 ? "year" : "years"} currently available.`
      : null;

  return (
    <div
      className={cn(
        "space-y-1 rounded-md border border-border-subtle/80 bg-surface/60 px-3 py-2.5 text-sm text-secondary",
        className
      )}
      role="status"
      aria-label={`${sectionLabel} data is ${completeness.status}`}
    >
      <p className="inline-flex items-center gap-1.5 font-medium text-primary">
        <Icon className="h-4 w-4 text-warning" aria-hidden />
        <span>{statusLead(completeness.status)}</span>
      </p>
      {reasonCopy ? <p>{reasonCopy}</p> : null}
      {yearsCopy ? <p>{yearsCopy}</p> : null}
      {completeness.lastUpdatedAt ? <p>Last refreshed: {completeness.lastUpdatedAt}</p> : null}
    </div>
  );
}
