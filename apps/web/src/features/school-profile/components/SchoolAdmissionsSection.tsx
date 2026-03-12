import { MetricGrid } from "../../../components/data/MetricGrid";
import { MetricUnavailable } from "../../../components/data/MetricUnavailable";
import { Sparkline } from "../../../components/data/Sparkline";
import { StatCard } from "../../../components/data/StatCard";
import { TrendIndicator } from "../../../components/data/TrendIndicator";
import { buildBenchmarkSlot } from "../benchmarkSlot";
import { Card } from "../../../components/ui/Card";
import {
  formatMetricValue,
  getMetricCatalogEntry
} from "../metricCatalog";
import { SectionCompletenessNotice } from "./SectionCompletenessNotice";
import type {
  AdmissionsLatestVM,
  BenchmarkDashboardVM,
  BenchmarkMetricVM,
  SectionCompletenessVM,
  TrendSeriesVM,
  TrendsVM
} from "../types";

interface SchoolAdmissionsSectionProps {
  admissions: AdmissionsLatestVM | null;
  trends: TrendsVM | null;
  completeness: SectionCompletenessVM;
  benchmarkDashboard: BenchmarkDashboardVM | null;
}

interface AdmissionsSummaryMetricDef {
  label: string;
  description: string;
  value: (admissions: AdmissionsLatestVM) => number | null;
}

type BenchmarkedAdmissionsMetricKey =
  | "admissions_oversubscription_ratio"
  | "admissions_first_preference_offer_rate"
  | "admissions_any_preference_offer_rate"
  | "admissions_cross_la_applications";

const SUMMARY_METRICS: AdmissionsSummaryMetricDef[] = [
  {
    label: "Places Offered",
    description: "Total published places offered in the latest admissions cycle.",
    value: (admissions) => admissions.placesOfferedTotal
  },
  {
    label: "Any Preference Applications",
    description: "Applications naming the school at any preference level in the latest cycle.",
    value: (admissions) => admissions.applicationsAnyPreference
  },
  {
    label: "First Preference Applications",
    description: "Applications naming the school as first choice in the latest cycle.",
    value: (admissions) => admissions.applicationsFirstPreference
  }
];

const BENCHMARKED_METRICS: {
  metricKey: BenchmarkedAdmissionsMetricKey;
  variant?: "hero" | "default";
}[] = [
  {
    metricKey: "admissions_oversubscription_ratio",
    variant: "hero"
  },
  {
    metricKey: "admissions_first_preference_offer_rate"
  },
  {
    metricKey: "admissions_any_preference_offer_rate"
  },
  {
    metricKey: "admissions_cross_la_applications"
  }
];

function latestSeriesValue(series: TrendSeriesVM | undefined): number | null {
  if (!series) {
    return null;
  }

  const latestPoint = series.points[series.points.length - 1];
  return latestPoint?.value ?? null;
}

function renderTrendFooter(series: TrendSeriesVM | undefined) {
  if (!series || series.latestDelta === null) {
    return null;
  }

  const sparkData = series.points
    .map((point) => point.value)
    .filter((value): value is number => value !== null);
  const period = sparkData.length > 1 ? `${sparkData.length}-yr trend` : undefined;
  const roundedDelta =
    series.unit === "count" || series.unit === "currency"
      ? Number(series.latestDelta.toFixed(0))
      : Number(series.latestDelta.toFixed(2));

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
        delta={roundedDelta}
        direction={series.latestDirection ?? undefined}
        asPercentage={false}
        period={period}
      />
    </div>
  );
}

function resolveBenchmarkedMetricValue(
  metricKey: BenchmarkedAdmissionsMetricKey,
  admissions: AdmissionsLatestVM | null,
  trendSeries: TrendSeriesVM | undefined
): number | null {
  switch (metricKey) {
    case "admissions_oversubscription_ratio":
      return admissions?.oversubscriptionRatio ?? latestSeriesValue(trendSeries);
    case "admissions_first_preference_offer_rate":
      return admissions?.firstPreferenceOfferRate ?? latestSeriesValue(trendSeries);
    case "admissions_any_preference_offer_rate":
      return admissions?.anyPreferenceOfferRate ?? latestSeriesValue(trendSeries);
    case "admissions_cross_la_applications":
      return latestSeriesValue(trendSeries);
    default:
      return null;
  }
}

