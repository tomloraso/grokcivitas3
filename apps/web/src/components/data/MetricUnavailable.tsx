import { CircleOff } from "lucide-react";
import type { HTMLAttributes } from "react";

import { cn } from "../../shared/utils/cn";

interface MetricUnavailableProps extends HTMLAttributes<HTMLDivElement> {
  /** Metric name for the "not available" context (e.g. "Ethnicity breakdown") */
  metricLabel?: string;
}

export function MetricUnavailable({
  metricLabel,
  className,
  ...props
}: MetricUnavailableProps): JSX.Element {
  const message = metricLabel
    ? `${metricLabel} data is not available`
    : "Data not available";

  return (
    <div
      className={cn(
        "flex items-center gap-2 rounded-lg border border-dashed border-border bg-surface/50 px-4 py-3 text-sm text-disabled",
        className
      )}
      role="status"
      aria-label={message}
      {...props}
    >
      <CircleOff className="h-4 w-4 shrink-0" aria-hidden />
      <span>{message}</span>
    </div>
  );
}
