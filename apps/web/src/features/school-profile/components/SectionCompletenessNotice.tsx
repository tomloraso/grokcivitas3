import { AlertTriangle, CircleOff } from "lucide-react";

import { formatCompletenessReasonCopy } from "../../../shared/completeness";
import { cn } from "../../../shared/utils/cn";
import type { SectionCompletenessVM } from "../types";

interface SectionCompletenessNoticeProps {
  sectionLabel: string;
  completeness: SectionCompletenessVM;
  className?: string;
}

function resolveReasonCopy(completeness: SectionCompletenessVM): string | null {
  return formatCompletenessReasonCopy({
    reasonCode: completeness.reasonCode,
    yearsAvailable: completeness.yearsAvailable
  });
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
