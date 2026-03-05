import { MetricGrid } from "../../../components/data/MetricGrid";
import { MetricUnavailable } from "../../../components/data/MetricUnavailable";
import { Sparkline } from "../../../components/data/Sparkline";
import { StatCard } from "../../../components/data/StatCard";
import { TrendIndicator } from "../../../components/data/TrendIndicator";
import { SectionCompletenessNotice } from "./SectionCompletenessNotice";
import type { PerformanceVM, PerformanceYearVM, SectionCompletenessVM } from "../types";

/* ------------------------------------------------------------------ */
/* Props                                                               */
/* ------------------------------------------------------------------ */

interface AcademicPerformanceSectionProps {
  performance: PerformanceVM | null;
  completeness: SectionCompletenessVM;
}

/* ------------------------------------------------------------------ */
/* Metric definitions                                                  */
/* ------------------------------------------------------------------ */

type PerformanceValueType = "score_1dp" | "score_2dp" | "pct";

interface PerformanceMetricDef {
  key: string;
  label: string;
  group: "ks4" | "ks2";
  valueType: PerformanceValueType;
  value: (y: PerformanceYearVM) => number | null;
}

const PERFORMANCE_METRICS: PerformanceMetricDef[] = [
  // KS4 (secondary)
  { key: "attainment8_average", label: "Attainment 8", group: "ks4", valueType: "score_1dp", value: (y) => y.attainment8Average },
  { key: "progress8_average", label: "Progress 8", group: "ks4", valueType: "score_2dp", value: (y) => y.progress8Average },
  { key: "progress8_disadvantaged_gap", label: "Progress 8 disadvantaged gap", group: "ks4", valueType: "score_2dp", value: (y) => y.progress8DisadvantagedGap },
  { key: "engmath_5_plus_pct", label: "Grade 5+ English & Maths", group: "ks4", valueType: "pct", value: (y) => y.engmath5PlusPct },
  { key: "engmath_4_plus_pct", label: "Grade 4+ English & Maths", group: "ks4", valueType: "pct", value: (y) => y.engmath4PlusPct },
  { key: "ebacc_entry_pct", label: "EBacc entry", group: "ks4", valueType: "pct", value: (y) => y.ebaccEntryPct },
  { key: "ebacc_5_plus_pct", label: "EBacc grade 5+", group: "ks4", valueType: "pct", value: (y) => y.ebacc5PlusPct },
  // KS2 (primary)
  { key: "ks2_reading_expected_pct", label: "KS2 reading expected", group: "ks2", valueType: "pct", value: (y) => y.ks2ReadingExpectedPct },
  { key: "ks2_writing_expected_pct", label: "KS2 writing expected", group: "ks2", valueType: "pct", value: (y) => y.ks2WritingExpectedPct },
  { key: "ks2_maths_expected_pct", label: "KS2 maths expected", group: "ks2", valueType: "pct", value: (y) => y.ks2MathsExpectedPct },
  { key: "ks2_combined_expected_pct", label: "KS2 combined expected", group: "ks2", valueType: "pct", value: (y) => y.ks2CombinedExpectedPct },
];

/* ------------------------------------------------------------------ */
/* Helpers                                                             */
/* ------------------------------------------------------------------ */

function formatValue(value: number | null, type: PerformanceValueType): string | null {
  if (value === null) return null;
  if (type === "pct") return `${value.toFixed(1)}%`;
  if (type === "score_1dp") return value.toFixed(1);
  return value.toFixed(2);
}

function directionFromDelta(d: number): "up" | "down" | "flat" {
  if (d > 0) return "up";
  if (d < 0) return "down";
  return "flat";
}

/* ------------------------------------------------------------------ */
/* Metric card builder                                                 */
/* ------------------------------------------------------------------ */

