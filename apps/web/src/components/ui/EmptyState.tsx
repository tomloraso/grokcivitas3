import type { ReactNode } from "react";

import { cn } from "../../shared/utils/cn";

interface EmptyStateProps {
  title: string;
  description: string;
  action?: ReactNode;
  /** Optional icon displayed above the title */
  icon?: ReactNode;
  className?: string;
}

export function EmptyState({
  title,
  description,
  action,
  icon,
  className
}: EmptyStateProps): JSX.Element {
  return (
    <section
      aria-live="polite"
      className={cn(
        "rounded-lg border border-dashed border-border bg-surface/75 p-5 text-center sm:p-6",
        className
      )}
    >
      {icon ? <div className="mx-auto mb-3 w-fit text-disabled">{icon}</div> : null}
      <h2 className="text-lg font-semibold text-primary">{title}</h2>
      <p className="mt-2 text-sm text-secondary">{description}</p>
      {action ? <div className="mt-4 flex justify-center">{action}</div> : null}
    </section>
  );
}
