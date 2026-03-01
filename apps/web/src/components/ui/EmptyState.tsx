import type { ReactNode } from "react";

import { cn } from "../../shared/utils/cn";

interface EmptyStateProps {
  title: string;
  description: string;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({
  title,
  description,
  action,
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
      <h2 className="text-lg font-semibold text-primary">{title}</h2>
      <p className="mt-2 text-sm text-secondary">{description}</p>
      {action ? <div className="mt-4 flex justify-center">{action}</div> : null}
    </section>
  );
}
