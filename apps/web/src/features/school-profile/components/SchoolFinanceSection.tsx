import { MetricGrid } from "../../../components/data/MetricGrid";
import { MetricUnavailable } from "../../../components/data/MetricUnavailable";
import { Sparkline } from "../../../components/data/Sparkline";
import { StatCard } from "../../../components/data/StatCard";
import type { BenchmarkSlot } from "../../../components/data/StatCard";
import { TrendIndicator } from "../../../components/data/TrendIndicator";
import {
  formatMetricDelta,
  formatMetricValue,
  getMetricCatalogEntry
} from "../metricCatalog";
import { SectionCompletenessNotice } from "./SectionCompletenessNotice";
import type {
  BenchmarkDashboardVM,
  BenchmarkMetricVM,
  FinanceLatestVM,
  SectionCompletenessVM,
  TrendSeriesVM,
  TrendsVM
} from "../types";

interface SchoolFinanceSectionProps {
  finance: FinanceLatestVM | null;
  trends: TrendsVM | null;
  completeness: SectionCompletenessVM;
  benchmarkDashboard: BenchmarkDashboardVM | null;
}

interface FinanceSummaryMetricDef {
  label: string;
  description: string;
  value: (finance: FinanceLatestVM) => number | null;
}

interface FinanceBenchmarkMetricDef {
  metricKey:
    | "income_per_pupil_gbp"
    | "expenditure_per_pupil_gbp"
    | "staff_costs_pct_of_expenditure"
    | "teaching_staff_costs_per_pupil_gbp"
    | "revenue_reserve_per_pupil_gbp";
  variant?: "hero" | "default";
}

const SUMMARY_METRICS: FinanceSummaryMetricDef[] = [
  {
    label: "Total Income",
    description: "The school's total published income for the academic year.",
    value: (finance) => finance.totalIncomeGbp
  },
  {
    label: "Total Expenditure",
    description: "The school's total published expenditure for the academic year.",
    value: (finance) => finance.totalExpenditureGbp
  },
  {
    label: "Total Staff Costs",
    description: "Published staffing costs across the school for the academic year.",
    value: (finance) => finance.totalStaffCostsGbp
  },
  {
    label: "Revenue Reserve",
    description: "Published year-end revenue reserves held by the school.",
    value: (finance) => finance.revenueReserveGbp
  }
];

const BENCHMARKED_METRICS: FinanceBenchmarkMetricDef[] = [
  {
    metricKey: "income_per_pupil_gbp",
    variant: "hero"
  },
  {
    metricKey: "expenditure_per_pupil_gbp"
  },
  {
    metricKey: "staff_costs_pct_of_expenditure"
  },
  {
    metricKey: "teaching_staff_costs_per_pupil_gbp"
  },
  {
    metricKey: "revenue_reserve_per_pupil_gbp"
  }
];

