import type { HTMLAttributes } from "react";

import { cn } from "../../shared/utils/cn";

type TrendDirection = "up" | "down" | "flat";
type TrendUnit = "%" | "pp";

interface TrendIndicatorProps extends HTMLAttributes<HTMLSpanElement> {
  /** Delta value to display (absolute value rendered; triangle conveys direction). */
  delta: number;
  /** Explicit direction override. Auto-derived from delta sign when omitted. */
  direction?: TrendDirection;
  /** Unit suffix for delta formatting (default: "%"). */
  unit?: TrendUnit;
  /** @deprecated Use `unit` instead. */
  asPercentage?: boolean;
  /**
   * Period label rendered on its own line below the delta value.
   * Use short form: "3-yr trend", "6-yr trend".
   */
  period?: string;
}

const TRIANGLE: Record<TrendDirection, string> = {
  up: "▲",
  down: "▼",
  flat: "—",
};

function resolveDirection(delta: number, explicit?: TrendDirection): TrendDirection {
  if (explicit) return explicit;
  if (delta > 0) return "up";
  if (delta < 0) return "down";
  return "flat";
}

export function TrendIndicator({
  delta,
  direction: directionProp,
  unit = "%",
  asPercentage,
  period,
  className,
  ...props
}: TrendIndicatorProps): JSX.Element {
  const dir = resolveDirection(delta, directionProp);
  const triangle = TRIANGLE[dir];

  // Always show absolute value — triangle conveys direction
  const absDelta = Math.abs(delta);
  const formatted =
    asPercentage === false
      ? `${absDelta}`
      : `${absDelta.toFixed(1)}${unit}`;

  const ariaLabel =
    dir === "flat"
      ? `No change: ${formatted}${period ? `, ${period}` : ""}`
      : `${dir === "up" ? "Up" : "Down"}: ${formatted}${period ? `, ${period}` : ""}`;

  return (
    <span
      className={cn(
        "inline-flex flex-col text-xs font-medium",
        dir === "flat" ? "text-disabled" : "text-brand",
        className
      )}
      aria-label={ariaLabel}
      {...props}
    >
      {/* Triangle + value on one line */}
      <span className="inline-flex items-center gap-0.5 whitespace-nowrap">
        <span aria-hidden>{triangle}</span>
        <span>{formatted}</span>
      </span>
      {/* Period on its own line in muted colour */}
      {period ? (
        <span className="text-[10px] text-disabled">{period}</span>
      ) : null}
    </span>
  );
}
