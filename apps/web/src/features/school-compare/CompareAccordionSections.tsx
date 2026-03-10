import { useState } from "react";
import { ChevronDown } from "lucide-react";

import { cn } from "../../shared/utils/cn";
import type { CompareSlot } from "./compareSlots";
import type { CompareSectionVM } from "./types";
import { CompareAccordionContent } from "./CompareAccordionContent";

/** First N sections default open */
const DEFAULT_OPEN_COUNT = 3;

interface CompareAccordionSectionsProps {
  slots: CompareSlot[];
  sections: CompareSectionVM[];
  /** URN of the origin school (first in URL) to highlight its column */
  originUrn?: string | null;
}

export function CompareAccordionSections({
  slots,
  sections,
  originUrn,
}: CompareAccordionSectionsProps): JSX.Element {
  const [openKeys, setOpenKeys] = useState<Set<string>>(
    () => new Set(sections.slice(0, DEFAULT_OPEN_COUNT).map((s) => s.key))
  );

  function toggle(key: string): void {
    setOpenKeys((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }

  return (
    <div className="space-y-3" role="region" aria-label="Comparison sections">
      {sections.map((section) => {
        const isOpen = openKeys.has(section.key);
        return (
          <div key={section.key}>
            <button
              type="button"
              onClick={() => toggle(section.key)}
              className={cn(
                "w-full flex items-center justify-between gap-3 min-h-[48px]",
                "border-l-2 border-l-brand px-5 py-3.5 text-base font-semibold text-primary",
                "rounded-xl border border-border-subtle/60 bg-[#0b2433] backdrop-blur-sm",
                "transition-all duration-200 hover:border-l-brand hover:border-brand/30 hover:bg-surface",
                isOpen && "rounded-b-none border-b-transparent"
              )}
              aria-expanded={isOpen}
            >
              <div className="flex items-center gap-2.5">
                <span>{section.label}</span>
                <span className="text-[10px] font-normal text-disabled tabular-nums">
                  {section.rows.length} metric{section.rows.length === 1 ? "" : "s"}
                </span>
              </div>
              <ChevronDown
                className={cn(
                  "h-4 w-4 shrink-0 text-secondary transition-transform duration-200",
                  isOpen && "rotate-180"
                )}
                aria-hidden
              />
            </button>

            {isOpen ? (
              <div
                className={cn(
                  "rounded-b-xl border border-t-0 border-border-subtle/60",
                  "bg-surface/40 backdrop-blur-sm p-1"
                )}
              >
                <CompareAccordionContent
                  slots={slots}
                  rows={section.rows}
                  originUrn={originUrn}
                />
              </div>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
