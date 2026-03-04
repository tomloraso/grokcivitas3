import type { HTMLAttributes } from "react";

import { cn } from "../../shared/utils/cn";

interface ProportionBarProps extends HTMLAttributes<HTMLDivElement> {
  /** Percentage value (0-100) used to fill the bar. */
  value: number;
}

function clampPercentage(value: number): number {
  if (Number.isNaN(value)) {
    return 0;
  }
  return Math.max(0, Math.min(100, value));
}

export function ProportionBar({
  value,
  className,
  ...props
}: ProportionBarProps): JSX.Element {
  const clamped = clampPercentage(value);

  return (
    <div
      {...props}
      role="meter"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={clamped}
      className={cn(
        "h-2 w-full overflow-hidden rounded-full bg-surface/75",
        className
      )}
    >
      <div
        className="h-full rounded-full bg-brand-solid transition-[width] duration-fast"
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}
