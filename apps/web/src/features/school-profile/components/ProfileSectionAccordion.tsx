import { useState, type ReactNode } from "react";

import { ChevronDown } from "lucide-react";

import { cn } from "../../../shared/utils/cn";

interface ProfileSectionAccordionProps {
  /** Section title shown in the mobile toggle button */
  title: string;
  /** Whether the accordion starts open. Defaults to false. */
  defaultOpen?: boolean;
  children: ReactNode;
}

/**
 * Mobile-only collapsible wrapper for profile page sections.
 *
 * On lg+ screens: renders children directly with no toggle (uses `lg:block`).
 * On mobile: renders a styled toggle button + collapsible content region.
 *
 * No external package dependency — uses React state + CSS transitions.
 */
export function ProfileSectionAccordion({
  title,
  defaultOpen = false,
  children,
}: ProfileSectionAccordionProps): JSX.Element {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <>
      {/* Toggle button — mobile only */}
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className={cn(
          "lg:hidden w-full flex items-center justify-between gap-3 min-h-[44px]",
          "px-3 py-2.5 text-sm font-semibold text-primary",
          "rounded-xl border border-border-subtle/60 bg-surface/70 backdrop-blur-sm",
          "transition-all duration-200 hover:border-brand/30 hover:bg-surface",
          open && "rounded-b-none border-b-transparent"
        )}
        aria-expanded={open}
      >
        <span>{title}</span>
        <ChevronDown
          className={cn(
            "h-4 w-4 shrink-0 text-secondary transition-transform duration-200",
            open && "rotate-180"
          )}
          aria-hidden
        />
      </button>

      {/* Content — always visible on desktop, conditional on mobile */}
      <div className={cn(!open ? "hidden lg:block" : "lg:block")}>
        {children}
      </div>
    </>
  );
}
