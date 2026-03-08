import { MetricGrid } from "../../../components/data/MetricGrid";
import { MetricUnavailable } from "../../../components/data/MetricUnavailable";
import { Sparkline } from "../../../components/data/Sparkline";
import { StatCard } from "../../../components/data/StatCard";
import type { BenchmarkSlot } from "../../../components/data/StatCard";
import { TrendIndicator } from "../../../components/data/TrendIndicator";
import {
  ATTENDANCE_METRIC_KEYS,
  BEHAVIOUR_METRIC_KEYS,
  formatMetricDelta,
  formatMetricValue,
  getMetricCatalogEntry
} from "../metricCatalog";
import { SectionCompletenessNotice } from "./SectionCompletenessNotice";
import type {
  AttendanceLatestVM,
  BehaviourLatestVM,
  BenchmarkDashboardVM,
  BenchmarkMetricVM,
  SectionCompletenessVM,
  TrendSeriesVM,
  TrendsVM
} from "../types";

interface AttendanceBehaviourSectionProps {
  attendance: AttendanceLatestVM | null;
  behaviour: BehaviourLatestVM | null;
  trends: TrendsVM | null;
  attendanceCompleteness: SectionCompletenessVM;
  behaviourCompleteness: SectionCompletenessVM;
  benchmarkDashboard: BenchmarkDashboardVM | null;
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

function renderTrendFooter(series: TrendSeriesVM | undefined) {
  if (!series || series.latestDelta === null) {
    return null;
  }

  const sparkData = series.points
    .map((point) => point.value)
    .filter((value): value is number => value !== null);
  const isPercent = series.unit === "percent";
  const period = sparkData.length > 1 ? `${sparkData.length}-year trend` : undefined;

  return (
    <div className="flex items-center justify-between gap-2">
      {sparkData.length > 1 ? (
        <Sparkline
          data={sparkData}
          width={92}
          height={30}
          aria-label={`${series.label} trend`}
        />
      ) : null}
      <TrendIndicator
        delta={isPercent ? series.latestDelta : Number(series.latestDelta.toFixed(2))}
        direction={series.latestDirection ?? undefined}
        unit="%"
        asPercentage={isPercent}
        period={period}
      />
    </div>
  );
}

function AttendanceMetricCard({
  metricKey,
  value,
  series,
  benchmark,
  variant = "default"
}: {
  metricKey: string;
  value: number | null;
  series: TrendSeriesVM | undefined;
  benchmark: BenchmarkSlot | undefined;
  variant?: "hero" | "default";
}): JSX.Element {
  const catalog = getMetricCatalogEntry(metricKey);
  if (!catalog) {
    return <MetricUnavailable metricLabel={metricKey} />;
  }

  if (value === null) {
    return <MetricUnavailable metricLabel={catalog.label} />;
  }

  return (
    <StatCard
      label={catalog.label}
      description={catalog.description}
      value={formatMetricValue(value, catalog.unit, catalog.decimals) ?? "n/a"}
      footer={renderTrendFooter(series)}
      benchmark={benchmark}
      variant={variant}
    />
  );
}

export function AttendanceBehaviourSection({
  attendance,
  behaviour,
  trends,
  attendanceCompleteness,
  behaviourCompleteness,
  benchmarkDashboard
}: AttendanceBehaviourSectionProps): JSX.Element {
  const trendLookup = new Map(
    trends?.series.map((series) => [series.metricKey, series] as const) ?? []
  );

  const benchmarkLookup = new Map<string, BenchmarkMetricVM>(
    benchmarkDashboard?.sections.flatMap((s) => s.metrics.map((m) => [m.metricKey, m] as const)) ?? []
  );

  const attendanceYear = attendance?.academicYear ?? null;
  const behaviourYear = behaviour?.academicYear ?? null;

  return (
    <section
      aria-labelledby="day-to-day-heading"
      className="panel-surface rounded-lg space-y-6 p-5 sm:p-6"
    >
      <div className="space-y-1">
        <h2
          id="day-to-day-heading"
          className="flex items-center gap-2 text-lg font-semibold text-primary sm:text-xl"
        >
          <span className="inline-block h-5 w-[3px] rounded-full bg-brand" aria-hidden />
          Day-to-Day at School
        </h2>
        <p className="text-sm text-secondary">
          How regularly pupils come to school, and how the school manages behaviour.
        </p>
      </div>

      <div className="space-y-4">
        <div className="flex items-baseline justify-between gap-3">
          <h3 className="text-base font-semibold text-primary">Attendance</h3>
          {attendanceYear ? (
            <span className="text-xs text-secondary">{attendanceYear}</span>
          ) : null}
        </div>
        <SectionCompletenessNotice
          sectionLabel="Attendance"
          completeness={attendanceCompleteness}
        />
        <MetricGrid columns={3} mobileTwo>
          {ATTENDANCE_METRIC_KEYS.flatMap((metricKey) => {
            const value =
              metricKey === "overall_attendance_pct"
                ? attendance?.overallAttendancePct ?? null
                : metricKey === "overall_absence_pct"
                  ? attendance?.overallAbsencePct ?? null
                  : attendance?.persistentAbsencePct ?? null;

            if (value === null) return [];

            const bm = benchmarkLookup.get(metricKey);

            return (
              <AttendanceMetricCard
                key={metricKey}
                metricKey={metricKey}
                value={value}
                series={trendLookup.get(metricKey)}
                benchmark={bm ? toBenchmarkSlot(bm) : undefined}
                variant={metricKey === "overall_attendance_pct" ? "hero" : "default"}
              />
            );
          })}
        </MetricGrid>
      </div>

      <div className="space-y-4 border-t border-border-subtle/50 pt-5">
        <div className="flex items-baseline justify-between gap-3">
          <h3 className="text-base font-semibold text-primary">Behaviour</h3>
          {behaviourYear ? (
            <span className="text-xs text-secondary">{behaviourYear}</span>
          ) : null}
        </div>
        <SectionCompletenessNotice
          sectionLabel="Behaviour"
          completeness={behaviourCompleteness}
        />
        <MetricGrid columns={4} mobileTwo>
          {BEHAVIOUR_METRIC_KEYS.flatMap((metricKey) => {
            const value =
              metricKey === "suspensions_count"
                ? behaviour?.suspensionsCount ?? null
                : metricKey === "suspensions_rate"
                  ? behaviour?.suspensionsRate ?? null
                  : metricKey === "permanent_exclusions_count"
                    ? behaviour?.permanentExclusionsCount ?? null
                    : behaviour?.permanentExclusionsRate ?? null;

            if (value === null) return [];

            const bm = benchmarkLookup.get(metricKey);

            return (
              <AttendanceMetricCard
                key={metricKey}
                metricKey={metricKey}
                value={value}
                series={trendLookup.get(metricKey)}
                benchmark={bm ? toBenchmarkSlot(bm) : undefined}
              />
            );
          })}
        </MetricGrid>
      </div>
    </section>
  );
}
