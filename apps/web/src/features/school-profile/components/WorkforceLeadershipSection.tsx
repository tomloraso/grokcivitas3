import { MetricGrid } from "../../../components/data/MetricGrid";
import { MetricUnavailable } from "../../../components/data/MetricUnavailable";
import { Sparkline } from "../../../components/data/Sparkline";
import { StatCard } from "../../../components/data/StatCard";
import { TrendIndicator } from "../../../components/data/TrendIndicator";
import { Card } from "../../../components/ui/Card";
import { buildBenchmarkSlot } from "../benchmarkSlot";
import {
  formatMetricValue,
  getMetricCatalogEntry,
  WORKFORCE_METRIC_KEYS
} from "../metricCatalog";
import { SectionCompletenessNotice } from "./SectionCompletenessNotice";
import type {
  BenchmarkDashboardVM,
  BenchmarkMetricVM,
  LeadershipSnapshotVM,
  SectionCompletenessVM,
  TrendSeriesVM,
  TrendsVM,
  WorkforceBreakdownItemVM,
  WorkforceLatestVM
} from "../types";

interface WorkforceLeadershipSectionProps {
  workforce: WorkforceLatestVM | null;
  leadership: LeadershipSnapshotVM | null;
  trends: TrendsVM | null;
  workforceCompleteness: SectionCompletenessVM;
  leadershipCompleteness: SectionCompletenessVM;
  benchmarkDashboard: BenchmarkDashboardVM | null;
}

const WORKFORCE_SNAPSHOT_SET = new Set([
  "pupil_teacher_ratio",
  "teacher_headcount_total",
  "teacher_fte_total",
  "support_staff_headcount_total",
  "support_staff_fte_total",
  "leadership_headcount",
  "supply_staff_pct",
  "third_party_support_staff_headcount"
]);

const WORKFORCE_STABILITY_SET = new Set([
  "teachers_3plus_years_pct",
  "teacher_turnover_pct",
  "qts_pct",
  "qualifications_level6_plus_pct",
  "leadership_share_of_teachers",
  "teacher_average_mean_salary_gbp",
  "teacher_average_median_salary_gbp",
  "teachers_on_leadership_pay_range_pct"
]);

const WORKFORCE_PRESSURE_SET = new Set([
  "teacher_absence_pct",
  "teacher_absence_days_total",
  "teacher_absence_days_average",
  "teacher_absence_days_average_all_teachers",
  "teacher_vacancy_count",
  "teacher_vacancy_rate",
  "teacher_tempfilled_vacancy_count",
  "teacher_tempfilled_vacancy_rate"
]);

const WORKFORCE_SNAPSHOT_KEYS = WORKFORCE_METRIC_KEYS.filter((metricKey) =>
  WORKFORCE_SNAPSHOT_SET.has(metricKey)
);
const WORKFORCE_STABILITY_KEYS = WORKFORCE_METRIC_KEYS.filter((metricKey) =>
  WORKFORCE_STABILITY_SET.has(metricKey)
);
const WORKFORCE_PRESSURE_KEYS = WORKFORCE_METRIC_KEYS.filter((metricKey) =>
  WORKFORCE_PRESSURE_SET.has(metricKey)
);

