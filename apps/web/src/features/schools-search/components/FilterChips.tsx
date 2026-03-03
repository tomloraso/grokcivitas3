import { X } from "lucide-react";

import { phaseColor } from "../../../shared/maps/map-tokens";
import { cn } from "../../../shared/utils/cn";
import type { Facet } from "../hooks/useResultFilters";

interface FilterChipProps {
  facet: Facet;
  onToggle: (label: string) => void;
}

function FilterChip({ facet, onToggle }: FilterChipProps): JSX.Element {
  const dotColor = phaseColor(facet.label);

  return (
    <button
      type="button"
      role="option"
      aria-selected={facet.selected}
      onClick={() => onToggle(facet.label)}
      className={cn(
        "inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border px-2.5 py-1 text-xs font-medium transition-all duration-fast",
        facet.selected
          ? "border-brand/50 bg-brand/15 text-primary"
          : "border-border-subtle/60 bg-white/[0.04] text-secondary hover:border-border-default hover:bg-white/[0.08] hover:text-primary"
      )}
    >
      <span
        className="inline-block h-2 w-2 shrink-0 rounded-full"
        style={{ backgroundColor: dotColor }}
        aria-hidden
      />
      <span>{facet.label}</span>
      <span
        className={cn(
          "tabular-nums",
          facet.selected ? "text-brand-hover" : "text-disabled"
        )}
      >
        {facet.count}
      </span>
    </button>
  );
}

interface FilterChipsProps {
  phases: Facet[];
  hasActiveFilters: boolean;
  hiddenCount: number;
  onTogglePhase: (label: string) => void;
  onClear: () => void;
}

/**
 * Phase chip strip rendered between search form and results.
 * Only visible when results contain more than one phase.
 */
export function FilterChips({
  phases,
  hasActiveFilters,
  hiddenCount,
  onTogglePhase,
  onClear,
}: FilterChipsProps): JSX.Element | null {
  // Don't render when there's nothing to filter
  if (phases.length <= 1) return null;

  return (
    <div
      className="space-y-2 px-4 pb-2 sm:px-5"
      role="group"
      aria-label="Filter results"
    >
      <div className="flex flex-wrap items-center gap-1.5" role="listbox" aria-label="Filter by phase">
        {phases.map((f) => (
          <FilterChip key={f.label} facet={f} onToggle={onTogglePhase} />
        ))}

        {hasActiveFilters && (
          <button
            type="button"
            onClick={onClear}
            className="ml-1 inline-flex items-center gap-1 rounded-full px-2 py-1 text-[10px] font-medium text-secondary transition-colors duration-fast hover:bg-white/[0.08] hover:text-primary"
          >
            <X className="h-3 w-3" aria-hidden />
            Clear
          </button>
        )}
      </div>

      {hasActiveFilters && (
        <p className="text-[10px] text-secondary">
          {hiddenCount} {hiddenCount === 1 ? "school" : "schools"} hidden
        </p>
      )}
    </div>
  );
}
