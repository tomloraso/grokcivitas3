import { cn } from "../../shared/utils/cn";

interface LoadingSkeletonProps {
  lines?: number;
  className?: string;
}

export function LoadingSkeleton({
  lines = 3,
  className
}: LoadingSkeletonProps): JSX.Element {
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
