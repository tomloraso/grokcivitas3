import type { ReactNode } from "react";

import { cn } from "../../shared/utils/cn";

interface AppShellProps {
  children: ReactNode;
  className?: string;
}

export function AppShell({ children, className }: AppShellProps): JSX.Element {
  return (
    <div className={cn("relative min-h-screen overflow-hidden text-primary", className)}>
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 subtle-grid-bg opacity-50"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute left-[-12%] top-[-18%] h-72 w-72 rounded-full bg-brand/25 blur-3xl"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute bottom-[-22%] right-[-10%] h-80 w-80 rounded-full bg-accent/20 blur-3xl"
      />
      <div className="relative z-nav">{children}</div>
    </div>
  );
}
