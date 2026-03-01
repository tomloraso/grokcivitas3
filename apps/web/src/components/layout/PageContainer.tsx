import type { ReactNode } from "react";

import { cn } from "../../shared/utils/cn";

interface PageContainerProps {
  children: ReactNode;
  className?: string;
}

export function PageContainer({ children, className }: PageContainerProps): JSX.Element {
  return (
    <div
      className={cn(
        "mx-auto w-full max-w-[1200px] px-4 pb-12 pt-8 sm:px-6 sm:pt-10 lg:px-8 lg:pt-12",
        className
      )}
    >
      {children}
    </div>
  );
}
