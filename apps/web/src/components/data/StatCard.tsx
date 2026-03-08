import type { HTMLAttributes, ReactNode } from "react";
import { useState } from "react";

import { Info } from "lucide-react";

import { cn } from "../../shared/utils/cn";
import { Card } from "../ui/Card";

/* ------------------------------------------------------------------ */
/* BenchmarkSlot — passed from section components, data pre-formatted  */
/* ------------------------------------------------------------------ */

export interface BenchmarkSlot {
  /** Label for the local benchmark (e.g. "London", "Cheshire East") */
  localLabel: string;
  /** Raw numeric values — used to draw proportional bars */
  schoolRaw: number | null;
  localRaw: number | null;
  nationalRaw: number | null;
  /**
   * True for percent-unit metrics → bar scale is fixed 0–100.
   * False → bar scale is max(school, local, national).
   */
  isPercent: boolean;
  /**
   * Decimal places used when formatting values — bars are rounded to this
   * precision so bar widths always match what the displayed numbers say.
   */
  displayDecimals: number;
  /** Pre-formatted display strings */
  schoolValueFormatted: string | null;
  localValueFormatted: string | null;
  nationalValueFormatted: string | null;
  /** Raw deltas (school minus benchmark) — used for colour coding only */
  schoolVsLocalDelta: number | null;
  schoolVsNationalDelta: number | null;
  /** Pre-formatted delta strings */
  schoolVsLocalDeltaFormatted: string | null;
  schoolVsNationalDeltaFormatted: string | null;
}

/* ------------------------------------------------------------------ */
/* Internal helpers                                                    */
/* ------------------------------------------------------------------ */

function deltaColorClass(delta: number | null): string {
  if (delta === null) return "text-secondary";
  if (delta > 0) return "text-trend-up";
  if (delta < 0) return "text-trend-down";
  return "text-trend-flat";
}

/* sm+ visual bar row */
function BarRow({
  label,
  barClass,
  widthPct,
  valueFormatted,
  delta,
  deltaFormatted,
}: {
  label: string;
  barClass: string;
  widthPct: number;
  valueFormatted: string | null;
  delta: number | null;
  deltaFormatted: string | null;
}): JSX.Element {
  return (
    <div className="space-y-0.5">
      <div className="flex items-center gap-1">
        <span className="min-w-0 flex-1 truncate text-[10px] leading-none text-secondary">
          {label}
        </span>
        {valueFormatted ? (
          <span className="shrink-0 text-[10px] font-semibold tabular-nums leading-none text-primary">
            {valueFormatted}
          </span>
        ) : null}
        {deltaFormatted ? (
          <span className={`shrink-0 text-[10px] tabular-nums leading-none ${deltaColorClass(delta)}`}>
            {deltaFormatted}
          </span>
        ) : null}
      </div>
      <div className="h-[5px] w-full overflow-hidden rounded-full bg-border-subtle/40">
        <div
          className={`h-full rounded-full ${barClass}`}
          style={{ width: `${widthPct}%`, opacity: 0.85 }}
        />
      </div>
    </div>
  );
}

