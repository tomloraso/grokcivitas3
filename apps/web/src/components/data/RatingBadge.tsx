import type { HTMLAttributes } from "react";

import { cn } from "../../shared/utils/cn";
import { Badge } from "../ui/Badge";

/* ------------------------------------------------------------------ */
/* Ofsted rating → visual mapping                                      */
/* ------------------------------------------------------------------ */

interface RatingConfig {
  label: string;
  variant: "success" | "warning" | "danger" | "info" | "default" | "outline";
}

const OFSTED_RATINGS: Record<string, RatingConfig> = {
  "1": { label: "Outstanding", variant: "success" },
  "2": { label: "Good", variant: "info" },
  "3": { label: "Requires Improvement", variant: "warning" },
  "4": { label: "Inadequate", variant: "danger" }
};

const UNGRADED_FALLBACK: RatingConfig = {
  label: "Ungraded",
  variant: "outline"
};

const UNKNOWN_FALLBACK: RatingConfig = {
  label: "Not Rated",
  variant: "outline"
};

/* ------------------------------------------------------------------ */
/* Component                                                           */
/* ------------------------------------------------------------------ */

interface RatingBadgeProps extends Omit<HTMLAttributes<HTMLSpanElement>, "children"> {
  /**
   * Rating code as string (e.g. "1", "2", "3", "4").
   * Pass `null` for unknown/missing ratings.
   */
  ratingCode: string | null;
  /**
   * Optional label override (e.g. from API `overall_effectiveness_label`).
   * Falls back to the built-in label map when omitted.
   */
  label?: string | null;
  /** Whether this was an ungraded inspection */
  isUngraded?: boolean;
}

export function RatingBadge({
  ratingCode,
  label: labelOverride,
  isUngraded = false,
  className,
  ...props
}: RatingBadgeProps): JSX.Element {
  // Resolve configuration
  let config: RatingConfig;
  if (isUngraded && !ratingCode) {
    config = UNGRADED_FALLBACK;
  } else if (ratingCode && OFSTED_RATINGS[ratingCode]) {
    config = OFSTED_RATINGS[ratingCode];
  } else {
    config = UNKNOWN_FALLBACK;
  }

  const displayLabel = labelOverride ?? config.label;

  return (
    <Badge
      variant={config.variant}
      className={cn("text-xs", className)}
      aria-label={`Ofsted rating: ${displayLabel}`}
      {...props}
    >
      {displayLabel}
    </Badge>
  );
}
