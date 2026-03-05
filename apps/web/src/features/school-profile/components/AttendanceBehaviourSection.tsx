import { MetricGrid } from "../../../components/data/MetricGrid";
import { MetricUnavailable } from "../../../components/data/MetricUnavailable";
import { Sparkline } from "../../../components/data/Sparkline";
import { StatCard } from "../../../components/data/StatCard";
import { TrendIndicator } from "../../../components/data/TrendIndicator";
import {
  ATTENDANCE_METRIC_KEYS,
  BEHAVIOUR_METRIC_KEYS,
  formatMetricValue,
  getMetricCatalogEntry
} from "../metricCatalog";
import { SectionCompletenessNotice } from "./SectionCompletenessNotice";
import type {
  AttendanceLatestVM,
  BehaviourLatestVM,
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
}

function renderTrendFooter(series: TrendSeriesVM | undefined) {
  if (!series || series.latestDelta === null) {
    return null;
  }

  const sparkData = series.points
    .map((point) => point.value)
    .filter((value): value is number => value !== null);
  const isPercent = series.unit === "percent";

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
        unit="pp"
        asPercentage={isPercent}
      />
    </div>
  );
}

function AttendanceMetricCard({
  metricKey,
  value,
  series
}: {
  metricKey: string;
  value: number | null;
  series: TrendSeriesVM | undefined;
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
      value={formatMetricValue(value, catalog.unit, catalog.decimals) ?? "n/a"}
      footer={renderTrendFooter(series)}
    />
  );
}

export function AttendanceBehaviourSection({
  attendance,
  behaviour,
  trends,
  attendanceCompleteness,
  behaviourCompleteness
}: AttendanceBehaviourSectionProps): JSX.Element {
  const trendLookup = new Map(
    trends?.series.map((series) => [series.metricKey, series] as const) ?? []
  );

  const attendanceYear = attendance?.academicYear ?? null;
  const behaviourYear = behaviour?.academicYear ?? null;

  return (
    <section
      aria-labelledby="attendance-behaviour-heading"
      className="panel-surface rounded-lg space-y-6 p-5 sm:p-6"
    >
      <div className="space-y-1">
        <h2
          id="attendance-behaviour-heading"
          className="flex items-center gap-2 text-lg font-semibold text-primary sm:text-xl"
        >
          <span className="inline-block h-5 w-[3px] rounded-full bg-brand" aria-hidden />
          Attendance and Behaviour
        </h2>
        <p className="text-sm text-secondary">
          Latest published attendance, persistent absence, suspensions and exclusions.
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
        <MetricGrid columns={3}>
          {ATTENDANCE_METRIC_KEYS.map((metricKey) => {
            const value =
              metricKey === "overall_attendance_pct"
                ? attendance?.overallAttendancePct ?? null
                : metricKey === "overall_absence_pct"
                  ? attendance?.overallAbsencePct ?? null
                  : attendance?.persistentAbsencePct ?? null;

            return (
              <AttendanceMetricCard
                key={metricKey}
                metricKey={metricKey}
                value={value}
                series={trendLookup.get(metricKey)}
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
        <MetricGrid columns={4}>
          {BEHAVIOUR_METRIC_KEYS.map((metricKey) => {
            const value =
              metricKey === "suspensions_count"
                ? behaviour?.suspensionsCount ?? null
                : metricKey === "suspensions_rate"
                  ? behaviour?.suspensionsRate ?? null
                  : metricKey === "permanent_exclusions_count"
                    ? behaviour?.permanentExclusionsCount ?? null
                    : behaviour?.permanentExclusionsRate ?? null;

            return (
              <AttendanceMetricCard
                key={metricKey}
                metricKey={metricKey}
                value={value}
                series={trendLookup.get(metricKey)}
              />
            );
          })}
        </MetricGrid>
      </div>
    </section>
  );
}
