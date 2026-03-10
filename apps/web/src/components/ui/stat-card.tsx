/**
 * StatCard — canonical shadcn-style stat display primitive (P10, 2026-03-09)
 *
 * VARIANTS
 *   default  Standalone card with Card chrome (border, glass, hover lift).
 *            Use for any freestanding metric in a MetricGrid.
 *   hero     Like default but with elevated border glow — for the most
 *            important metric in a section.
 *   mini     No Card chrome, no padding, no border, no shadow.
 *            Use ONLY when embedding inside an existing section card.
 *            Solves the double-padding problem that caused desktop overflow.
 *
 * SIZE  (controls value font size — replaces ad-hoc valueClassName overrides)
 *   sm   mini: text-xl          / standalone: text-2xl sm:text-3xl
 *   md   mini: text-2xl         / standalone: text-3xl sm:text-4xl  ← default
 *   lg   mini: text-2xl sm:text-3xl  / standalone: text-4xl sm:text-5xl
 *        hero (md): text-4xl sm:text-5xl
 *        hero (lg): text-5xl sm:text-6xl
 *
 * OVERFLOW PROTECTION
 *   All label containers include min-w-0 + leading-tight.
 *   Value spans include tabular-nums + break-all.
 *   Outer wrapper always overflow-hidden.
 *
 * TOOLTIP / DESCRIPTION
 *   Pass `tooltip` (preferred) or `description` (legacy alias) to show an
 *   expandable ⓘ info paragraph when the icon is clicked.
 *
 * BENCHMARK BARS
 *   Pass a `BenchmarkSlot` to render proportional school/local/national bars.
 *   Bar heights: h-2 (8px) mobile, h-[5px] sm+ — visible at all breakpoints.
 */

import type { HTMLAttributes, ReactNode } from "react";
import { useState } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { Info } from "lucide-react";

import { cn } from "../../shared/utils/cn";
import { Card } from "./Card";

/* ------------------------------------------------------------------ */
/* BenchmarkSlot                                                       */
/* ------------------------------------------------------------------ */

export interface BenchmarkSlot {
  /** Label for the local benchmark (e.g. "London", "Cheshire East") */
  localLabel: string;
  schoolRaw: number | null;
  localRaw: number | null;
  nationalRaw: number | null;
  /**
   * True for percent-unit metrics → bar scale is fixed 0–100.
   * False → bar scale is max(school, local, national).
   */
  isPercent: boolean;
  /** Decimal places used when formatting values — bars are rounded to this precision */
  displayDecimals: number;
  schoolValueFormatted: string | null;
  localValueFormatted: string | null;
  nationalValueFormatted: string | null;
  schoolVsLocalDelta: number | null;
  schoolVsNationalDelta: number | null;
  schoolVsLocalDeltaFormatted: string | null;
  schoolVsNationalDeltaFormatted: string | null;
}

/* ------------------------------------------------------------------ */
/* Internal helpers — benchmark bars                                   */
/* ------------------------------------------------------------------ */

function deltaColorClass(delta: number | null): string {
  if (delta === null) return "text-secondary";
  if (delta > 0) return "text-trend-up";
  if (delta < 0) return "text-trend-down";
  return "text-trend-flat";
}

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
          <span
            className={`shrink-0 text-[10px] tabular-nums leading-none ${deltaColorClass(delta)}`}
          >
            {deltaFormatted}
          </span>
        ) : null}
      </div>
      {/* h-2 mobile, h-[5px] sm+ — bars visible at all breakpoints */}
      <div className="h-2 w-full overflow-hidden rounded-full bg-border-subtle/40 sm:h-[5px]">
        <div
          className={`h-full rounded-full ${barClass}`}
          style={{ width: `${widthPct}%`, opacity: 0.85 }}
        />
      </div>
    </div>
  );
}

