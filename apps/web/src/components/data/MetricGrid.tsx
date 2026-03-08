import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "../../shared/utils/cn";

interface MetricGridProps extends HTMLAttributes<HTMLDivElement> {
  /** Grid children (typically StatCard instances) */
  children: ReactNode;
  /** Number of columns at md+ breakpoint (default: 3). Always 1 col on mobile (or 2 if mobileTwo), 2 on sm. */
  columns?: 2 | 3 | 4;
  /** When true, uses 2 columns on narrow mobile (≥375px) instead of 1 */
  mobileTwo?: boolean;
}

const colClasses: Record<string, string> = {
  "1-2": "grid-cols-1 sm:grid-cols-2",
  "1-3": "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3",
  "1-4": "grid-cols-1 sm:grid-cols-2 lg:grid-cols-4",
  "2-2": "grid-cols-2",
  "2-3": "grid-cols-2 lg:grid-cols-3",
  "2-4": "grid-cols-2 lg:grid-cols-4",
};

export function MetricGrid({
  children,
  columns = 3,
  mobileTwo = false,
  className,
  ...props
}: MetricGridProps): JSX.Element {
  const key = `${mobileTwo ? "2" : "1"}-${columns}`;
  return (
    <div
      className={cn("grid gap-3 sm:gap-4", colClasses[key], className)}
      {...props}
    >
      {children}
    </div>
  );
}
