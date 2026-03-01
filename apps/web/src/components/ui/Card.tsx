import type { HTMLAttributes } from "react";

import { cn } from "../../shared/utils/cn";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>): JSX.Element {
  return <div className={cn("panel-surface rounded-lg p-4 sm:p-5", className)} {...props} />;
}

export function Panel({ className, ...props }: HTMLAttributes<HTMLDivElement>): JSX.Element {
  return (
    <Card
      className={cn("rounded-xl border-border-subtle bg-surface/85 sm:p-6", className)}
      {...props}
    />
  );
}
