import { cn } from "../../shared/utils/cn";
import type { CompareSlot } from "./compareSlots";
import type { CompareCellVM, CompareRowVM } from "./types";

interface CompareMobileContentProps {
  slots: CompareSlot[];
  rows: CompareRowVM[];
  originUrn?: string | null;
}

/**
 * Mobile-only (<sm) vertical card layout for compare accordion content.
 * Each metric row renders as: metric label header → stacked school value cards.
 */
export function CompareMobileContent({
  slots,
  rows,
  originUrn,
}: CompareMobileContentProps): JSX.Element {
  const filledSlots = slots.filter(Boolean) as Exclude<CompareSlot, null>[];

  return (
    <div className="space-y-4 px-2 py-3">
      {rows.map((row) => (
        <div key={row.metricKey} className="space-y-2">
          {/* Metric label header */}
          <div className="border-l-2 border-l-brand/60 pl-3 py-1">
            <p className="text-sm font-semibold text-primary">{row.label}</p>
            {unitLabel(row.unit) ? (
              <p className="text-[10px] tracking-[0.04em] text-disabled">
                {unitLabel(row.unit)}
              </p>
            ) : null}
          </div>

          {/* School value cards — stacked vertically */}
          <div className="space-y-1.5">
            {filledSlots.map((slot) => {
              const cell = row.cells.find((c) => c.urn === slot.urn);
              const isOrigin = originUrn === slot.urn;
              return (
                <MobileValueCard
                  key={`${row.metricKey}-${slot.urn}`}
                  schoolName={slot.name}
                  cell={cell ?? null}
                  isOrigin={isOrigin}
                />
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Mobile value card                                                    */
/* ------------------------------------------------------------------ */

function MobileValueCard({
  schoolName,
  cell,
  isOrigin,
}: {
  schoolName: string;
  cell: CompareCellVM | null;
  isOrigin: boolean;
}): JSX.Element {
  return (
    <div
      className={cn(
        "flex items-baseline justify-between gap-3 rounded-lg px-3 py-2.5",
        "border border-border-subtle/40 bg-surface/60",
        isOrigin && "border-l-2 border-l-brand/30 bg-brand/[0.02]"
      )}
    >
      <p className="min-w-0 truncate text-xs text-secondary">{schoolName}</p>
      <div className="shrink-0 text-right">
        {cell ? (
          <MobileCellValue cell={cell} />
        ) : (
          <p className="text-sm text-disabled/40">&mdash;</p>
        )}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Mobile cell value                                                    */
/* ------------------------------------------------------------------ */

const MAX_MOBILE_LIST_ITEMS = 2;

function MobileCellValue({ cell }: { cell: CompareCellVM }): JSX.Element {
  return (
    <div className="space-y-0.5">
      <MobileDisplayValue value={cell.displayValue} isMuted={cell.isMuted} />
      {cell.metaLabel ? (
        <p className="text-[10px] tracking-[0.04em] text-disabled">
          {cell.metaLabel}
        </p>
      ) : null}
      {cell.benchmarkLabel ? (
        <p className="text-[10px] leading-snug text-secondary">
          {cell.benchmarkLabel}
        </p>
      ) : null}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Helper                                                               */
/* ------------------------------------------------------------------ */

function MobileDisplayValue({
  value,
  isMuted,
}: {
  value: string;
  isMuted: boolean;
}): JSX.Element {
  if (isMuted) {
    return (
      <p className="text-sm font-medium text-disabled/50 leading-snug">
        — {value}
      </p>
    );
  }

  const parts = value.split(/,\s+/).filter(Boolean);
  if (parts.length <= 1) {
    return (
      <p className="text-sm font-semibold text-primary tabular-nums leading-snug">
        {value}
      </p>
    );
  }

  const visible = parts.slice(0, MAX_MOBILE_LIST_ITEMS);
  const remaining = parts.length - MAX_MOBILE_LIST_ITEMS;

  return (
    <div className="space-y-0.5">
      {visible.map((part) => (
        <p key={part} className="text-[11px] leading-snug text-primary tabular-nums">
          {part}
        </p>
      ))}
      {remaining > 0 ? (
        <p className="text-[10px] text-disabled">+{remaining} more</p>
      ) : null}
    </div>
  );
}

function unitLabel(unit: string): string | null {
  switch (unit) {
    case "percent":
      return "Percent";
    case "count":
      return "Count";
    case "rate":
      return "Rate";
    case "ratio":
      return "Ratio";
    case "score":
      return "Score";
    case "currency":
      return "GBP";
    case "decile":
      return "Decile";
    case "date":
      return "Date";
    case "days":
      return "Days";
    case "years":
      return "Years";
    default:
      return null;
  }
}
