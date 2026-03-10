import { ChevronDown, ChevronUp, Home, MapPin, Shield } from "lucide-react";
import { useState } from "react";

import { GlossaryTerm } from "../../../components/data/GlossaryTerm";
import { MetricUnavailable } from "../../../components/data/MetricUnavailable";
import { Sparkline } from "../../../components/data/Sparkline";
import { StatCard } from "../../../components/ui/stat-card";
import { Card } from "../../../components/ui/Card";
import { PremiumPreviewGate } from "../../premium-access/components/PremiumPreviewGate";
import { formatMetricValue } from "../metricCatalog";
import { SectionCompletenessNotice } from "./SectionCompletenessNotice";
import type { NeighbourhoodSectionVM, SectionCompletenessVM } from "../types";

interface NeighbourhoodSectionProps {
  neighbourhood: NeighbourhoodSectionVM;
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

function deprivationSentence(decile: number): string {
  const bottomPct = decile * 10;
  if (decile <= 2) return `This area is in the most deprived ${bottomPct}% of areas in England.`;
  if (decile <= 5) return `This area is in the bottom ${bottomPct}% of areas in England for deprivation.`;
  if (decile >= 9) return `This area is among the least deprived in England (top ${100 - (decile - 1) * 10}%).`;
  return `This area is in the least deprived ${100 - (decile - 1) * 10}% of areas in England.`;
}

function domainDotClass(decile: number | null): string {
  if (decile === null) return "bg-border-subtle";
  if (decile <= 2) return "bg-danger";
  if (decile <= 4) return "bg-warning";
  if (decile <= 6) return "bg-amber-400";
  if (decile <= 8) return "bg-emerald-400";
  return "bg-success";
}

export function NeighbourhoodSection({
  neighbourhood,
  deprivationCompleteness,
  crimeCompleteness,
  housePriceCompleteness
}: NeighbourhoodSectionProps): JSX.Element {
  const [crimeExpanded, setCrimeExpanded] = useState(false);
  const areaContext = neighbourhood.areaContext;

  const deprivation =
    areaContext?.coverage.hasDeprivation && areaContext.deprivation
      ? areaContext.deprivation
      : null;
  const crime = areaContext?.coverage.hasCrime && areaContext.crime ? areaContext.crime : null;
  const housePrices =
    areaContext?.coverage.hasHousePrices && areaContext.housePrices
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
      className="panel-surface rounded-lg space-y-4 p-4 sm:space-y-5 sm:p-6"
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

      <PremiumPreviewGate
        access={neighbourhood.access}
        teaser={
          <div className="space-y-3">
            <p className="text-sm leading-7 text-secondary">
              {neighbourhood.teaserText ??
                "Premium neighbourhood context is available for this school."}
            </p>
            <div className="grid gap-3 sm:grid-cols-3">
              <Card className="border-brand/20 bg-brand/5">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-brand">
                  Deprivation
                </p>
                <p className="mt-2 text-sm text-secondary">
                  LSOA deprivation context and domain deciles.
                </p>
              </Card>
              <Card className="border-brand/20 bg-brand/5">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-brand">
                  Crime
                </p>
                <p className="mt-2 text-sm text-secondary">
                  Local incident rates and category mix within the search radius.
                </p>
              </Card>
              <Card className="border-brand/20 bg-brand/5">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-brand">
                  House Prices
                </p>
                <p className="mt-2 text-sm text-secondary">
                  Local authority price levels, change rates, and recent trend points.
                </p>
              </Card>
            </div>
          </div>
        }
        unavailable={
          <div className="rounded-md border border-border-subtle/60 bg-surface/40 p-4 sm:p-5">
            <p className="text-sm leading-7 text-secondary">
              Neighbourhood context has not been published for this school yet.
            </p>
          </div>
        }
      >
        <div className="grid grid-cols-1 gap-5 xl:grid-cols-3 xl:items-stretch">
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

                <p className="text-sm text-secondary">
                  {deprivationSentence(deprivation.imdDecile)}
                </p>

                {deprivation.localAuthorityDistrictName ? (
                  <p className="text-xs text-secondary">
                    District:{" "}
                    <span className="font-medium text-primary">
                      {deprivation.localAuthorityDistrictName}
                    </span>
                  </p>
                ) : null}

                {deprivation.domains.length > 0 ? (
                  <div className="space-y-1">
                    {deprivation.domains.map((domain) => (
                      <div
                        key={domain.key}
                        className="flex items-center justify-between gap-3 rounded-md border border-border-subtle/60 bg-surface/50 px-3 py-2"
                      >
                        <div className="flex min-w-0 items-center gap-2">
                          <span
                            className={`h-2 w-2 shrink-0 rounded-full ${domainDotClass(domain.decile)}`}
                            aria-hidden
                          />
                          <p className="text-sm text-primary leading-tight">{domain.label}</p>
                        </div>
                        <p className="shrink-0 text-sm font-semibold text-primary">
                          {domain.decile !== null ? `${domain.decile} / 10` : "n/a"}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : null}

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
                  Within {crime.radiusMiles} mile radius · 12 months to {crime.latestMonth}
                </p>

                <div className="grid grid-cols-2 gap-x-4 gap-y-1 rounded-md border border-danger/30 bg-danger/5 px-3 py-2.5">
                  <StatCard
                    variant="mini"
                    size="sm"
                    label="Incidents"
                    value={crime.totalIncidents.toLocaleString("en-GB")}
                    valueClassName="text-primary"
                  />
                  <StatCard
                    variant="mini"
                    size="sm"
                    label="Per 1,000"
                    value={formatMetricValue(crime.incidentsPer1000, "rate") ?? "n/a"}
                    valueClassName="text-primary"
                  />
                </div>

                {crimeRateSparkline.length > 1 ? (
                  <div className="space-y-2 overflow-hidden rounded-md border border-danger/20 bg-danger/5 px-3 py-3">
                    <p className="text-xs font-medium uppercase tracking-[0.06em] text-danger/70">
                      Annual Rate Trend
                    </p>
                    <Sparkline
                      data={crimeRateSparkline}
                      height={44}
                      className="w-full"
                      aria-label="Annual crime incidents per 1,000 trend"
                    />
                  </div>
                ) : null}

                <div className="space-y-2">
                  {crime.categories
                    .slice(0, crimeExpanded ? undefined : 4)
                    .map((category) => {
                      const pct = Math.round((category.incidentCount / crime.totalIncidents) * 100);
                      return (
                        <div
                          key={category.category}
                          className="space-y-1.5 rounded-md border border-border-subtle/60 bg-surface/50 px-3 py-2"
                        >
                          <div className="flex items-center justify-between gap-2">
                            <span className="min-w-0 text-sm text-primary leading-tight">{category.category}</span>
                            <span className="shrink-0 text-sm font-semibold text-primary">
                              {category.incidentCount.toLocaleString("en-GB")}
                            </span>
                          </div>
                          <div className="relative h-1 w-full overflow-hidden rounded-full bg-danger/10">
                            <div
                              className="absolute inset-y-0 left-0 rounded-full bg-danger/50"
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
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

                <div className="grid grid-cols-2 gap-x-4 gap-y-3 rounded-md border border-border-subtle/60 bg-surface/50 px-3 py-2.5">
                  <StatCard
                    variant="mini"
                    size="sm"
                    label="Avg. Price"
                    value={formatMetricValue(housePrices.averagePrice, "currency") ?? "n/a"}
                  />
                  <StatCard
                    variant="mini"
                    size="sm"
                    label="Annual Change"
                    value={formatMetricValue(housePrices.annualChangePct, "percent") ?? "n/a"}
                  />
                  <StatCard
                    variant="mini"
                    size="sm"
                    label="Monthly Change"
                    value={formatMetricValue(housePrices.monthlyChangePct, "percent") ?? "n/a"}
                  />
                  <StatCard
                    variant="mini"
                    size="sm"
                    label="3-Year Change"
                    value={formatMetricValue(housePrices.threeYearChangePct, "percent") ?? "n/a"}
                  />
                </div>

                {housePriceSparkline.length > 1 ? (
                  <div className="space-y-2 overflow-hidden rounded-md border border-border-subtle/60 bg-surface/50 px-3 py-3">
                    <div className="flex items-center justify-between">
                      <p className="text-xs font-medium uppercase tracking-[0.06em] text-disabled">
                        Price Trend
                      </p>
                      <p className="text-[10px] text-disabled">
                        {housePrices.trend[0].month.slice(-4)} –{" "}
                        {housePrices.trend[housePrices.trend.length - 1].month.slice(-4)}
                      </p>
                    </div>
                    <Sparkline
                      data={housePriceSparkline}
                      height={44}
                      className="w-full"
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
      </PremiumPreviewGate>
    </section>
  );
}
