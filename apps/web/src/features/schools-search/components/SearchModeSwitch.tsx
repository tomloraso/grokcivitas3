import { ListFilter, Map } from "lucide-react";

import { cn } from "../../../shared/utils/cn";
import type { SearchViewMode } from "../../../shared/search/searchState";

interface SearchModeSwitchProps {
  activeView: SearchViewMode;
  resultsEnabled: boolean;
  onMapSelect: () => void;
  onResultsSelect: () => void;
  className?: string;
}

function ModeButton({
  active,
  disabled,
  icon,
  label,
  onClick,
}: {
  active: boolean;
  disabled?: boolean;
  icon: JSX.Element;
  label: string;
  onClick: () => void;
}): JSX.Element {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-pressed={active}
      className={cn(
        "inline-flex items-center gap-2 rounded-full px-3 py-2 text-xs font-semibold transition-colors duration-fast",
        active
          ? "bg-brand-solid text-primary shadow-sm"
          : "text-secondary hover:bg-elevated hover:text-primary",
      )}
    >
      {icon}
      <span>{label}</span>
    </button>
  );
}

export function SearchModeSwitch({
  activeView,
  resultsEnabled,
  onMapSelect,
  onResultsSelect,
  className,
}: SearchModeSwitchProps): JSX.Element {
  return (
    <div
      role="group"
      aria-label="Search exploration mode"
      className={cn(
        "inline-flex items-center rounded-full border border-border-subtle/70 bg-surface/80 p-1 backdrop-blur-sm",
        className,
      )}
    >
      <ModeButton
        active={activeView === "map"}
        icon={<Map className="h-3.5 w-3.5" aria-hidden />}
        label="Map"
        onClick={onMapSelect}
      />
      <ModeButton
        active={activeView === "results"}
        disabled={!resultsEnabled}
        icon={<ListFilter className="h-3.5 w-3.5" aria-hidden />}
        label="Results"
        onClick={onResultsSelect}
      />
    </div>
  );
}