function renderTrendFooter(series: TrendSeriesVM | undefined) {
  if (!series || series.latestDelta === null) {
    return null;
  }

  const sparkData = series.points
    .map((point) => point.value)
    .filter((value): value is number => value !== null);
  const isPercent = series.unit === "percent";
  const period = sparkData.length > 1 ? `${sparkData.length}-yr trend` : undefined;

  return (
    <div className="space-y-1.5">
      {sparkData.length > 1 ? (
        <Sparkline
          data={sparkData}
          height={30}
          className="w-full"
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

function latestSeriesValue(series: TrendSeriesVM | undefined): number | null {
  if (!series) {
    return null;
  }

  const latestPoint = series.points[series.points.length - 1];
  return latestPoint?.value ?? null;
}

function getWorkforceMetricValue(
  metricKey: string,
  workforce: WorkforceLatestVM | null,
  trendLookup: Map<string, TrendSeriesVM>
): number | null {
  const trendValue = latestSeriesValue(trendLookup.get(metricKey));

  switch (metricKey) {
    case "pupil_teacher_ratio":
      return workforce?.pupilTeacherRatio ?? trendValue;
    case "teacher_headcount_total":
      return workforce?.teacherHeadcountTotal ?? trendValue;
    case "teacher_fte_total":
      return workforce?.teacherFteTotal ?? trendValue;
    case "support_staff_headcount_total":
      return workforce?.supportStaffHeadcountTotal ?? trendValue;
    case "support_staff_fte_total":
      return workforce?.supportStaffFteTotal ?? trendValue;
    case "leadership_headcount":
      return workforce?.leadershipHeadcount ?? null;
    case "supply_staff_pct":
      return workforce?.supplyStaffPct ?? trendValue;
    case "third_party_support_staff_headcount":
      return workforce?.thirdPartySupportStaffHeadcount ?? trendValue;
    case "teachers_3plus_years_pct":
      return workforce?.teachers3plusYearsPct ?? trendValue;
    case "teacher_turnover_pct":
      return workforce?.teacherTurnoverPct ?? trendValue;
    case "qts_pct":
      return workforce?.qtsPct ?? trendValue;
    case "qualifications_level6_plus_pct":
      return workforce?.qualificationsLevel6PlusPct ?? trendValue;
    case "teacher_average_mean_salary_gbp":
      return workforce?.teacherAverageMeanSalaryGbp ?? trendValue;
    case "teacher_absence_pct":
      return workforce?.teacherAbsencePct ?? trendValue;
    case "teacher_vacancy_rate":
      return workforce?.teacherVacancyRate ?? trendValue;
    default:
      return trendValue;
  }
}

function buildMetricCards(
  metricKeys: readonly string[],
  workforce: WorkforceLatestVM | null,
  trendLookup: Map<string, TrendSeriesVM>,
  benchmarkLookup: Map<string, BenchmarkMetricVM>
): JSX.Element[] {
  return metricKeys.flatMap((metricKey) => {
    const catalog = getMetricCatalogEntry(metricKey);
    if (!catalog) {
      return [];
    }

    const value = getWorkforceMetricValue(metricKey, workforce, trendLookup);
    if (value === null) {
      return [];
    }

    const benchmark = benchmarkLookup.get(metricKey);

    return (
      <StatCard
        key={metricKey}
        label={catalog.label}
        description={catalog.description}
        value={formatMetricValue(value, catalog.unit, catalog.decimals) ?? "n/a"}
        footer={renderTrendFooter(trendLookup.get(metricKey))}
        benchmark={benchmark ? buildBenchmarkSlot(benchmark) : undefined}
        variant={
          metricKey === "pupil_teacher_ratio" || metricKey === "teacher_headcount_total"
            ? "hero"
            : "default"
        }
      />
    );
  });
}

function formatBreakdownNumber(value: number | null, decimals?: number): string | null {
  if (value === null) {
    return null;
  }

  return value.toLocaleString("en-GB", {
    minimumFractionDigits: decimals ?? (Number.isInteger(value) ? 0 : 1),
    maximumFractionDigits: decimals ?? (Number.isInteger(value) ? 0 : 1)
  });
}

function formatBreakdownMeta(item: WorkforceBreakdownItemVM): string | null {
  const parts: string[] = [];

  if (item.headcount !== null) {
    parts.push(`${formatBreakdownNumber(item.headcount)} headcount`);
  }
  if (item.fte !== null) {
    parts.push(`${formatBreakdownNumber(item.fte, 1)} FTE`);
  }

  return parts.length > 0 ? parts.join(" · ") : null;
}

function BreakdownCard({
  title,
  description,
  items,
  emptyLabel,
  preferPercentage = true
}: {
  title: string;
  description: string;
  items: WorkforceBreakdownItemVM[];
  emptyLabel: string;
  preferPercentage?: boolean;
}): JSX.Element {
  return (
    <Card className="space-y-4">
      <div className="space-y-1">
        <h3 className="text-base font-semibold text-primary">{title}</h3>
        <p className="text-xs text-secondary">{description}</p>
      </div>

      {items.length === 0 ? (
        <MetricUnavailable metricLabel={emptyLabel} />
      ) : (
        <ol className="space-y-2">
          {items.map((item) => {
            const headlineValue =
              preferPercentage && item.headcountPct !== null
                ? formatMetricValue(item.headcountPct, "percent")
                : preferPercentage && item.ftePct !== null
                  ? formatMetricValue(item.ftePct, "percent")
                  : item.headcount !== null
                    ? formatBreakdownNumber(item.headcount)
                    : item.fte !== null
                      ? `${formatBreakdownNumber(item.fte, 1)} FTE`
                      : null;

            return (
              <li
                key={item.key}
                className="flex items-center justify-between gap-3 rounded-md border border-border-subtle/60 bg-surface/50 px-3 py-2"
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium text-primary">{item.label}</p>
                  <p className="text-xs text-secondary">
                    {formatBreakdownMeta(item) ?? "Published with no value"}
                  </p>
                </div>
                <span className="text-sm font-semibold text-primary">
                  {headlineValue ?? "n/a"}
                </span>
              </li>
            );
          })}
        </ol>
      )}
    </Card>
  );
}

function LeadershipStrip({ leadership }: { leadership: LeadershipSnapshotVM }): JSX.Element {
  const fields: { label: string; value: string }[] = [];

  if (leadership.headteacherName) {
    fields.push({ label: "Headteacher", value: leadership.headteacherName });
  }
  if (leadership.headteacherStartDate) {
    fields.push({ label: "In post since", value: leadership.headteacherStartDate });
  }
  if (leadership.headteacherTenureYears !== null && leadership.headteacherTenureYears !== undefined) {
    fields.push({ label: "Tenure", value: `${leadership.headteacherTenureYears.toFixed(1)} yrs` });
  }
  if (leadership.leadershipTurnoverScore !== null && leadership.leadershipTurnoverScore !== undefined) {
    fields.push({ label: "Leadership Turnover", value: leadership.leadershipTurnoverScore.toFixed(2) });
  }

  if (fields.length === 0) {
    return <MetricUnavailable metricLabel="Leadership metadata" />;
  }

  return (
    <div className="flex min-w-max divide-x divide-border-subtle/60 overflow-x-auto rounded-lg border border-border-subtle/60 bg-surface/50">
      {fields.map((field) => (
        <div key={field.label} className="flex flex-col px-4 py-3">
          <p className="text-[10px] font-medium uppercase tracking-[0.08em] text-disabled whitespace-nowrap">
            {field.label}
          </p>
          <p className="mt-1 text-sm font-semibold text-primary whitespace-nowrap">
            {field.value}
          </p>
        </div>
      ))}
    </div>
  );
}

export function WorkforceLeadershipSection({
  workforce,
  leadership,
  trends,
  workforceCompleteness,
  leadershipCompleteness,
  benchmarkDashboard
}: WorkforceLeadershipSectionProps): JSX.Element {
  const trendLookup = new Map(
    trends?.series.map((series) => [series.metricKey, series] as const) ?? []
  );

  const benchmarkLookup = new Map<string, BenchmarkMetricVM>(
    benchmarkDashboard?.sections.flatMap((section) =>
      section.metrics.map((metric) => [metric.metricKey, metric] as const)
    ) ?? []
  );

  const metricGroups = [
    {
      key: "snapshot",
      title: "Staffing Snapshot",
      description: "Size and shape of the published workforce in the latest year.",
      cards: buildMetricCards(
        WORKFORCE_SNAPSHOT_KEYS,
        workforce,
        trendLookup,
        benchmarkLookup
      )
    },
    {
      key: "stability",
      title: "Workforce Stability & Quality",
      description: "Experience, qualification mix, leadership share, and pay signals.",
      cards: buildMetricCards(
        WORKFORCE_STABILITY_KEYS,
        workforce,
        trendLookup,
        benchmarkLookup
      )
    },
    {
      key: "pressure",
      title: "Absence & Vacancy Pressure",
      description: "Absence patterns and hiring pressure from the latest published returns.",
      cards: buildMetricCards(
        WORKFORCE_PRESSURE_KEYS,
        workforce,
        trendLookup,
        benchmarkLookup
      )
    }
  ].filter((group) => group.cards.length > 0);

  return (
    <section
      aria-labelledby="teachers-staff-heading"
      className="panel-surface rounded-lg space-y-4 p-4 sm:space-y-6 sm:p-6"
    >
      <div className="space-y-1">
        <h2
          id="teachers-staff-heading"
          className="flex items-center gap-2 text-lg font-semibold text-primary sm:text-xl"
        >
          <span className="inline-block h-5 w-[3px] rounded-full bg-brand" aria-hidden />
          Teachers &amp; Staff
        </h2>
        <p className="text-sm text-secondary">
          Classroom staffing depth, teacher composition, and current leadership context.
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

        {metricGroups.length === 0 ? (
          <MetricUnavailable metricLabel="Workforce" />
        ) : (
          <div className="space-y-5">
            {metricGroups.map((group) => (
              <div key={group.key} className="space-y-3">
                <div className="space-y-1">
                  <h4 className="text-sm font-semibold uppercase tracking-[0.08em] text-secondary">
                    {group.title}
                  </h4>
                  <p className="text-sm text-secondary">{group.description}</p>
                </div>
                <MetricGrid columns={4} mobileTwo>
                  {group.cards}
                </MetricGrid>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 border-t border-border-subtle/50 pt-5 xl:grid-cols-2">
        <BreakdownCard
          title="Teacher Mix by Sex"
          description="Published teacher headcount and share by sex."
          items={workforce?.teacherSexBreakdown ?? []}
          emptyLabel="Teacher sex breakdown"
        />
        <BreakdownCard
          title="Teacher Age Profile"
          description="Published teacher headcount and share by age group."
          items={workforce?.teacherAgeBreakdown ?? []}
          emptyLabel="Teacher age breakdown"
        />
        <BreakdownCard
          title="Teacher Ethnicity"
          description="Published teacher headcount and share by broad ethnicity group."
          items={workforce?.teacherEthnicityBreakdown ?? []}
          emptyLabel="Teacher ethnicity breakdown"
        />
        <BreakdownCard
          title="Teacher Qualifications"
          description="Published teacher headcount and share by qualification status."
          items={workforce?.teacherQualificationBreakdown ?? []}
          emptyLabel="Teacher qualification breakdown"
        />
        <BreakdownCard
          title="Support Staff Roles"
          description="Latest support-staff mix by post, with headcount and FTE where published."
          items={workforce?.supportStaffPostMix ?? []}
          emptyLabel="Support staff post mix"
          preferPercentage={false}
        />
      </div>

      <div className="space-y-4 border-t border-border-subtle/50 pt-5">
        <h3 className="text-base font-semibold text-primary">Leadership</h3>
        <SectionCompletenessNotice
          sectionLabel="Leadership"
          completeness={leadershipCompleteness}
        />
        {leadership ? (
          <LeadershipStrip leadership={leadership} />
        ) : (
          <MetricUnavailable metricLabel="Leadership metadata" />
        )}
      </div>
    </section>
  );
}
