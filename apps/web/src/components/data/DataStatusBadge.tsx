import type { HTMLAttributes } from "react";

import { cn } from "../../shared/utils/cn";
import { Badge } from "../ui/Badge";

/* ------------------------------------------------------------------ */
/* Status → display mapping                                            */
/* ------------------------------------------------------------------ */

type DataStatus = "available" | "partial" | "unavailable";

interface StatusConfig {
  label: string;
  variant: "success" | "warning" | "outline";
}

const STATUS_CONFIG: Record<DataStatus, StatusConfig> = {
  available: { label: "Available", variant: "success" },
  partial: { label: "Partially available", variant: "warning" },
  unavailable: { label: "Not yet published", variant: "outline" }
};

/* ------------------------------------------------------------------ */
/* Component                                                           */
/* ------------------------------------------------------------------ */

interface DataStatusBadgeProps extends Omit<HTMLAttributes<HTMLSpanElement>, "children"> {
  /** Section completeness status */
  status: DataStatus;
}

/**
 * Per-section status badge using plain-language states.
 * Replaces generic warning patterns with clear availability indicators.
 */
export function DataStatusBadge({
  status,
  className,
  ...props
}: DataStatusBadgeProps): JSX.Element {
  const config = STATUS_CONFIG[status];

  return (
    <Badge
      variant={config.variant}
      className={cn("text-xs", className)}
      aria-label={`Data status: ${config.label}`}
      {...props}
    >
      {config.label}
    </Badge>
  );
}
