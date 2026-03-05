import { MetricGrid } from "../../../components/data/MetricGrid";
import { MetricUnavailable } from "../../../components/data/MetricUnavailable";
import { Sparkline } from "../../../components/data/Sparkline";
import { StatCard } from "../../../components/data/StatCard";
import { TrendIndicator } from "../../../components/data/TrendIndicator";
import { Card } from "../../../components/ui/Card";
import {
  formatMetricValue,
  getMetricCatalogEntry,
  WORKFORCE_METRIC_KEYS
} from "../metricCatalog";
import { SectionCompletenessNotice } from "./SectionCompletenessNotice";
import type {
  LeadershipSnapshotVM,
  SectionCompletenessVM,
  TrendSeriesVM,
  TrendsVM,
  WorkforceLatestVM
} from "../types";

interface WorkforceLeadershipSectionProps {
  workforce: WorkforceLatestVM | null;
  leadership: LeadershipSnapshotVM | null;
  trends: TrendsVM | null;
  workforceCompleteness: SectionCompletenessVM;
  leadershipCompleteness: SectionCompletenessVM;
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

function WorkforceMetricCard({
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

export function WorkforceLeadershipSection({
  workforce,
  leadership,
  trends,
  workforceCompleteness,
  leadershipCompleteness
}: WorkforceLeadershipSectionProps): JSX.Element {
  const trendLookup = new Map(
    trends?.series.map((series) => [series.metricKey, series] as const) ?? []
  );

  const leadershipValues = [
    leadership?.headteacherName,
    leadership?.headteacherStartDate,
    leadership?.headteacherTenureYears,
    leadership?.leadershipTurnoverScore
  ];
  const hasLeadershipValues = leadershipValues.some((value) => value !== null && value !== undefined);

  return (
    <section
      aria-labelledby="workforce-heading"
      className="panel-surface rounded-lg space-y-6 p-5 sm:p-6"
    >
      <div className="space-y-1">
        <h2
          id="workforce-heading"
          className="flex items-center gap-2 text-lg font-semibold text-primary sm:text-xl"
        >
          <span className="inline-block h-5 w-[3px] rounded-full bg-brand" aria-hidden />
          Workforce and Leadership
        </h2>
        <p className="text-sm text-secondary">
          Staffing ratios, teacher profile measures and leadership metadata.
        </p>
      </div>

      <div className="space-y-4">
        <div className="flex items-baseline justify-between gap-3">
          <h3 className="text-base font-semibold text-primary">Workforce</h3>
          {workforce?.academicYear ? (
            <span className="text-xs text-secondary">{workforce.academicYear}</span>
          ) : null}
        </div>
        <SectionCompletenessNotice
          sectionLabel="Workforce"
          completeness={workforceCompleteness}
        />
        <MetricGrid columns={3}>
          {WORKFORCE_METRIC_KEYS.map((metricKey) => {
            const value =
              metricKey === "pupil_teacher_ratio"
                ? workforce?.pupilTeacherRatio ?? null
                : metricKey === "supply_staff_pct"
                  ? workforce?.supplyStaffPct ?? null
                  : metricKey === "teachers_3plus_years_pct"
                    ? workforce?.teachers3plusYearsPct ?? null
                    : metricKey === "teacher_turnover_pct"
                      ? workforce?.teacherTurnoverPct ?? null
                      : metricKey === "qts_pct"
                        ? workforce?.qtsPct ?? null
                        : workforce?.qualificationsLevel6PlusPct ?? null;

            return (
              <WorkforceMetricCard
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
        <h3 className="text-base font-semibold text-primary">Leadership</h3>
        <SectionCompletenessNotice
          sectionLabel="Leadership"
          completeness={leadershipCompleteness}
        />

        {!hasLeadershipValues ? (
          <MetricUnavailable metricLabel="Leadership metadata" />
        ) : (
          <Card className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.08em] text-secondary">
                Headteacher
              </p>
              <p className="mt-1 text-base font-semibold text-primary">
                {leadership?.headteacherName ?? "Not published"}
              </p>
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.08em] text-secondary">
                Start Date
              </p>
              <p className="mt-1 text-base font-semibold text-primary">
                {leadership?.headteacherStartDate ?? "Not published"}
              </p>
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.08em] text-secondary">
                Tenure
              </p>
              <p className="mt-1 text-base font-semibold text-primary">
                {leadership?.headteacherTenureYears !== null &&
                leadership?.headteacherTenureYears !== undefined
                  ? `${leadership.headteacherTenureYears.toFixed(1)} years`
                  : "Not published"}
              </p>
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.08em] text-secondary">
                Leadership Turnover Score
              </p>
              <p className="mt-1 text-base font-semibold text-primary">
                {leadership?.leadershipTurnoverScore !== null &&
                leadership?.leadershipTurnoverScore !== undefined
                  ? leadership.leadershipTurnoverScore.toFixed(2)
                  : "Not published"}
              </p>
            </div>
          </Card>
        )}
      </div>
    </section>
  );
}
