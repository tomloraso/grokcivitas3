import { MetricGrid } from "../../../components/data/MetricGrid";
import { MetricUnavailable } from "../../../components/data/MetricUnavailable";
import { Sparkline } from "../../../components/data/Sparkline";
import { StatCard } from "../../../components/data/StatCard";
import type { BenchmarkSlot } from "../../../components/data/StatCard";
import { TrendIndicator } from "../../../components/data/TrendIndicator";
import { formatMetricDelta, formatMetricValue } from "../metricCatalog";
import { SectionCompletenessNotice } from "./SectionCompletenessNotice";
import type {
  BenchmarkDashboardVM,
  BenchmarkMetricVM,
  PerformanceVM,
  PerformanceYearVM,
  SectionCompletenessVM
} from "../types";

/* ------------------------------------------------------------------ */
/* Props                                                               */
/* ------------------------------------------------------------------ */

interface AcademicPerformanceSectionProps {
  performance: PerformanceVM | null;
  completeness: SectionCompletenessVM;
  benchmarkDashboard: BenchmarkDashboardVM | null;
}

/* ------------------------------------------------------------------ */
/* Metric definitions                                                  */
/* ------------------------------------------------------------------ */

type PerformanceValueType = "score_1dp" | "score_2dp" | "pct";

interface PerformanceMetricDef {
  key: string;
  label: string;
  description?: string;
  group: "ks4" | "ks2";
  valueType: PerformanceValueType;
  value: (y: PerformanceYearVM) => number | null;
  hero?: boolean;
}