export function SchoolAdmissionsSection({
  admissions,
  trends,
  completeness,
  benchmarkDashboard
}: SchoolAdmissionsSectionProps): JSX.Element {
  const trendLookup = new Map(
    trends?.series.map((series) => [series.metricKey, series] as const) ?? []
  );
  const benchmarkLookup = new Map<string, BenchmarkMetricVM>(
    benchmarkDashboard?.sections.flatMap((section) =>
      section.metrics.map((metric) => [metric.metricKey, metric] as const)
    ) ?? []
  );

  const summaryCards =
    admissions === null
      ? []
      : SUMMARY_METRICS.flatMap((metric) => {
          const value = metric.value(admissions);
          if (value === null) {
            return [];
          }

          return (
            <StatCard
              key={metric.label}
              label={metric.label}
              description={metric.description}
              value={formatMetricValue(value, "count") ?? "n/a"}
            />
          );
        });

  const benchmarkedCards = BENCHMARKED_METRICS.flatMap((metric) => {
    const catalog = getMetricCatalogEntry(metric.metricKey);
    if (!catalog) {
      return [];
    }

    const trendSeries = trendLookup.get(metric.metricKey);
    const benchmark = benchmarkLookup.get(metric.metricKey);
    const value = resolveBenchmarkedMetricValue(metric.metricKey, admissions, trendSeries);
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
        benchmark={benchmark ? buildBenchmarkSlot(benchmark) : undefined}
        variant={metric.variant ?? "default"}
      />
    );
  });

  const crossLaOffersSeries = trendLookup.get("admissions_cross_la_offers");
  const crossLaOffersValue = latestSeriesValue(crossLaOffersSeries);
  const policyLabel = admissions?.admissionsPolicy ?? null;

  const shouldShowUnavailable =
    summaryCards.length === 0 &&
    benchmarkedCards.length === 0 &&
    crossLaOffersValue === null &&
    policyLabel === null;

  return (
    <section
      aria-labelledby="school-admissions-heading"
      className="panel-surface rounded-lg space-y-4 p-4 sm:space-y-6 sm:p-6"
    >
      <div className="space-y-1">
        <div className="flex items-baseline justify-between gap-3">
          <h2
            id="school-admissions-heading"
            className="flex items-center gap-2 text-lg font-semibold text-primary sm:text-xl"
          >
            <span className="inline-block h-5 w-[3px] rounded-full bg-brand" aria-hidden />
            School Admissions
          </h2>
          {admissions?.academicYear ? (
            <span className="text-xs text-secondary">{admissions.academicYear}</span>
          ) : null}
        </div>
        <p className="text-sm text-secondary">
          Published demand, offer rates, and how competitive the latest admissions cycle was.
        </p>
      </div>

      <SectionCompletenessNotice sectionLabel="Admissions" completeness={completeness} />

      {summaryCards.length > 0 ? (
        <div className="space-y-3">
          <h3 className="text-base font-semibold text-primary">Latest demand snapshot</h3>
          <MetricGrid columns={3} mobileTwo>
            {summaryCards}
          </MetricGrid>
        </div>
      ) : null}

      {policyLabel ? (
        <Card className="space-y-2">
          <p className="text-[10px] font-semibold uppercase tracking-[0.08em] text-disabled">
            Admissions Policy
          </p>
          <p className="text-base font-semibold text-primary">{policyLabel}</p>
          <p className="text-sm text-secondary">
            Latest policy descriptor published alongside the admissions return.
          </p>
        </Card>
      ) : null}

      {benchmarkedCards.length > 0 ? (
        <div className="space-y-3">
          <h3 className="text-base font-semibold text-primary">Demand and benchmark context</h3>
          <MetricGrid columns={4} mobileTwo>
            {benchmarkedCards}
          </MetricGrid>
        </div>
      ) : null}

      {crossLaOffersValue !== null ? (
        <div className="space-y-3">
          <h3 className="text-base font-semibold text-primary">Cross-authority offers</h3>
          <div className="max-w-sm">
            <StatCard
              label="Cross-LA Offers"
              description="Offers made to applicants from outside the school's home local authority."
              value={formatMetricValue(crossLaOffersValue, "count") ?? "n/a"}
              footer={renderTrendFooter(crossLaOffersSeries)}
            />
          </div>
        </div>
      ) : null}

      {shouldShowUnavailable ? <MetricUnavailable metricLabel="School admissions" /> : null}
    </section>
  );
}
