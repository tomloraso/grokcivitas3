import { ChevronDown, ChevronUp, Home, MapPin, Shield } from "lucide-react";
import { useState } from "react";

import { GlossaryTerm } from "../../../components/data/GlossaryTerm";
import { MetricGrid } from "../../../components/data/MetricGrid";
import { MetricUnavailable } from "../../../components/data/MetricUnavailable";
import { Sparkline } from "../../../components/data/Sparkline";
import { StatCard } from "../../../components/data/StatCard";
import { Card } from "../../../components/ui/Card";
import { formatMetricValue } from "../metricCatalog";
import { SectionCompletenessNotice } from "./SectionCompletenessNotice";
import type { AreaContextVM, SectionCompletenessVM } from "../types";

interface NeighbourhoodSectionProps {
  areaContext: AreaContextVM;
  deprivationCompleteness: SectionCompletenessVM;
  crimeCompleteness: SectionCompletenessVM;
  housePriceCompleteness: SectionCompletenessVM;
}

function DeprivationGauge({ decile }: { decile: number }): JSX.Element {
  const colors = [
    "bg-danger",
    "bg-danger",
    "bg-warning",
    "bg-warning",
    "bg-amber-400",
    "bg-amber-400",
    "bg-emerald-400",
    "bg-emerald-400",
    "bg-success",
    "bg-success"
  ];

  return (
    <div className="space-y-1">
      <div className="flex gap-[2px]" role="img" aria-label={`Deprivation decile ${decile} of 10`}>
        {Array.from({ length: 10 }, (_, index) => {
          const position = index + 1;
          const isActive = position === decile;

          return (
            <div key={position} className="relative flex flex-1 flex-col items-center">
              {isActive ? (
                <div className="mb-0.5 h-0 w-0 border-x-[4px] border-t-[5px] border-x-transparent border-t-primary" />
              ) : (
                <div className="mb-0.5 h-[5px]" />
              )}
              <div
                className={`w-full rounded-sm transition-all ${colors[index]} ${
                  isActive
                    ? "h-3 opacity-100 shadow-[0_0_8px_rgba(255,255,255,0.2)]"
                    : "h-2 opacity-25"
                }`}
              />
            </div>
          );
        })}
      </div>
      <div className="flex justify-between text-[10px] text-disabled">
        <span>Most deprived</span>
        <span>Least deprived</span>
      </div>
    </div>
  );
}

function formatDomainValue(value: number | null): string {
  if (value === null) {
    return "n/a";
  }
  return `${value}`;
}

