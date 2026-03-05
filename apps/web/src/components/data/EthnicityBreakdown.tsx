import { useState } from "react";

import { cn } from "../../shared/utils/cn";

/* ------------------------------------------------------------------ */
/* Types                                                               */
/* ------------------------------------------------------------------ */

export interface EthnicityGroup {
  key: string;
  label: string;
  percentage: number | null;
  count: number | null;
  percentageLabel: string | null;
}

interface EthnicityBreakdownProps {
  groups: EthnicityGroup[];
  /** How many rows to show before the "Show more" toggle. Default: 8 */
  initialVisibleCount?: number;
}

/* ------------------------------------------------------------------ */
/* Palette – 12 distinct hues that read well on dark surfaces          */
/* ------------------------------------------------------------------ */

const SEGMENT_COLORS = [
  "#A855F7", // purple (brand)
  "#22d3ee", // cyan (accent)
  "#3b82f6", // blue
  "#f59e0b", // amber
  "#22c55e", // green
  "#ec4899", // pink
  "#f97316", // orange
  "#06b6d4", // teal
  "#8b5cf6", // violet
  "#14b8a6", // emerald
  "#e879f9", // fuchsia
  "#facc15", // yellow
];

function segmentColor(index: number): string {
  return SEGMENT_COLORS[index % SEGMENT_COLORS.length];
}

/* ------------------------------------------------------------------ */
/* Helpers                                                             */
/* ------------------------------------------------------------------ */

function sortedGroups(groups: EthnicityGroup[]) {
  return [...groups]
    .filter((g) => g.percentage !== null)
    .sort((a, b) => (b.percentage ?? 0) - (a.percentage ?? 0));
}

/* ------------------------------------------------------------------ */
/* Sub-components                                                      */
/* ------------------------------------------------------------------ */

function StackedBar({
  groups,
  hoveredKey,
  onHover,
}: {
  groups: EthnicityGroup[];
  hoveredKey: string | null;
  onHover: (key: string | null) => void;
}) {
  return (
    <div
      className="flex h-3 w-full overflow-hidden rounded-full"
      role="img"
      aria-label="Ethnicity proportions bar"
    >
      {groups.map((group, i) => {
        const pct = group.percentage ?? 0;
        if (pct === 0) return null;
        const isHovered = hoveredKey === group.key;
        const isFaded = hoveredKey !== null && !isHovered;

        return (
          <div
            key={group.key}
            className="transition-opacity duration-fast"
            style={{
              width: `${pct}%`,
              minWidth: pct > 0 ? 2 : 0,
              backgroundColor: segmentColor(i),
              opacity: isFaded ? 0.3 : 1,
              borderRight:
                i < groups.length - 1
                  ? "1px solid var(--color-bg-surface)"
                  : undefined,
            }}
            onMouseEnter={() => onHover(group.key)}
            onMouseLeave={() => onHover(null)}
          />
        );
      })}
    </div>
  );
}

function LegendRow({
  group,
  colorIndex,
  isHovered,
  onHover,
}: {
  group: EthnicityGroup;
  colorIndex: number;
  isHovered: boolean;
  onHover: (key: string | null) => void;
}) {
  const countLabel =
    group.count !== null ? `(${group.count})` : "";

  return (
    <div
      className={cn(
        "flex items-center gap-2 rounded px-2 py-1 text-sm transition-colors duration-fast",
        isHovered && "bg-surface/50"
      )}
      onMouseEnter={() => onHover(group.key)}
      onMouseLeave={() => onHover(null)}
    >
      <span
        className="inline-block h-2.5 w-2.5 shrink-0 rounded-full"
        style={{ backgroundColor: segmentColor(colorIndex) }}
        aria-hidden
      />
      <span
        className="truncate text-secondary"
        style={{ opacity: "var(--text-opacity-muted)" }}
      >
        {group.label}
      </span>
      <span className="ml-auto shrink-0 tabular-nums font-medium text-primary">
        {group.percentageLabel ?? "—"}
      </span>
      {countLabel ? (
        <span
          className="shrink-0 tabular-nums text-xs text-secondary"
          style={{ opacity: "var(--text-opacity-subtle)" }}
        >
          {countLabel}
        </span>
      ) : null}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Main component                                                      */
/* ------------------------------------------------------------------ */

export function EthnicityBreakdown({
  groups,
  initialVisibleCount = 8,
}: EthnicityBreakdownProps): JSX.Element | null {
  const sorted = sortedGroups(groups);
  const [expanded, setExpanded] = useState(false);
  const [hoveredKey, setHoveredKey] = useState<string | null>(null);

  if (sorted.length === 0) return null;

  const needsCollapse = sorted.length > initialVisibleCount;
  const visibleRows = expanded ? sorted : sorted.slice(0, initialVisibleCount);
  const hiddenCount = sorted.length - initialVisibleCount;

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-primary">
        Ethnicity breakdown
      </h3>

      {/* Stacked proportion bar */}
      <StackedBar
        groups={sorted}
        hoveredKey={hoveredKey}
        onHover={setHoveredKey}
      />

      {/* Sorted compact legend */}
      <div className="grid grid-cols-1 gap-0.5 sm:grid-cols-2">
        {visibleRows.map((group) => {
          const colorIndex = sorted.indexOf(group);
          return (
            <LegendRow
              key={group.key}
              group={group}
              colorIndex={colorIndex}
              isHovered={hoveredKey === group.key}
              onHover={setHoveredKey}
            />
          );
        })}
      </div>

      {/* Show more / less toggle */}
      {needsCollapse ? (
        <button
          type="button"
          onClick={() => setExpanded((prev) => !prev)}
          className="text-xs font-medium text-brand transition-colors duration-fast hover:text-brand-hover"
        >
          {expanded
            ? "Show less"
            : `Show ${hiddenCount} more group${hiddenCount === 1 ? "" : "s"}`}
        </button>
      ) : null}
    </div>
  );
}
