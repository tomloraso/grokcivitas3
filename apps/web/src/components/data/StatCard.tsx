import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "../../shared/utils/cn";
import { Card } from "../ui/Card";

interface StatCardProps extends HTMLAttributes<HTMLDivElement> {
  /** Metric label — plain text or JSX (e.g. GlossaryTerm) */
  label: ReactNode;
  /** Primary display value (e.g. "32.4%") */
  value: string;
  /** Optional secondary element rendered below the value (e.g. TrendIndicator, Sparkline) */
  footer?: ReactNode;
  /** Optional icon rendered top-right */
  icon?: ReactNode;
}

export function StatCard({
  label,
  value,
  footer,
  icon,
  className,
  ...props
}: StatCardProps): JSX.Element {
  return (
    <Card
      className={cn(
        "group relative flex flex-col gap-2 overflow-hidden p-4 transition-colors duration-fast hover:border-brand/25 sm:p-5",
        className
      )}
      {...props}
    >
      {/* Header row: label + optional icon */}
      <div className="flex items-start justify-between gap-2">
        <span className="text-xs font-medium uppercase tracking-[0.08em] text-secondary" style={{ opacity: "var(--text-opacity-muted)" }}>
          {label}
        </span>
        {icon ? (
          <span className="shrink-0 text-disabled transition-colors duration-fast group-hover:text-secondary" aria-hidden>
            {icon}
          </span>
        ) : null}
      </div>

      {/* Big number */}
      <span className="font-display text-3xl font-bold leading-tight tracking-tight text-primary sm:text-4xl">
        {value}
      </span>

      {/* Optional footer (trend delta, sparkline, etc.) */}
      {footer ? <div className="mt-auto pt-1">{footer}</div> : null}
    </Card>
  );
}
