import type { ReactNode } from "react";
import { SearchX } from "lucide-react";

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

/* ------------------------------------------------------------------ */
/* Map-context-aware empty state (UX-7)                                */
/* ------------------------------------------------------------------ */

interface MapEmptyStateProps {
  /** Postcode used for the search */
  postcode?: string;
  /** Radius in miles used for the search */
  radiusMiles?: number;
  /** Custom action slot */
  action?: ReactNode;
  className?: string;
}

/**
 * Search-results empty state that includes spatial search context.
 * Provides actionable guidance to widen radius or try a nearby postcode.
 */
export function MapEmptyState({
  postcode,
  radiusMiles,
  action,
  className,
}: MapEmptyStateProps): JSX.Element {
  const description = postcode && radiusMiles
    ? `No schools found within ${radiusMiles} miles of ${postcode}. Try widening your search radius or entering a nearby postcode.`
    : "No schools matched your search area. Try widening the radius or searching a different postcode.";

  return (
    <EmptyState
      icon={<SearchX className="h-8 w-8" />}
      title="No schools found"
      description={description}
      action={action}
      className={className}
    />
  );
}