function buildCards(
  metrics: PerformanceMetricDef[],
  latest: PerformanceYearVM,
  history: PerformanceYearVM[],
): JSX.Element[] {
  return metrics
    .map((def) => {
      const latestVal = def.value(latest);
      if (latestVal === null) return null;

      const histValues = history
        .map((yr) => def.value(yr))
        .filter((v): v is number => v !== null);
      const prev =
        history.length >= 2 ? history[history.length - 2] : null;
      const prevVal = prev ? def.value(prev) : null;
      const delta =
        prevVal !== null ? Number((latestVal - prevVal).toFixed(2)) : null;

      return (
        <StatCard
          key={def.key}
          label={def.label}
          value={formatValue(latestVal, def.valueType) ?? "—"}
          footer={
            delta !== null ? (
              <div className="flex items-center justify-between gap-2">
                {histValues.length > 1 ? (
                  <Sparkline
                    data={histValues}
                    width={92}
                    height={30}
                    aria-label={`${def.label} trend`}
                  />
                ) : null}
                {def.valueType === "pct" ? (
                  <TrendIndicator delta={delta} direction={directionFromDelta(delta)} unit="pp" />
                ) : (
                  <TrendIndicator delta={delta} direction={directionFromDelta(delta)} asPercentage={false} />
                )}
              </div>
            ) : null
          }
        />
      );
    })
    .filter((el): el is JSX.Element => el !== null);
}

/* ------------------------------------------------------------------ */
/* Component                                                           */
/* ------------------------------------------------------------------ */

export function AcademicPerformanceSection({
  performance,
  completeness,
}: AcademicPerformanceSectionProps): JSX.Element {
  const latest = performance?.latest ?? null;
  const history = performance?.history ?? [];

  const yearRange =
    history.length > 1
      ? `${history[0]?.academicYear ?? ""} – ${history[history.length - 1]?.academicYear ?? ""}`
      : latest?.academicYear ?? null;

  const ks4Defs = PERFORMANCE_METRICS.filter((d) => d.group === "ks4");
  const ks2Defs = PERFORMANCE_METRICS.filter((d) => d.group === "ks2");

  const ks4Cards = latest ? buildCards(ks4Defs, latest, history) : [];
  const ks2Cards = latest ? buildCards(ks2Defs, latest, history) : [];

  const hasAny = ks4Cards.length > 0 || ks2Cards.length > 0;

  return (
    <section
      aria-labelledby="performance-heading"
      className="panel-surface rounded-lg space-y-5 p-5 sm:p-6"
    >
      <div className="flex items-baseline justify-between gap-3">
        <h2
          id="performance-heading"
          className="flex items-center gap-2 text-lg font-semibold text-primary sm:text-xl"
        >
          <span className="inline-block h-5 w-[3px] rounded-full bg-brand" aria-hidden />
          Academic Performance
        </h2>
        {yearRange ? (
          <span className="text-xs text-secondary" style={{ opacity: "var(--text-opacity-muted)" }}>
            {yearRange}
          </span>
        ) : null}
      </div>

      <SectionCompletenessNotice sectionLabel="Performance" completeness={completeness} />

      {!hasAny ? (
        <MetricUnavailable metricLabel="School performance" />
      ) : (
        <div className="space-y-6">
          {/* KS4 (secondary) group */}
          {ks4Cards.length > 0 ? (
            <div className="space-y-3">
              <h3 className="text-sm font-medium uppercase tracking-[0.06em] text-disabled">
                Key Stage 4
              </h3>
              <MetricGrid columns={3}>{ks4Cards}</MetricGrid>
            </div>
          ) : null}

          {/* KS2 (primary) group */}
          {ks2Cards.length > 0 ? (
            <div className="space-y-3">
              <h3 className="text-sm font-medium uppercase tracking-[0.06em] text-disabled">
                Key Stage 2
              </h3>
              <MetricGrid columns={3}>{ks2Cards}</MetricGrid>
            </div>
          ) : null}
        </div>
      )}
    </section>
  );
}