function BenchmarkBlock({ benchmark }: { benchmark: BenchmarkSlot }): JSX.Element {
  const { schoolRaw, localRaw, nationalRaw, isPercent, displayDecimals } = benchmark;

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
      <div className="space-y-2 sm:space-y-2.5">
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
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* cva — outer wrapper classes                                         */
/* ------------------------------------------------------------------ */

const statCardWrapperVariants = cva(
  "relative flex flex-col overflow-hidden",
  {
    variants: {
      variant: {
        default: "gap-2",
        hero:    "gap-2",
        mini:    "gap-1",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

/* ------------------------------------------------------------------ */
/* Value font-size map: [size][variant]                                */
/* ------------------------------------------------------------------ */

const VALUE_SIZE_CLASSES: Record<string, Record<string, string>> = {
  sm: {
    default: "text-2xl sm:text-3xl",
    hero:    "text-3xl sm:text-4xl",
    mini:    "text-xl",
  },
  md: {
    default: "text-3xl sm:text-4xl",
    hero:    "text-4xl sm:text-5xl",
    mini:    "text-2xl",
  },
  lg: {
    default: "text-4xl sm:text-5xl",
    hero:    "text-5xl sm:text-6xl",
    mini:    "text-2xl sm:text-3xl",
  },
};

/* ------------------------------------------------------------------ */
/* Props                                                               */
/* ------------------------------------------------------------------ */

interface StatCardProps
  extends Omit<HTMLAttributes<HTMLDivElement>, "children">,
    VariantProps<typeof statCardWrapperVariants> {
  /** Metric label — plain text or JSX (e.g. GlossaryTerm) */
  label: ReactNode;
  /**
   * Info text shown in an expandable paragraph when ⓘ is tapped.
   * `tooltip` is the preferred name; `description` is accepted as a legacy alias.
   */
  tooltip?: string;
  /** @deprecated Use `tooltip` instead. Kept for backward compatibility. */
  description?: string;
  /** Primary display value (e.g. "32.4%") */
  value: string;
  /** Optional element rendered below the value (sparkline, TrendIndicator) */
  footer?: ReactNode;
  /** Optional icon rendered top-right (standalone variants only) */
  icon?: ReactNode;
  /** Benchmark comparison bars */
  benchmark?: BenchmarkSlot;
  /**
   * Controls value font size. Replaces per-call valueClassName overrides.
   * sm = smaller (for dense grids), md = default, lg = large hero numbers.
   */
  size?: "sm" | "md" | "lg";
  /**
   * Renders a solid teal direction triangle (▲/▼) inline immediately after the
   * value. Always brand teal — never conditional on good/bad.
   * Use `footer` + TrendIndicator when you also need a delta number or sparkline.
   */
  trendDirection?: "up" | "down" | null;
  /**
   * @deprecated Use `size` instead. Escape hatch for one-off overrides only.
   * Will be ignored when `size` is explicitly set.
   */
  valueClassName?: string;
}

/* ------------------------------------------------------------------ */
/* StatCard                                                            */
/* ------------------------------------------------------------------ */

export function StatCard({
  label,
  tooltip,
  description,
  value,
  footer,
  icon,
  benchmark,
  variant = "default",
  size = "md",
  trendDirection,
  valueClassName,
  className,
  ...props
}: StatCardProps): JSX.Element {
  const [showInfo, setShowInfo] = useState(false);

  // Resolve info text: `tooltip` preferred, `description` as legacy fallback
  const infoText = tooltip ?? description;

  // Resolve value size class: explicit size wins over legacy valueClassName
  const valueSizeClass = VALUE_SIZE_CLASSES[size]?.[variant ?? "default"]
    ?? VALUE_SIZE_CLASSES.md.default;

  const inner = (
    <>
      {/* Label row */}
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1 space-y-1 min-h-[40px]">
          <div className="flex items-center gap-1">
            <span className="min-w-0 text-xs font-medium uppercase tracking-[0.08em] leading-tight text-secondary">
              {label}
            </span>
            {infoText ? (
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
          {showInfo && infoText ? (
            <p className="text-[11px] leading-snug text-secondary">{infoText}</p>
          ) : null}
        </div>
        {icon && variant !== "mini" ? (
          <span
            className="shrink-0 text-disabled transition-colors duration-fast group-hover:text-secondary"
            aria-hidden
          >
            {icon}
          </span>
        ) : null}
      </div>

      {/* Value + optional inline direction triangle (triangle precedes the number) */}
      <div className="flex items-baseline gap-1.5">
        {trendDirection ? (
          <span className="shrink-0 text-sm font-bold leading-none text-brand" aria-hidden>
            {trendDirection === "up" ? "▲" : "▼"}
          </span>
        ) : null}
        <span
          className={cn(
            "font-display font-bold leading-tight tracking-tight text-primary tabular-nums break-all",
            valueSizeClass,
            valueClassName
          )}
        >
          {value}
        </span>
      </div>

      {/* Footer (sparkline + trend indicator) */}
      {footer ? <div className="pt-1">{footer}</div> : null}

      {/* Benchmark bars */}
      {benchmark ? <BenchmarkBlock benchmark={benchmark} /> : null}
    </>
  );

  if (variant === "mini") {
    return (
      <div
        className={cn(statCardWrapperVariants({ variant }), className)}
        {...props}
      >
        {inner}
      </div>
    );
  }

  return (
    <Card
      className={cn(
        "group",
        statCardWrapperVariants({ variant }),
        "p-4 transition-colors duration-fast hover:border-brand/25 sm:p-5",
        variant === "hero" &&
          "border-brand/30 shadow-sm shadow-[0_0_28px_rgba(0,212,200,0.12)] hover:border-brand/40",
        className
      )}
      {...props}
    >
      {inner}
    </Card>
  );
}