export function NeighbourhoodSection({
  areaContext,
  deprivationCompleteness,
  crimeCompleteness,
  housePriceCompleteness
}: NeighbourhoodSectionProps): JSX.Element {
  const [crimeExpanded, setCrimeExpanded] = useState(false);

  const deprivation =
    areaContext.coverage.hasDeprivation && areaContext.deprivation
      ? areaContext.deprivation
      : null;
  const crime = areaContext.coverage.hasCrime && areaContext.crime ? areaContext.crime : null;
  const housePrices =
    areaContext.coverage.hasHousePrices && areaContext.housePrices
      ? areaContext.housePrices
      : null;

  const crimeRateSparkline =
    crime?.annualIncidentsPer1000
      .map((entry) => entry.incidentsPer1000)
      .filter((value): value is number => value !== null) ?? [];
  const housePriceSparkline = housePrices?.trend.map((point) => point.averagePrice) ?? [];

  return (
    <section
      aria-labelledby="neighbourhood-heading"
      className="panel-surface rounded-lg space-y-5 p-5 sm:p-6"
    >
      <div className="space-y-1">
        <h2
          id="neighbourhood-heading"
          className="flex items-center gap-2 text-lg font-semibold text-primary sm:text-xl"
        >
          <span className="inline-block h-5 w-[3px] rounded-full bg-brand" aria-hidden />
          Neighbourhood Context
        </h2>
        <p className="text-sm text-secondary">
          Based on the school&apos;s postcode, local crime radius and local authority district.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-3">
        <Card className="space-y-4">
          <div className="flex items-center gap-2">
            <MapPin className="h-4 w-4 text-brand" aria-hidden />
            <h3 className="text-base font-semibold text-primary">Area Deprivation</h3>
          </div>
          <SectionCompletenessNotice
            sectionLabel="Area deprivation"
            completeness={deprivationCompleteness}
          />

          {deprivation ? (
            <>
              <DeprivationGauge decile={deprivation.imdDecile} />
              <div className="space-y-1 text-sm text-secondary">
                <p>
                  <GlossaryTerm term="imd">IMD Decile</GlossaryTerm>{" "}
                  <span className="font-semibold text-primary">{deprivation.imdDecile}</span>
                </p>
                <p>
                  <GlossaryTerm term="idaci">IDACI Decile</GlossaryTerm>{" "}
                  <span className="font-semibold text-primary">{deprivation.idaciDecile}</span>
                </p>
                <p>
                  Population{" "}
                  <span className="font-semibold text-primary">
                    {deprivation.populationTotal?.toLocaleString("en-GB") ?? "n/a"}
                  </span>
                </p>
                <p>
                  LAD{" "}
                  <span className="font-semibold text-primary">
                    {deprivation.localAuthorityDistrictName ?? "Unknown"}
                  </span>
                </p>
              </div>

              <div className="grid grid-cols-2 gap-2">
                {deprivation.domains.map((domain) => (
                  <div
                    key={domain.key}
                    className="rounded-md border border-border-subtle/60 bg-surface/50 px-3 py-2"
                  >
                    <p className="text-[11px] font-medium uppercase tracking-[0.06em] text-disabled">
                      {domain.label}
                    </p>
                    <p className="mt-1 text-sm font-semibold text-primary">
                      Decile {formatDomainValue(domain.decile)}
                    </p>
                    <p className="text-xs text-secondary">
                      Score {formatDomainValue(domain.score)}
                    </p>
                  </div>
                ))}
              </div>

              <p className="text-xs text-disabled">
                Source: {deprivation.sourceRelease} ·{" "}
                <GlossaryTerm term="lsoa">{deprivation.lsoaCode}</GlossaryTerm>
              </p>
            </>
          ) : (
            <MetricUnavailable metricLabel="Area deprivation" />
          )}
        </Card>

        <Card className="space-y-4">
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-brand" aria-hidden />
            <h3 className="text-base font-semibold text-primary">Area Crime</h3>
          </div>
          <SectionCompletenessNotice sectionLabel="Area crime" completeness={crimeCompleteness} />

          {crime ? (
            <>
              <p className="text-xs text-secondary">
                Within {crime.radiusMiles} mile radius · Latest {crime.latestMonth}
              </p>
              <MetricGrid columns={2}>
                <StatCard
                  label="Incidents"
                  value={crime.totalIncidents.toLocaleString("en-GB")}
                />
                <StatCard
                  label="Per 1,000"
                  value={formatMetricValue(crime.incidentsPer1000, "rate") ?? "n/a"}
                />
              </MetricGrid>

              {crimeRateSparkline.length > 1 ? (
                <div className="space-y-2 rounded-md border border-border-subtle/60 bg-surface/50 px-3 py-3">
                  <p className="text-xs font-medium uppercase tracking-[0.06em] text-disabled">
                    Annual Rate Trend
                  </p>
                  <Sparkline
                    data={crimeRateSparkline}
                    width={220}
                    height={44}
                    aria-label="Annual crime incidents per 1,000 trend"
                  />
                </div>
              ) : null}

              <div className="space-y-2">
                {crime.categories
                  .slice(0, crimeExpanded ? undefined : 4)
                  .map((category) => (
                    <div
                      key={category.category}
                      className="flex items-center justify-between rounded-md border border-border-subtle/60 bg-surface/50 px-3 py-2"
                    >
                      <span className="text-sm text-primary">{category.category}</span>
                      <span className="text-sm font-medium text-secondary">
                        {category.incidentCount.toLocaleString("en-GB")}
                      </span>
                    </div>
                  ))}
                {crime.categories.length > 4 ? (
                  <button
                    type="button"
                    className="flex w-full items-center justify-center gap-1 rounded-md border border-border-subtle/40 py-2 text-xs font-medium text-secondary transition-colors hover:bg-surface/80 hover:text-primary"
                    onClick={() => setCrimeExpanded((previous) => !previous)}
                  >
                    {crimeExpanded ? (
                      <>
                        <ChevronUp className="h-3 w-3" aria-hidden />
                        Show less
                      </>
                    ) : (
                      <>
                        <ChevronDown className="h-3 w-3" aria-hidden />
                        Show {crime.categories.length - 4} more categories
                      </>
                    )}
                  </button>
                ) : null}
              </div>
            </>
          ) : (
            <MetricUnavailable metricLabel="Area crime context" />
          )}
        </Card>

        <Card className="space-y-4">
          <div className="flex items-center gap-2">
            <Home className="h-4 w-4 text-brand" aria-hidden />
            <h3 className="text-base font-semibold text-primary">House Prices</h3>
          </div>
          <SectionCompletenessNotice
            sectionLabel="Area house prices"
            completeness={housePriceCompleteness}
          />

          {housePrices ? (
            <>
              <p className="text-xs text-secondary">
                {housePrices.areaName} · Latest {housePrices.latestMonth}
              </p>
              <MetricGrid columns={2}>
                <StatCard
                  label="Average Price"
                  value={formatMetricValue(housePrices.averagePrice, "currency") ?? "n/a"}
                />
                <StatCard
                  label="Annual Change"
                  value={formatMetricValue(housePrices.annualChangePct, "percent") ?? "n/a"}
                />
              </MetricGrid>
              <MetricGrid columns={2}>
                <StatCard
                  label="Monthly Change"
                  value={formatMetricValue(housePrices.monthlyChangePct, "percent") ?? "n/a"}
                />
                <StatCard
                  label="Three-Year Change"
                  value={formatMetricValue(housePrices.threeYearChangePct, "percent") ?? "n/a"}
                />
              </MetricGrid>

              {housePriceSparkline.length > 1 ? (
                <div className="space-y-2 rounded-md border border-border-subtle/60 bg-surface/50 px-3 py-3">
                  <p className="text-xs font-medium uppercase tracking-[0.06em] text-disabled">
                    Price Trend
                  </p>
                  <Sparkline
                    data={housePriceSparkline}
                    width={220}
                    height={44}
                    aria-label="Area house price trend"
                  />
                </div>
              ) : null}
            </>
          ) : (
            <MetricUnavailable metricLabel="Area house prices" />
          )}
        </Card>
      </div>
    </section>
  );
}
