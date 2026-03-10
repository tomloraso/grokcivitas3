import { Link } from "react-router-dom";

import { cn } from "../../shared/utils/cn";
import type { CompareSlot } from "./compareSlots";
import { CompareMobileContent } from "./CompareMobileContent";
import type {
  CompareCellVM,
  CompareRowVM,
} from "./types";

/** Must match CompareSchoolStrip column widths */
const LABEL_COL_WIDTH = 200;
const SCHOOL_COL_WIDTH = 180;
const TOTAL_SLOTS = 4;

interface CompareAccordionContentProps {
  slots: CompareSlot[];
  rows: CompareRowVM[];
  /** URN of the origin school to highlight its column */
  originUrn?: string | null;
}

export function CompareAccordionContent({
  slots,
  rows,
  originUrn,
}: CompareAccordionContentProps): JSX.Element {
  const totalMinWidth = LABEL_COL_WIDTH + TOTAL_SLOTS * SCHOOL_COL_WIDTH;

  return (
    <>
    {/* Mobile: vertical stacked cards */}
    <div className="sm:hidden">
      <CompareMobileContent slots={slots} rows={rows} originUrn={originUrn} />
    </div>

    {/* Desktop: horizontal table */}
    <div className="hidden sm:block overflow-x-auto" role="table" aria-label="School comparison table">
      <table
        className="min-w-full border-separate border-spacing-0"
        style={{ minWidth: totalMinWidth }}
      >
        <thead>
          <tr>
            <th
              scope="col"
              className="sticky left-0 z-20 border-b border-border-subtle/30 bg-surface/95 px-4 py-3 backdrop-blur"
              style={{ minWidth: LABEL_COL_WIDTH, width: LABEL_COL_WIDTH }}
            />
            {slots.map((slot, index) =>
              slot ? (
                <th
                  key={slot.urn}
                  scope="col"
                  className={cn(
                    "border-b border-border-subtle/30 px-3 py-3 text-left align-bottom",
                    originUrn === slot.urn && "border-l-2 border-l-brand/30 bg-brand/[0.02]"
                  )}
                  style={{ minWidth: SCHOOL_COL_WIDTH, width: SCHOOL_COL_WIDTH }}
                >
                  <Link
                    to={slot.profileHref}
                    state={slot.profileState}
                    className="block transition-colors hover:text-brand-hover"
                  >
                    <p className="text-xs font-semibold leading-snug text-primary">
                      {slot.name}
                    </p>
                  </Link>
                </th>
              ) : (
                <th
                  key={`empty-${index}`}
                  scope="col"
                  className="border-b border-border-subtle/30 px-3 py-3"
                  style={{ minWidth: SCHOOL_COL_WIDTH, width: SCHOOL_COL_WIDTH }}
                />
              )
            )}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => {
            const isEven = rowIndex % 2 === 0;
            return (
              <tr
                key={row.metricKey}
                className="transition-colors hover:bg-surface/50"
              >
                {/* Sticky metric label */}
                <th
                  scope="row"
                  className={cn(
                    "sticky left-0 z-10 px-4 py-3.5 text-left align-top backdrop-blur",
                    "border-b border-border-subtle/25",
                    isEven ? "bg-surface/[0.08]" : "bg-surface/95"
                  )}
                  style={{ minWidth: LABEL_COL_WIDTH, width: LABEL_COL_WIDTH }}
                >
                  <div className="space-y-0.5">
                    <p className="text-sm font-medium text-primary">
                      {row.label}
                    </p>
                    {unitLabel(row.unit) ? (
                      <p className="text-[10px] tracking-[0.04em] text-disabled">
                        {unitLabel(row.unit)}
                      </p>
                    ) : null}
                  </div>
                </th>

                {/* School value cells — fixed 4 columns */}
                {slots.map((slot, index) => {
                  if (!slot) {
                    return (
                      <td
                        key={`${row.metricKey}-empty-${index}`}
                        className={cn(
                          "px-3 py-3.5",
                          "border-b border-border-subtle/25",
                          isEven && "bg-surface/[0.04]"
                        )}
                        style={{ minWidth: SCHOOL_COL_WIDTH, width: SCHOOL_COL_WIDTH }}
                      />
                    );
                  }
                  const cell = row.cells.find((c) => c.urn === slot.urn);
                  const isOrigin = originUrn === slot.urn;
                  return (
                    <td
                      key={`${row.metricKey}-${slot.urn}`}
                      className={cn(
                        "px-3 py-3.5 align-top",
                        "border-b border-border-subtle/25",
                        isOrigin && "border-l-2 border-l-brand/30 bg-brand/[0.02]",
                        !isOrigin && isEven && "bg-surface/[0.06]",
                        !isOrigin && cellBgClass(cell?.availability ?? "unavailable")
                      )}
                    >
                      {cell ? (
                        <CompareCell cell={cell} />
                      ) : (
                        <p className="text-sm text-disabled/50">&mdash;</p>
                      )}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
    </>
  );
}

/* ------------------------------------------------------------------ */
/* Internal sub-components                                             */
/* ------------------------------------------------------------------ */

function CompareCell({ cell }: { cell: CompareCellVM }): JSX.Element {
  return (
    <div className="space-y-1">
      <CellDisplayValue value={cell.displayValue} isMuted={cell.isMuted} />
      {cell.metaLabel ? (
        <p className="text-[10px] tracking-[0.04em] text-disabled">
          {cell.metaLabel}
        </p>
      ) : null}
      {cell.detailLabel ? (
        <p className="text-[10px] leading-snug text-disabled/70">
          {cell.detailLabel}
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
/* Helpers                                                             */
/* ------------------------------------------------------------------ */

/**
 * Detects comma-separated multi-entry values (e.g. ethnicity summary)
 * and renders them as a compact truncated list instead of a wall of text.
 */
const MAX_LIST_ITEMS = 3;

function CellDisplayValue({
  value,
  isMuted,
}: {
  value: string;
  isMuted: boolean;
}): JSX.Element {
  if (isMuted) {
    return (
      <p className="text-sm font-medium text-disabled/60 leading-snug">
        — {value}
      </p>
    );
  }

  // Split on ", " but only if there are percentage-like entries
  const parts = value.split(/,\s+/).filter(Boolean);
  if (parts.length <= 1) {
    return (
      <p className="text-sm font-semibold text-primary tabular-nums leading-snug">
        {value}
      </p>
    );
  }

  const visible = parts.slice(0, MAX_LIST_ITEMS);
  const remaining = parts.length - MAX_LIST_ITEMS;

  return (
    <div className="space-y-0.5">
      {visible.map((part) => (
        <p
          key={part}
          className="text-xs leading-snug text-primary tabular-nums"
        >
          {part}
        </p>
      ))}
      {remaining > 0 ? (
        <p className="text-[10px] text-disabled">
          +{remaining} more
        </p>
      ) : null}
    </div>
  );
}

function cellBgClass(availability: CompareCellVM["availability"]): string {
  switch (availability) {
    case "available":
      return "";
    case "unsupported":
      return "bg-surface/30";
    case "suppressed":
      return "bg-warning/5";
    case "unavailable":
    default:
      return "bg-surface/20";
  }
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