function barDecimals(unit: BenchmarkMetricVM["unit"]): number {
  if (unit === "count" || unit === "currency") {
    return 0;
  }
  if (unit === "ratio") {
    return 1;
  }
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
    schoolVsNationalDeltaFormatted: formatMetricDelta(metric.schoolVsNationalDelta, metric.unit)
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

function resolveBenchmarkedMetricValue(
  metricKey: FinanceBenchmarkMetricDef["metricKey"],
  finance: FinanceLatestVM,
  trendSeries: TrendSeriesVM | undefined,
  benchmark: BenchmarkMetricVM | undefined
): number | null {
  switch (metricKey) {
    case "income_per_pupil_gbp":
      return finance.incomePerPupilGbp;
    case "expenditure_per_pupil_gbp":
      return finance.expenditurePerPupilGbp;
    case "staff_costs_pct_of_expenditure":
      return finance.staffCostsPctOfExpenditure;
    case "revenue_reserve_per_pupil_gbp":
      return finance.revenueReservePerPupilGbp;
    case "teaching_staff_costs_per_pupil_gbp": {
      const latestTrendPoint = trendSeries?.points[trendSeries.points.length - 1];
      return latestTrendPoint?.value ?? benchmark?.schoolValue ?? null;
    }
    default:
      return null;
  }
}

export function SchoolFinanceSection({
  finance,
  trends,
  completeness,
  benchmarkDashboard
}: SchoolFinanceSectionProps): JSX.Element {
  const trendLookup = new Map(
    trends?.series.map((series) => [series.metricKey, series] as const) ?? []
  );
  const benchmarkLookup = new Map<string, BenchmarkMetricVM>(
    benchmarkDashboard?.sections.flatMap((section) =>
      section.metrics.map((metric) => [metric.metricKey, metric] as const)
    ) ?? []
  );

  const summaryCards =
    finance === null
      ? []
      : SUMMARY_METRICS.flatMap((metric) => {
          const value = metric.value(finance);
          if (value === null) {
            return [];
          }

          return (
            <StatCard
              key={metric.label}
              label={metric.label}
              description={metric.description}
              value={formatMetricValue(value, "currency") ?? "n/a"}
            />
          );
        });

  const benchmarkedCards =
    finance === null
      ? []
      : BENCHMARKED_METRICS.flatMap((metric) => {
          const catalog = getMetricCatalogEntry(metric.metricKey);
          if (!catalog) {
            return [];
          }

          const trendSeries = trendLookup.get(metric.metricKey);
          const benchmark = benchmarkLookup.get(metric.metricKey);
          const value = resolveBenchmarkedMetricValue(
            metric.metricKey,
            finance,
            trendSeries,
            benchmark
          );
          if (value === null) {
            return [];
          }

          return (
            <StatCard
              key={metric.metricKey}
              label={catalog.label}
              description={catalog.description}
              value={formatMetricValue(value, catalog.unit, catalog.decimals) ?? "n/a"}
              footer={renderTrendFooter(trendSeries)}
              benchmark={benchmark ? toBenchmarkSlot(benchmark) : undefined}
              variant={metric.variant ?? "default"}
            />
          );
        });

  const shouldShowUnavailable =
    summaryCards.length === 0 &&
    benchmarkedCards.length === 0 &&
    completeness.reasonCode !== "not_applicable";

  return (
    <section
      aria-labelledby="school-finance-heading"
      className="panel-surface rounded-lg space-y-4 p-4 sm:space-y-6 sm:p-6"
    >
      <div className="space-y-1">
        <div className="flex items-baseline justify-between gap-3">
          <h2
            id="school-finance-heading"
            className="flex items-center gap-2 text-lg font-semibold text-primary sm:text-xl"
          >
            <span className="inline-block h-5 w-[3px] rounded-full bg-brand" aria-hidden />
            School Finance
          </h2>
          {finance?.academicYear ? (
            <span className="text-xs text-secondary">{finance.academicYear}</span>
          ) : null}
        </div>
        <p className="text-sm text-secondary">
          Latest published academy finance measures, per-pupil context, and benchmark cues.
        </p>
      </div>

      <SectionCompletenessNotice sectionLabel="Finance" completeness={completeness} />

      {summaryCards.length > 0 ? (
        <div className="space-y-3">
          <h3 className="text-base font-semibold text-primary">Latest totals</h3>
          <MetricGrid columns={4} mobileTwo>
            {summaryCards}
          </MetricGrid>
        </div>
      ) : null}

      {benchmarkedCards.length > 0 ? (
        <div className="space-y-3">
          <h3 className="text-base font-semibold text-primary">Per-pupil and benchmarked</h3>
          <MetricGrid columns={3} mobileTwo>
            {benchmarkedCards}
          </MetricGrid>
        </div>
      ) : null}

      {shouldShowUnavailable ? <MetricUnavailable metricLabel="School finance" /> : null}
    </section>
  );
}