const PERFORMANCE_METRICS: PerformanceMetricDef[] = [
  // KS4 (secondary)
  { key: "attainment8_average", label: "Attainment 8", description: "Average total score across 8 GCSE subjects including English, maths, and chosen options. The national average is around 46. Higher is better.", group: "ks4", valueType: "score_1dp", value: (y) => y.attainment8Average, hero: true },
  { key: "progress8_average", label: "Progress 8", description: "How much progress pupils made between age 11 and 16 compared to similar pupils nationally. 0 is average; positive means above average progress; negative means below.", group: "ks4", valueType: "score_2dp", value: (y) => y.progress8Average },
  { key: "progress8_disadvantaged_gap", label: "Disadvantage Progress Gap", description: "The gap in Progress 8 scores between disadvantaged and non-disadvantaged pupils. Smaller gaps indicate more equitable outcomes across different backgrounds.", group: "ks4", valueType: "score_2dp", value: (y) => y.progress8DisadvantagedGap },
  { key: "engmath_5_plus_pct", label: "English & Maths Strong Pass", description: "Pupils achieving grade 5 or above in both English and maths GCSEs — considered a 'strong pass' and often required for sixth form or college entry.", group: "ks4", valueType: "pct", value: (y) => y.engmath5PlusPct },
  { key: "engmath_4_plus_pct", label: "English & Maths Standard Pass", description: "Pupils achieving grade 4 or above in both English and maths GCSEs — the 'standard pass', equivalent to the old grade C.", group: "ks4", valueType: "pct", value: (y) => y.engmath4PlusPct },
  { key: "ebacc_entry_pct", label: "EBacc Entered", description: "English Baccalaureate — the percentage of pupils entered for a core set of academic GCSEs: English, maths, sciences, history or geography, and a language.", group: "ks4", valueType: "pct", value: (y) => y.ebaccEntryPct },
  { key: "ebacc_5_plus_pct", label: "EBacc Strong Pass", description: "Pupils achieving grade 5 or above across all English Baccalaureate subjects.", group: "ks4", valueType: "pct", value: (y) => y.ebacc5PlusPct },
  // KS2 (primary)
  { key: "ks2_reading_expected_pct", label: "Year 6 Reading (Expected)", description: "Pupils meeting the expected standard in Key Stage 2 reading assessments at the end of Year 6 (age 10–11).", group: "ks2", valueType: "pct", value: (y) => y.ks2ReadingExpectedPct },
  { key: "ks2_writing_expected_pct", label: "Year 6 Writing (Expected)", description: "Pupils meeting the expected standard in Key Stage 2 writing assessments at the end of Year 6 (age 10–11).", group: "ks2", valueType: "pct", value: (y) => y.ks2WritingExpectedPct },
  { key: "ks2_maths_expected_pct", label: "Year 6 Maths (Expected)", description: "Pupils meeting the expected standard in Key Stage 2 maths assessments at the end of Year 6 (age 10–11).", group: "ks2", valueType: "pct", value: (y) => y.ks2MathsExpectedPct },
  { key: "ks2_combined_expected_pct", label: "Year 6 All Subjects (Expected)", description: "Pupils meeting the expected standard in all three Key Stage 2 subjects: reading, writing and maths.", group: "ks2", valueType: "pct", value: (y) => y.ks2CombinedExpectedPct, hero: true },
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

function barDecimals(unit: BenchmarkMetricVM["unit"]): number {
  if (unit === "count" || unit === "currency") return 0;
  if (unit === "ratio") return 1;
  return 2;
}

function toBenchmarkSlot(metric: BenchmarkMetricVM): BenchmarkSlot {
  return {
    localLabel: metric.localAreaLabel,
    schoolRaw: metric.schoolValue,
    localRaw: metric.localValue,
    nationalRaw: metric.nationalValue,
    isPercent: metric.unit === "percent",
    displayDecimals: barDecimals(metric.unit),
    schoolValueFormatted: formatMetricValue(metric.schoolValue, metric.unit),
    localValueFormatted: formatMetricValue(metric.localValue, metric.unit),
    nationalValueFormatted: formatMetricValue(metric.nationalValue, metric.unit),
    schoolVsLocalDelta: metric.schoolVsLocalDelta,
    schoolVsNationalDelta: metric.schoolVsNationalDelta,
    schoolVsLocalDeltaFormatted: formatMetricDelta(metric.schoolVsLocalDelta, metric.unit),
    schoolVsNationalDeltaFormatted: formatMetricDelta(metric.schoolVsNationalDelta, metric.unit),
  };
}

/* ------------------------------------------------------------------ */
/* Metric card builder                                                 */
/* ------------------------------------------------------------------ */

function buildCards(
  metrics: PerformanceMetricDef[],
  latest: PerformanceYearVM,
  history: PerformanceYearVM[],
  benchmarkLookup: Map<string, BenchmarkMetricVM>,
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

      const bm = benchmarkLookup.get(def.key);

      return (
        <StatCard
          key={def.key}
          label={def.label}
          description={def.description}
          value={formatValue(latestVal, def.valueType) ?? "—"}
          variant={def.hero ? "hero" : "default"}
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
                  <TrendIndicator delta={delta} direction={directionFromDelta(delta)} unit="%" period={histValues.length > 1 ? `${histValues.length}yr` : undefined} />
                ) : (
                  <TrendIndicator delta={delta} direction={directionFromDelta(delta)} asPercentage={false} period={histValues.length > 1 ? `${histValues.length}yr` : undefined} />
                )}
              </div>
            ) : null
          }
          benchmark={bm ? toBenchmarkSlot(bm) : undefined}
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
  benchmarkDashboard,
}: AcademicPerformanceSectionProps): JSX.Element {
  const latest = performance?.latest ?? null;
  const history = performance?.history ?? [];

  const yearRange =
    history.length > 1
      ? `${history[0]?.academicYear ?? ""} – ${history[history.length - 1]?.academicYear ?? ""}`
      : latest?.academicYear ?? null;

  const benchmarkLookup = new Map<string, BenchmarkMetricVM>(
    benchmarkDashboard?.sections.flatMap((s) => s.metrics.map((m) => [m.metricKey, m] as const)) ?? []
  );

  const ks4Defs = PERFORMANCE_METRICS.filter((d) => d.group === "ks4");
  const ks2Defs = PERFORMANCE_METRICS.filter((d) => d.group === "ks2");

  const ks4Cards = latest ? buildCards(ks4Defs, latest, history, benchmarkLookup) : [];
  const ks2Cards = latest ? buildCards(ks2Defs, latest, history, benchmarkLookup) : [];

  const hasAny = ks4Cards.length > 0 || ks2Cards.length > 0;

  return (
    <section
      aria-labelledby="results-progress-heading"
      className="panel-surface rounded-lg space-y-5 p-5 sm:p-6"
    >
      <div className="flex items-baseline justify-between gap-3">
        <h2
          id="results-progress-heading"
          className="flex items-center gap-2 text-lg font-semibold text-primary sm:text-xl"
        >
          <span className="inline-block h-5 w-[3px] rounded-full bg-brand" aria-hidden />
          Results &amp; Progress
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
