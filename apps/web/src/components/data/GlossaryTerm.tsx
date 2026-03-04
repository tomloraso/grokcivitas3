import { HelpCircle } from "lucide-react";
import type { ReactNode } from "react";

import { getGlossaryEntry } from "../../shared/glossary";
import { cn } from "../../shared/utils/cn";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger
} from "../ui/Tooltip";

/* ------------------------------------------------------------------ */
/* Component                                                           */
/* ------------------------------------------------------------------ */

interface GlossaryTermProps {
  /** Key into the shared glossary (e.g. "ehcp", "idaci") */
  term: string;
  /** Display text override. Defaults to the glossary short name. */
  children?: ReactNode;
  /** Additional classes on the trigger wrapper */
  className?: string;
}

/**
 * Renders a term with a dotted underline and a tooltip showing
 * the full name and plain-language explanation. Falls back to
 * rendering children as-is when the term is not in the glossary.
 */
export function GlossaryTerm({
  term,
  children,
  className
}: GlossaryTermProps): JSX.Element {
  const entry = getGlossaryEntry(term);

  // Unknown term — render children without tooltip
  if (!entry) {
    return <span className={className}>{children ?? term}</span>;
  }

  const display = children ?? entry.short;

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span
          className={cn(
            "inline-flex cursor-help items-center gap-0.5 border-b border-dotted border-secondary/40",
            className
          )}
        >
          {display}
          <HelpCircle className="inline-block h-3 w-3 shrink-0 text-disabled" aria-hidden />
        </span>
      </TooltipTrigger>
      <TooltipContent className="max-w-xs space-y-1">
        <p className="font-medium">{entry.full}</p>
        <p className="text-secondary">{entry.description}</p>
      </TooltipContent>
    </Tooltip>
  );
}
