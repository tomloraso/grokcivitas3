import type { HTMLAttributes } from "react";

import { cn } from "../../shared/utils/cn";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>): JSX.Element {
  return (
    <div
      className={cn(
        "panel-surface rounded-xl p-4 sm:p-5",
        "transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg",
        className
      )}
      {...props}
    />
  );
}

export function Panel({ className, ...props }: HTMLAttributes<HTMLDivElement>): JSX.Element {
  return (
    <Card
      className={cn("rounded-2xl border-border-subtle bg-surface/85 sm:p-6", className)}
      {...props}
    />
  );
}
