import type { ReactNode } from "react";

import { cn } from "../../shared/utils/cn";

interface SplitPaneLayoutProps {
  listPane: ReactNode;
  mapPane: ReactNode;
  className?: string;
}

export function SplitPaneLayout({
  listPane,
  mapPane,
  className
}: SplitPaneLayoutProps): JSX.Element {
  return (
    <div
      className={cn(
        "grid gap-6 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)] lg:items-start",
        className
      )}
    >
      <section aria-label="School results" className="space-y-4">
        {listPane}
      </section>
      <aside aria-label="Map view" className="space-y-4">
        {mapPane}
      </aside>
    </div>
  );
}
