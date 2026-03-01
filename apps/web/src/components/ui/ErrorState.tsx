import type { ReactNode } from "react";

import { Button } from "./Button";
import { cn } from "../../shared/utils/cn";

interface ErrorStateProps {
  title: string;
  description: string;
  onRetry?: () => void;
  action?: ReactNode;
  className?: string;
}

export function ErrorState({
  title,
  description,
  onRetry,
  action,
  className
}: ErrorStateProps): JSX.Element {
  return (
    <section
      role="alert"
      className={cn("rounded-lg border border-danger/60 bg-danger/10 p-5 text-left sm:p-6", className)}
    >
      <h2 className="text-lg font-semibold text-primary">{title}</h2>
      <p className="mt-2 text-sm text-secondary">{description}</p>
      <div className="mt-4 flex flex-wrap gap-3">
        {onRetry ? (
          <Button type="button" variant="secondary" onClick={onRetry}>
            Try again
          </Button>
        ) : null}
        {action}
      </div>
    </section>
  );
}
