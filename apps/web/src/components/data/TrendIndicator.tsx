import { TrendingDown, TrendingUp, Minus } from "lucide-react";
import type { HTMLAttributes } from "react";

import { cn } from "../../shared/utils/cn";

type TrendDirection = "up" | "down" | "flat";
type TrendUnit = "%" | "pp";

interface TrendIndicatorProps extends HTMLAttributes<HTMLSpanElement> {
  /** Delta value to display (e.g. +2.3, -1.5) */
  delta: number;
  /** Explicit direction override. Auto-derived from delta sign when omitted. */
  direction?: TrendDirection;
  /** Unit suffix for delta formatting (default: "%"). */
  unit?: TrendUnit;
  /** @deprecated Use `unit` instead. */
  asPercentage?: boolean;
  /** Size of the icon in pixels (default: 14) */
  iconSize?: number;
}

function resolveDirection(delta: number, explicit?: TrendDirection): TrendDirection {
  if (explicit) return explicit;
  if (delta > 0) return "up";
  if (delta < 0) return "down";
  return "flat";
}

const directionConfig: Record<
  TrendDirection,
  { icon: typeof TrendingUp; colorClass: string; label: string }
> = {
  up: { icon: TrendingUp, colorClass: "text-trend-up", label: "Trending up" },
  down: { icon: TrendingDown, colorClass: "text-trend-down", label: "Trending down" },
  flat: { icon: Minus, colorClass: "text-trend-flat", label: "No change" }
};

export function TrendIndicator({
  delta,
  direction: directionProp,
  unit = "%",
  asPercentage,
  iconSize = 14,
  className,
  ...props
}: TrendIndicatorProps): JSX.Element {
  const dir = resolveDirection(delta, directionProp);
  const { icon: Icon, colorClass, label } = directionConfig[dir];
  const prefix = delta > 0 ? "+" : "";
  const formatted =
    asPercentage === false
      ? `${prefix}${delta}`
      : `${prefix}${delta.toFixed(1)}${unit}`;

  return (
    <span
      className={cn("inline-flex items-center gap-1 text-xs font-medium", colorClass, className)}
      aria-label={`${label}: ${formatted}`}
      {...props}
    >
      <Icon size={iconSize} aria-hidden />
      <span>{formatted}</span>
    </span>
  );
}
