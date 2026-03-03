import { cn } from "../../shared/utils/cn";

interface LoadingSkeletonProps {
  /** Number of skeleton lines for the "lines" variant */
  lines?: number;
  /** "lines" shows generic bars; "result-card" mimics ResultCard geometry */
  variant?: "lines" | "result-card";
  /** Number of skeleton cards for the "result-card" variant */
  count?: number;
  className?: string;
}

function ResultCardSkeleton(): JSX.Element {
  return (
    <div className="space-y-3 rounded-lg border border-border-subtle bg-surface/70 p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="h-5 w-3/4 animate-pulse rounded bg-white/10" />
        <div className="h-6 w-16 animate-pulse rounded-full bg-white/10" />
      </div>
      <div className="flex items-center gap-3">
        <div className="h-3.5 w-24 animate-pulse rounded bg-white/10" />
        <div className="h-3.5 w-16 animate-pulse rounded bg-white/10" />
        <div className="h-3.5 w-20 animate-pulse rounded bg-white/10" />
      </div>
    </div>
  );
}

export function LoadingSkeleton({
  lines = 3,
  variant = "lines",
  count = 3,
  className
}: LoadingSkeletonProps): JSX.Element {
  if (variant === "result-card") {
    return (
      <div
        role="status"
        aria-live="polite"
        aria-label="Loading results"
        className={cn("space-y-3", className)}
      >
        {Array.from({ length: count }, (_, i) => (
          <ResultCardSkeleton key={`skeleton-card-${i}`} />
        ))}
      </div>
    );
  }

  return (
    <div
      role="status"
      aria-live="polite"
      aria-label="Loading content"
      className={cn("space-y-3 rounded-lg border border-border-subtle bg-surface/70 p-4", className)}
    >
      {Array.from({ length: lines }, (_, index) => (
        <div
          key={`skeleton-line-${index}`}
          className={cn(
            "h-4 animate-pulse rounded bg-white/10",
            index === 0 ? "w-11/12" : index === lines - 1 ? "w-7/12" : "w-full"
          )}
        />
      ))}
    </div>
  );
}
