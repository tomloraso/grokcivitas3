import type { CompareCellVM, CompareSchoolColumnVM, CompareSectionVM } from "./types";
import { CompareTableHeader } from "./CompareTableHeader";

interface CompareMetricTableProps {
  schools: CompareSchoolColumnVM[];
  sections: CompareSectionVM[];
}

const LABEL_WIDTH = 200;
const COLUMN_WIDTH = 200;

export function CompareMetricTable({
  schools,
  sections,
}: CompareMetricTableProps): JSX.Element {
  const minWidth = LABEL_WIDTH + schools.length * COLUMN_WIDTH;

  return (
    <div className="overflow-x-auto rounded-xl border border-border-subtle/60 bg-surface/50">
      <table
        className="min-w-full border-separate border-spacing-0"
        style={{ minWidth }}
      >
        <caption className="sr-only">School comparison table</caption>
        <CompareTableHeader
          schools={schools}
          labelWidth={LABEL_WIDTH}
          columnWidth={COLUMN_WIDTH}
        />

        {sections.map((section) => (
          <tbody key={section.key}>
            {/* Section divider row */}
            <tr>
              <td
                colSpan={schools.length + 1}
                className="sticky left-0 z-10 bg-canvas/95 px-4 py-3 backdrop-blur"
              >
                <div className="flex items-center gap-2">
                  <span className="h-px flex-1 bg-brand/20" aria-hidden />
                  <span className="text-xs font-semibold tracking-[0.04em] text-brand">
                    {section.label}
                  </span>
                  <span className="h-px flex-1 bg-brand/20" aria-hidden />
                </div>
              </td>
            </tr>

            {section.rows.map((row) => (
              <tr
                key={row.metricKey}
                className="transition-colors hover:bg-brand/[0.03]"
              >
                {/* Sticky metric label */}
                <th
                  scope="row"
                  className="sticky left-0 z-10 border-b border-border-subtle/30 bg-surface/95 px-4 py-3 text-left align-top backdrop-blur"
                  style={{ minWidth: LABEL_WIDTH, width: LABEL_WIDTH }}
                >
                  <div className="space-y-0.5">
                    <p className="text-sm font-medium text-primary">{row.label}</p>
                    {unitLabel(row.unit) ? (
                      <p className="text-[10px] tracking-[0.04em] text-disabled">
                        {unitLabel(row.unit)}
                      </p>
                    ) : null}
                  </div>
                </th>

                {/* School value cells */}
                {schools.map((school) => {
                  const cell = row.cells.find((c) => c.urn === school.urn);
                  return (
                    <td
                      key={`${row.metricKey}-${school.urn}`}
                      className={`border-b border-border-subtle/30 px-4 py-3 align-top ${cellBgClass(cell?.availability ?? "unavailable")}`}
                    >
                      {cell ? (
                        <CompareCell cell={cell} />
                      ) : (
                        <p className="text-sm text-disabled">—</p>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        ))}
      </table>
    </div>
  );
}

function CompareCell({ cell }: { cell: CompareCellVM }): JSX.Element {
  return (
    <div className="space-y-1">
      <p
        className={`text-base font-semibold tabular-nums leading-snug ${
          cell.isMuted ? "text-secondary" : "text-primary"
        }`}
      >
        {cell.displayValue}
      </p>
      {cell.metaLabel ? (
        <p className="text-[10px] tracking-[0.04em] text-disabled">
          {cell.metaLabel}
        </p>
      ) : null}
      {cell.detailLabel ? (
        <p className="text-[10px] leading-snug text-secondary">{cell.detailLabel}</p>
      ) : null}
      {cell.benchmarkLabel ? (
        <p className="text-[10px] leading-snug text-secondary">{cell.benchmarkLabel}</p>
      ) : null}
    </div>
  );
}

function cellBgClass(availability: CompareCellVM["availability"]): string {
  switch (availability) {
    case "available":
      return "";
    case "unsupported":
      return "bg-surface/60";
    case "suppressed":
      return "bg-warning/5";
    case "unavailable":
    default:
      return "bg-surface/40";
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
