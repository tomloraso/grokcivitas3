import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "../../shared/utils/cn";

interface MetricGridProps extends HTMLAttributes<HTMLDivElement> {
  /** Grid children (typically StatCard instances) */
  children: ReactNode;
  /** Number of columns at md+ breakpoint (default: 3). Always 1 col on mobile, 2 on sm. */
  columns?: 2 | 3 | 4;
}

const colClasses: Record<number, string> = {
  2: "grid-cols-1 sm:grid-cols-2",
  3: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3",
  4: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-4"
};

export function MetricGrid({
  children,
  columns = 3,
  className,
  ...props
}: MetricGridProps): JSX.Element {
  return (
    <div
      className={cn("grid gap-3 sm:gap-4", colClasses[columns], className)}
      {...props}
    >
      {children}
    </div>
  );
}
