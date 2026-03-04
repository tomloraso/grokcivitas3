import { HelpCircle, X } from "lucide-react";
import type { ReactNode } from "react";

import { getGlossaryEntry } from "../../shared/glossary";
import { useIsTouch } from "../../shared/hooks/useIsTouch";
import { cn } from "../../shared/utils/cn";
import {
  Popover,
  PopoverClose,
  PopoverContent,
  PopoverTrigger
} from "../ui/Popover";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger
} from "../ui/Tooltip";

/* ------------------------------------------------------------------ */
/* Shared pieces                                                       */
/* ------------------------------------------------------------------ */

interface GlossaryTermProps {
  /** Key into the shared glossary (e.g. "ehcp", "idaci") */
  term: string;
  /** Display text override. Defaults to the glossary short name. */
  children?: ReactNode;
  /** Additional classes on the trigger wrapper */
  className?: string;
}

const triggerClasses =
  "inline-flex cursor-help items-center gap-0.5 border-b border-dotted border-secondary/40 transition-colors hover:border-info/60";

/* ------------------------------------------------------------------ */
/* Tooltip variant (pointer / desktop)                                 */
/* ------------------------------------------------------------------ */

function GlossaryTooltip({
  entry,
  display,
  className
}: {
  entry: { full: string; description: string };
  display: ReactNode;
  className?: string;
}): JSX.Element {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span className={cn(triggerClasses, "group/glossary", className)}>
          {display}
          <HelpCircle className="inline-block h-3.5 w-3.5 shrink-0 text-secondary transition-colors group-hover/glossary:text-info" aria-hidden />
        </span>
      </TooltipTrigger>
      <TooltipContent className="max-w-xs space-y-1">
        <p className="font-medium">{entry.full}</p>
        <p className="text-secondary">{entry.description}</p>
      </TooltipContent>
    </Tooltip>
  );
}

/* ------------------------------------------------------------------ */
/* Popover variant (touch devices)                                     */
/* ------------------------------------------------------------------ */

function GlossaryPopover({
  entry,
  display,
  className
}: {
  entry: { full: string; description: string };
  display: ReactNode;
  className?: string;
}): JSX.Element {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          type="button"
          className={cn(triggerClasses, "group/glossary", className)}
          aria-label="Show definition"
        >
          {display}
          <HelpCircle className="inline-block h-3.5 w-3.5 shrink-0 text-secondary transition-colors group-hover/glossary:text-info" aria-hidden />
        </button>
      </PopoverTrigger>

      <PopoverContent side="top" className="space-y-1">
        <div className="flex items-start justify-between gap-2">
          <p className="font-medium">{entry.full}</p>
          <PopoverClose
            aria-label="Close"
            className="shrink-0 rounded p-0.5 text-secondary hover:text-primary"
          >
            <X className="h-3 w-3" />
          </PopoverClose>
        </div>
        <p className="text-secondary">{entry.description}</p>
      </PopoverContent>
    </Popover>
  );
}

/* ------------------------------------------------------------------ */
/* Public component                                                    */
/* ------------------------------------------------------------------ */

/**
 * Renders a term with a dotted underline and an explanation.
 *
 * - **Pointer devices (desktop)**: hover tooltip (Radix Tooltip)
 * - **Touch devices (mobile)**: tap-to-open popover with close button (Radix Popover)
 *
 * Falls back to rendering children as-is when the term is not in the glossary.
 */
export function GlossaryTerm({
  term,
  children,
  className
}: GlossaryTermProps): JSX.Element {
  const entry = getGlossaryEntry(term);
  const isTouch = useIsTouch();

  // Unknown term — render children without tooltip
  if (!entry) {
    return <span className={className}>{children ?? term}</span>;
  }

  const display = children ?? entry.short;

  if (isTouch) {
    return <GlossaryPopover entry={entry} display={display} className={className} />;
  }

  return <GlossaryTooltip entry={entry} display={display} className={className} />;
}
