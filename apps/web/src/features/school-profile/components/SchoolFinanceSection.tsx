import { useState } from "react";
import { MetricGrid } from "../../../components/data/MetricGrid";
import { MetricUnavailable } from "../../../components/data/MetricUnavailable";
import { Sparkline } from "../../../components/data/Sparkline";
import { StatCard } from "../../../components/ui/stat-card";
import { TrendIndicator } from "../../../components/data/TrendIndicator";
import { buildBenchmarkSlot } from "../benchmarkSlot";
import {
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

/* ── Summary totals (no benchmarks) ────────────────────────────────── */

interface FinanceSummaryMetricDef {
  label: string;
  description: string;
  value: (finance: FinanceLatestVM) => number | null;
}

const SUMMARY_METRICS: FinanceSummaryMetricDef[] = [
  {
    label: "Total Income",
    description: "The school's total published income for the academic year.",
    value: (f) => f.totalIncomeGbp
  },
  {
    label: "Total Expenditure",
    description: "The school's total published expenditure for the academic year.",
    value: (f) => f.totalExpenditureGbp
  },
  {
    label: "Total Staff Costs",
    description: "Published staffing costs across the school for the academic year.",
    value: (f) => f.totalStaffCostsGbp
  },
  {
    label: "Revenue Reserve",
    description: "Published year-end revenue reserves held by the school.",
    value: (f) => f.revenueReserveGbp
  },
  {
    label: "In-Year Balance",
    description:
      "Income minus expenditure for the academic year. A negative value means the school spent more than it received.",
    value: (f) => f.inYearBalanceGbp
  }
];

/* ── Funding mix (grant vs self-generated) ─────────────────────────── */

interface FundingSlice {
  label: string;
  value: number;
  pct: number;
}

function buildFundingMix(finance: FinanceLatestVM): FundingSlice[] | null {
  const grant = finance.totalGrantFundingGbp;
  const selfGen = finance.totalSelfGeneratedFundingGbp;
  if (grant === null && selfGen === null) return null;
  const total = (grant ?? 0) + (selfGen ?? 0);
  if (total <= 0) return null;
  const slices: FundingSlice[] = [];
  if (grant !== null && grant > 0) {
    slices.push({ label: "Grant Funding", value: grant, pct: (grant / total) * 100 });
  }
  if (selfGen !== null && selfGen > 0) {
    slices.push({
      label: "Self-Generated",
      value: selfGen,
      pct: (selfGen / total) * 100
    });
  }
  return slices.length > 0 ? slices : null;
}

/* ── Spending breakdown ────────────────────────────────────────────── */

interface SpendingCategory {
  label: string;
  value: number;
  pct: number;
}

function buildSpendingBreakdown(finance: FinanceLatestVM): SpendingCategory[] | null {
  const total = finance.totalExpenditureGbp;
  if (!total || total <= 0) return null;

  const categories: { label: string; raw: number | null }[] = [
    { label: "Teaching Staff", raw: finance.teachingStaffCostsGbp },
    { label: "Supply Staff", raw: finance.supplyTeachingStaffCostsGbp },
    { label: "Support Staff", raw: finance.educationSupportStaffCostsGbp },
    { label: "Other Staff", raw: finance.otherStaffCostsGbp },
    { label: "Premises", raw: finance.premisesCostsGbp },
    { label: "Educational Supplies", raw: finance.educationalSuppliesCostsGbp },
    { label: "Professional Services", raw: finance.boughtInProfessionalServicesCostsGbp },
    { label: "Catering", raw: finance.cateringCostsGbp }
  ];

  const known = categories
    .filter((c): c is { label: string; raw: number } => c.raw !== null && c.raw > 0)
    .sort((a, b) => b.raw - a.raw);

  if (known.length === 0) return null;

  const knownTotal = known.reduce((sum, c) => sum + c.raw, 0);
  const slices: SpendingCategory[] = known.map((c) => ({
    label: c.label,
    value: c.raw,
    pct: (c.raw / total) * 100
  }));

  const remainder = total - knownTotal;
  if (remainder > 0 && remainder / total > 0.005) {
    slices.push({
      label: "Other Costs",
      value: remainder,
      pct: (remainder / total) * 100
    });
  }

  return slices;
}

/* ── Benchmarked per-pupil metrics ─────────────────────────────────── */

type BenchmarkableMetricKey =
  | "finance_income_per_pupil_gbp"
  | "finance_expenditure_per_pupil_gbp"
  | "finance_staff_costs_pct_of_expenditure"
  | "finance_teaching_staff_costs_per_pupil_gbp"
  | "finance_revenue_reserve_per_pupil_gbp"
  | "finance_supply_staff_costs_pct_of_staff_costs";

interface FinanceBenchmarkMetricDef {
  metricKey: BenchmarkableMetricKey;
  variant?: "hero" | "default";
}

const BENCHMARKED_METRICS: FinanceBenchmarkMetricDef[] = [
  { metricKey: "finance_income_per_pupil_gbp", variant: "hero" },
  { metricKey: "finance_expenditure_per_pupil_gbp" },
  { metricKey: "finance_staff_costs_pct_of_expenditure" },
  { metricKey: "finance_teaching_staff_costs_per_pupil_gbp" },
  { metricKey: "finance_revenue_reserve_per_pupil_gbp" },
  { metricKey: "finance_supply_staff_costs_pct_of_staff_costs" }
];

/* ── Helpers ───────────────────────────────────────────────────────── */

function renderTrendFooter(series: TrendSeriesVM | undefined) {
  if (!series || series.latestDelta === null) return null;

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
  metricKey: BenchmarkableMetricKey,
  finance: FinanceLatestVM,
  trendSeries: TrendSeriesVM | undefined,
  benchmark: BenchmarkMetricVM | undefined
): number | null {
  switch (metricKey) {
    case "finance_income_per_pupil_gbp":
      return finance.incomePerPupilGbp;
    case "finance_expenditure_per_pupil_gbp":
      return finance.expenditurePerPupilGbp;
    case "finance_staff_costs_pct_of_expenditure":
      return finance.staffCostsPctOfExpenditure;
    case "finance_revenue_reserve_per_pupil_gbp":
      return finance.revenueReservePerPupilGbp;
    case "finance_supply_staff_costs_pct_of_staff_costs":
      return finance.supplyStaffCostsPctOfStaffCosts;
    case "finance_teaching_staff_costs_per_pupil_gbp": {
      const latestTrendPoint = trendSeries?.points[trendSeries.points.length - 1];
      return latestTrendPoint?.value ?? benchmark?.schoolValue ?? null;
    }
    default:
      return null;
  }
}

/* ── Shared chart colours (hex for inline style) ─────────────────── */

const CHART_COLORS = [
  "#2dd4bf", // teal-400
  "#0d9488", // teal-600
  "#38bdf8", // sky-400
  "#0284c7", // sky-600
  "#a78bfa", // violet-400
  "#fbbf24", // amber-400
  "#fb7185", // rose-400
  "#22c55e", // emerald-500
  "#9ca3af"  // gray-400
];

const FUNDING_HEX = ["#2dd4bf", "#fbbf24"] as const; // teal-400, amber-400

/* ── Funding bar component ─────────────────────────────────────────── */

function FundingBar({ slices }: { slices: FundingSlice[] }) {
  const [hovered, setHovered] = useState<string | null>(null);

  return (
    <div className="space-y-3">
      <div className="flex h-3 overflow-hidden rounded-full bg-surface/40">
        {slices.map((slice, i) => {
          const isFaded = hovered !== null && hovered !== slice.label;
          return (
            <div
              key={slice.label}
              className="transition-opacity duration-150"
              style={{
                width: `${slice.pct}%`,
                backgroundColor: FUNDING_HEX[i % FUNDING_HEX.length],
                opacity: isFaded ? 0.3 : 1
              }}
              title={`${slice.label}: ${slice.pct.toFixed(1)}%`}
              onMouseEnter={() => setHovered(slice.label)}
              onMouseLeave={() => setHovered(null)}
            />
          );
        })}
      </div>
      <div className="grid grid-cols-1 gap-0.5 sm:grid-cols-2">
        {slices.map((slice, i) => {
          const isActive = hovered === slice.label;
          const isFaded = hovered !== null && !isActive;
          return (
            <div
              key={slice.label}
              className={`flex items-center gap-2 rounded px-2 py-1 text-sm transition-all duration-150 ${isActive ? "bg-surface/50" : ""} ${isFaded ? "opacity-40" : ""}`}
              onMouseEnter={() => setHovered(slice.label)}
              onMouseLeave={() => setHovered(null)}
            >
              <span
                className="inline-block h-2.5 w-2.5 shrink-0 rounded-full"
                style={{ backgroundColor: FUNDING_HEX[i % FUNDING_HEX.length] }}
                aria-hidden
              />
              <span className="truncate text-secondary">{slice.label}</span>
              <span className="ml-auto shrink-0 tabular-nums font-medium text-primary">
                {slice.pct.toFixed(1)}%
              </span>
              <span className="shrink-0 tabular-nums text-xs text-secondary">
                {formatMetricValue(slice.value, "currency") ?? "—"}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ── Spending bar component ────────────────────────────────────────── */

function SpendingBar({ categories }: { categories: SpendingCategory[] }) {
  const [hovered, setHovered] = useState<string | null>(null);

  return (
    <div className="space-y-3">
      <div className="flex h-3 overflow-hidden rounded-full bg-surface/40">
        {categories.map((cat, i) => {
          const isFaded = hovered !== null && hovered !== cat.label;
          return (
            <div
              key={cat.label}
              className="transition-opacity duration-150"
              style={{
                width: `${cat.pct}%`,
                backgroundColor: CHART_COLORS[i % CHART_COLORS.length],
                opacity: isFaded ? 0.3 : 1
              }}
              title={`${cat.label}: ${cat.pct.toFixed(1)}%`}
              onMouseEnter={() => setHovered(cat.label)}
              onMouseLeave={() => setHovered(null)}
            />
          );
        })}
      </div>
      <div className="grid grid-cols-1 gap-0.5 sm:grid-cols-2">
        {categories.map((cat, i) => {
          const isActive = hovered === cat.label;
          const isFaded = hovered !== null && !isActive;
          return (
            <div
              key={cat.label}
              className={`flex items-center gap-2 rounded px-2 py-1 text-sm transition-all duration-150 ${isActive ? "bg-surface/50" : ""} ${isFaded ? "opacity-40" : ""}`}
              onMouseEnter={() => setHovered(cat.label)}
              onMouseLeave={() => setHovered(null)}
            >
              <span
                className="inline-block h-2.5 w-2.5 shrink-0 rounded-full"
                style={{ backgroundColor: CHART_COLORS[i % CHART_COLORS.length] }}
                aria-hidden
              />
              <span className="truncate text-secondary">{cat.label}</span>
              <span className="ml-auto shrink-0 tabular-nums font-medium text-primary">
                {cat.pct.toFixed(1)}%
              </span>
              <span className="shrink-0 tabular-nums text-xs text-secondary">
                {formatMetricValue(cat.value, "currency") ?? "—"}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ── Main component ────────────────────────────────────────────────── */

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

  /* Summary totals */
  const summaryCards =
    finance === null
      ? []
      : SUMMARY_METRICS.flatMap((metric) => {
          const value = metric.value(finance);
          if (value == null) return [];

          const isBalance = metric.label === "In-Year Balance";
          const formatted = formatMetricValue(value, "currency") ?? "—";

          return (
            <StatCard
              key={metric.label}
              label={metric.label}
              tooltip={metric.description}
              value={formatted}
              variant="mini"
              size="sm"
              trendDirection={
                isBalance ? (value > 0 ? "up" : value < 0 ? "down" : null) : undefined
              }
            />
          );
        });

  /* Funding mix */
  const fundingMix = finance ? buildFundingMix(finance) : null;

  /* Spending breakdown */
  const spendingBreakdown = finance ? buildSpendingBreakdown(finance) : null;

  /* Benchmarked per-pupil cards */
  const benchmarkedCards =
    finance === null
      ? []
      : BENCHMARKED_METRICS.flatMap((metric) => {
          const catalog = getMetricCatalogEntry(metric.metricKey);
          if (!catalog) return [];

          const trendSeries = trendLookup.get(metric.metricKey);
          const benchmark = benchmarkLookup.get(metric.metricKey);
          const value = resolveBenchmarkedMetricValue(
            metric.metricKey,
            finance,
            trendSeries,
            benchmark
          );
          if (value == null) return [];

          return (
            <StatCard
              key={metric.metricKey}
              label={catalog.label}
              tooltip={catalog.description}
              value={formatMetricValue(value, catalog.unit, catalog.decimals) ?? "—"}
              footer={renderTrendFooter(trendSeries)}
              benchmark={benchmark ? buildBenchmarkSlot(benchmark) : undefined}
              variant={metric.variant ?? "default"}
            />
          );
        });

  const hasAnyContent =
    summaryCards.length > 0 ||
    fundingMix !== null ||
    spendingBreakdown !== null ||
    benchmarkedCards.length > 0;

  const shouldShowUnavailable =
    !hasAnyContent && completeness.reasonCode !== "not_applicable";

  return (
    <section
      aria-labelledby="school-finance-heading"
      className="panel-surface rounded-lg space-y-4 p-4 sm:space-y-5 sm:p-6"
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
          Published academy finance data and per-pupil benchmarks.
        </p>
      </div>

      <SectionCompletenessNotice sectionLabel="Finance" completeness={completeness} />

      {/* ── Latest Totals ── */}
      {summaryCards.length > 0 ? (
        <div className="space-y-3">
          <h3 className="text-base font-semibold text-primary">Latest Totals</h3>
          <div className="rounded-lg border border-border-subtle/40 bg-surface/30 p-3 sm:p-4">
            <div className="grid grid-cols-2 gap-x-6 gap-y-4 lg:grid-cols-5">
              {summaryCards}
            </div>
          </div>
        </div>
      ) : null}

      {/* ── Funding Sources ── */}
      {fundingMix ? (
        <div className="space-y-3 border-t border-border-subtle/50 pt-5">
          <h3 className="text-base font-semibold text-primary">Funding Sources</h3>
          <div className="rounded-lg border border-border-subtle/40 bg-surface/30 p-3 sm:p-4">
            <FundingBar slices={fundingMix} />
          </div>
        </div>
      ) : null}

      {/* ── Spending Breakdown ── */}
      {spendingBreakdown ? (
        <div className="space-y-3 border-t border-border-subtle/50 pt-5">
          <h3 className="text-base font-semibold text-primary">Where the Money Goes</h3>
          <div className="rounded-lg border border-border-subtle/40 bg-surface/30 p-3 sm:p-4">
            <SpendingBar
              categories={spendingBreakdown}
            />
          </div>
        </div>
      ) : null}

      {/* ── Per-Pupil & Benchmarked ── */}
      {benchmarkedCards.length > 0 ? (
        <div className="space-y-3 border-t border-border-subtle/50 pt-5">
          <h3 className="text-base font-semibold text-primary">Per-Pupil & Benchmarked</h3>
          <MetricGrid columns={3} mobileTwo>
            {benchmarkedCards}
          </MetricGrid>
        </div>
      ) : null}

      {shouldShowUnavailable ? <MetricUnavailable metricLabel="School finance" /> : null}
    </section>
  );
}