/* Mobile text row (no bars) */
function TextRow({
  dotClass,
  label,
  valueFormatted,
  delta,
  deltaFormatted,
}: {
  dotClass: string;
  label: string;
  valueFormatted: string | null;
  delta: number | null;
  deltaFormatted: string | null;
}): JSX.Element {
  return (
    <div className="flex items-center gap-1.5 text-[11px]">
      <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${dotClass}`} aria-hidden />
      <span className="min-w-0 flex-1 truncate text-secondary">{label}</span>
      {valueFormatted ? (
        <span className="shrink-0 font-semibold tabular-nums text-primary">{valueFormatted}</span>
      ) : null}
      {deltaFormatted ? (
        <span className={`shrink-0 tabular-nums ${deltaColorClass(delta)}`}>{deltaFormatted}</span>
      ) : null}
    </div>
  );
}

/* Full benchmark block */
function BenchmarkBlock({ benchmark }: { benchmark: BenchmarkSlot }): JSX.Element {
  const { schoolRaw, localRaw, nationalRaw, isPercent, displayDecimals } = benchmark;

  // Round to display precision so bars match the numbers shown (avoids mismatched
  // bar widths when sub-display-precision differences exist between school/local/national)
  const r = (v: number | null) =>
    v === null ? null : parseFloat(v.toFixed(displayDecimals));

  const scale = isPercent
    ? 100
    : Math.max(r(schoolRaw) ?? 0, r(localRaw) ?? 0, r(nationalRaw) ?? 0, 0.001);

  const pct = (v: number | null) => {
    const rv = r(v);
    return rv === null ? 0 : Math.min(100, Math.max(0, (rv / scale) * 100));
  };

  return (
    <div className="mt-auto space-y-2 border-t border-border-subtle/50 pt-2.5">
      {/* sm+: proportional bar chart */}
      <div className="hidden space-y-2.5 sm:block">
        <BarRow
          label="This school"
          barClass="bg-benchmark-school"
          widthPct={pct(schoolRaw)}
          valueFormatted={benchmark.schoolValueFormatted}
          delta={null}
          deltaFormatted={null}
        />
        {localRaw !== null ? (
          <BarRow
            label={benchmark.localLabel}
            barClass="bg-benchmark-local"
            widthPct={pct(localRaw)}
            valueFormatted={benchmark.localValueFormatted}
            delta={benchmark.schoolVsLocalDelta}
            deltaFormatted={benchmark.schoolVsLocalDeltaFormatted}
          />
        ) : null}
        {nationalRaw !== null ? (
          <BarRow
            label="England"
            barClass="bg-benchmark-national"
            widthPct={pct(nationalRaw)}
            valueFormatted={benchmark.nationalValueFormatted}
            delta={benchmark.schoolVsNationalDelta}
            deltaFormatted={benchmark.schoolVsNationalDeltaFormatted}
          />
        ) : null}
      </div>

      {/* mobile: compact text rows */}
      <div className="space-y-1.5 sm:hidden">
        <TextRow
          dotClass="bg-benchmark-school"
          label="This school"
          valueFormatted={benchmark.schoolValueFormatted}
          delta={null}
          deltaFormatted={null}
        />
        {localRaw !== null ? (
          <TextRow
            dotClass="bg-benchmark-local"
            label={benchmark.localLabel}
            valueFormatted={benchmark.localValueFormatted}
            delta={benchmark.schoolVsLocalDelta}
            deltaFormatted={benchmark.schoolVsLocalDeltaFormatted}
          />
        ) : null}
        {nationalRaw !== null ? (
          <TextRow
            dotClass="bg-benchmark-national"
            label="England"
            valueFormatted={benchmark.nationalValueFormatted}
            delta={benchmark.schoolVsNationalDelta}
            deltaFormatted={benchmark.schoolVsNationalDeltaFormatted}
          />
        ) : null}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* StatCard                                                            */
/* ------------------------------------------------------------------ */

interface StatCardProps extends HTMLAttributes<HTMLDivElement> {
  /** Metric label — plain text or JSX (e.g. GlossaryTerm) */
  label: ReactNode;
  /** Optional plain-English explanation shown when the ⓘ button is tapped */
  description?: string;
  /** Primary display value (e.g. "32.4%") */
  value: string;
  /** Optional secondary element rendered below the value (e.g. TrendIndicator, Sparkline) */
  footer?: ReactNode;
  /** Optional icon rendered top-right */
  icon?: ReactNode;
  /** Optional inline benchmark comparison */
  benchmark?: BenchmarkSlot;
  /** "hero" gives the card elevated visual weight for the most important metric in a section */
  variant?: "hero" | "default";
}

export function StatCard({
  label,
  description,
  value,
  footer,
  icon,
  benchmark,
  variant = "default",
  className,
  ...props
}: StatCardProps): JSX.Element {
  const [showInfo, setShowInfo] = useState(false);

  return (
    <Card
      className={cn(
        "group relative flex flex-col gap-2 overflow-hidden p-4 transition-colors duration-fast hover:border-brand/25 sm:p-5",
        variant === "hero" && "border-brand/30 shadow-sm shadow-[0_0_28px_rgba(168,85,247,0.10)]",
        className
      )}
      {...props}
    >
      {/* Header row: label + optional icon */}
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1 space-y-1">
          <div className="flex items-center gap-1">
            <span className="text-xs font-medium uppercase tracking-[0.08em] text-secondary">
              {label}
            </span>
            {description ? (
              <button
                type="button"
                onClick={() => setShowInfo((v) => !v)}
                className="shrink-0 rounded text-disabled transition-colors hover:text-secondary focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-brand"
                aria-label="About this metric"
                aria-expanded={showInfo}
              >
                <Info className="h-3 w-3" aria-hidden />
              </button>
            ) : null}
          </div>
          {showInfo && description ? (
            <p className="text-[11px] leading-snug text-secondary">{description}</p>
          ) : null}
        </div>
        {icon ? (
          <span className="shrink-0 text-disabled transition-colors duration-fast group-hover:text-secondary" aria-hidden>
            {icon}
          </span>
        ) : null}
      </div>

      {/* Hero number */}
      <span className={cn(
        "font-display font-bold leading-tight tracking-tight text-primary",
        variant === "hero" ? "text-4xl sm:text-5xl" : "text-3xl sm:text-4xl"
      )}>
        {value}
      </span>

      {/* Optional footer (sparkline + trend indicator) */}
      {footer ? <div className="pt-1">{footer}</div> : null}

      {/* Benchmark comparison block */}
      {benchmark ? <BenchmarkBlock benchmark={benchmark} /> : null}
    </Card>
  );
}
