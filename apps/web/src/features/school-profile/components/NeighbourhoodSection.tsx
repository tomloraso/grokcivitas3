import { ChevronDown, ChevronUp, MapPin, Shield } from "lucide-react";
import { useState } from "react";

import { GlossaryTerm } from "../../../components/data/GlossaryTerm";
import { MetricUnavailable } from "../../../components/data/MetricUnavailable";
import { StatCard } from "../../../components/data/StatCard";
import { Card } from "../../../components/ui/Card";
import { SectionCompletenessNotice } from "./SectionCompletenessNotice";
import type { AreaContextVM, SectionCompletenessVM } from "../types";

interface NeighbourhoodSectionProps {
  areaContext: AreaContextVM;
  deprivationCompleteness: SectionCompletenessVM;
  crimeCompleteness: SectionCompletenessVM;
}

/* ------------------------------------------------------------------ */
/* Deprivation gauge — visual 1-10 scale                               */
/* ------------------------------------------------------------------ */

function DeprivationGauge({ decile }: { decile: number }): JSX.Element {
  // Full-spectrum colours so the scale is always complete and readable
  const colors = [
    "bg-danger",      // 1
    "bg-danger",      // 2
    "bg-warning",     // 3
    "bg-warning",     // 4
    "bg-amber-400",   // 5
    "bg-amber-400",   // 6
    "bg-emerald-400", // 7
    "bg-emerald-400", // 8
    "bg-success",     // 9
    "bg-success",     // 10
  ];

  return (
    <div className="space-y-1">
      <div className="flex gap-[2px]" role="img" aria-label={`Deprivation decile ${decile} of 10`}>
        {Array.from({ length: 10 }, (_, i) => {
          const pos = i + 1;
          const isActive = pos === decile;

          return (
            <div key={pos} className="relative flex flex-1 flex-col items-center">
              {/* Pointer triangle above active segment */}
              {isActive ? (
                <div className="mb-0.5 h-0 w-0 border-x-[4px] border-t-[5px] border-x-transparent border-t-primary" />
              ) : (
                <div className="mb-0.5 h-[5px]" />
              )}
              <div
                className={`w-full rounded-sm transition-all ${colors[i]} ${
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

/* ------------------------------------------------------------------ */
/* Deprivation context copy                                            */
/* ------------------------------------------------------------------ */

function deprivationContextLabel(decile: number): string {
  if (decile <= 2) {
    return "This area has higher levels of deprivation (1 is most deprived, 10 is least).";
  }
  if (decile >= 9) {
    return "This area has lower levels of deprivation (1 is most deprived, 10 is least).";
  }
  return "This area has mid-range deprivation levels (1 is most deprived, 10 is least).";
}

/* ------------------------------------------------------------------ */
/* Component                                                           */
/* ------------------------------------------------------------------ */

export function NeighbourhoodSection({
  areaContext,
  deprivationCompleteness,
  crimeCompleteness,
}: NeighbourhoodSectionProps): JSX.Element {
  const [crimeExpanded, setCrimeExpanded] = useState(false);

  const deprivation =
    areaContext.coverage.hasDeprivation && areaContext.deprivation
      ? areaContext.deprivation
      : null;

  const crime =
    areaContext.coverage.hasCrime && areaContext.crime ? areaContext.crime : null;

  const hasAnyData = deprivation || crime;

  return (
    <section aria-labelledby="neighbourhood-heading" className="panel-surface rounded-lg space-y-5 p-5 sm:p-6">
      <div className="space-y-1">
        <h2
          id="neighbourhood-heading"
          className="flex items-center gap-2 text-lg font-semibold text-primary sm:text-xl"
        >
          <span className="inline-block h-5 w-[3px] rounded-full bg-brand" aria-hidden />
          Neighbourhood Context
        </h2>
        <p className="text-sm text-secondary">
          Based on the school&apos;s local area and postcode.
        </p>
      </div>

      {!hasAnyData ? (
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
          <Card className="space-y-4 p-5 sm:p-6">
            <div className="flex items-center gap-2">
              <MapPin className="h-4 w-4 text-brand" aria-hidden />
              <h3 className="text-base font-semibold text-primary">
                Area Deprivation
              </h3>
            </div>
            <SectionCompletenessNotice
              sectionLabel="Area deprivation"
              completeness={deprivationCompleteness}
            />
            <MetricUnavailable metricLabel="Area deprivation" />
          </Card>
          <Card className="space-y-4 p-5 sm:p-6">
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4 text-brand" aria-hidden />
              <h3 className="text-base font-semibold text-primary">
                Area Crime
              </h3>
            </div>
            <SectionCompletenessNotice
              sectionLabel="Area crime"
              completeness={crimeCompleteness}
            />
            <MetricUnavailable metricLabel="Area crime context" />
          </Card>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
          {/* Deprivation */}
          <Card className="space-y-4 p-5 sm:p-6">
            <div className="flex items-center gap-2">
              <MapPin className="h-4 w-4 text-brand" aria-hidden />
              <h3 className="text-base font-semibold text-primary">
                Area Deprivation
              </h3>
            </div>
            <SectionCompletenessNotice
              sectionLabel="Area deprivation"
              completeness={deprivationCompleteness}
            />

            {deprivation ? (
              <>
                <DeprivationGauge decile={deprivation.imdDecile} />

                <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 2xl:grid-cols-5">
                  <StatCard
                    label={<GlossaryTerm term="imd">IMD Decile</GlossaryTerm>}
                    value={`${deprivation.imdDecile}`}
                    className="p-3"
                  />
                  <StatCard
                    label={<GlossaryTerm term="imd">IMD Rank</GlossaryTerm>}
                    value={deprivation.imdRank.toLocaleString("en-GB")}
                    className="p-3"
                  />
                  <StatCard
                    label={<GlossaryTerm term="imd">IMD Score</GlossaryTerm>}
                    value={deprivation.imdScore.toFixed(3)}
                    className="p-3"
                  />
                  <StatCard
                    label={<GlossaryTerm term="idaci">IDACI Decile</GlossaryTerm>}
                    value={`${deprivation.idaciDecile}`}
                    className="p-3"
                  />
                  <StatCard
                    label={<GlossaryTerm term="idaci">IDACI Score</GlossaryTerm>}
                    value={deprivation.idaciScore.toFixed(3)}
                    className="p-3"
                  />
                </div>

                <p className="text-sm text-secondary">
                  {deprivationContextLabel(deprivation.imdDecile)}
                </p>
                <p className="text-xs text-disabled">
                  Source: {deprivation.sourceRelease} &middot;{" "}
                  <GlossaryTerm term="lsoa">{deprivation.lsoaCode}</GlossaryTerm>
                </p>
              </>
            ) : (
              <MetricUnavailable metricLabel="Area deprivation" />
            )}
          </Card>

          {/* Crime */}
          <Card className="space-y-4 p-5 sm:p-6">
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4 text-brand" aria-hidden />
              <h3 className="text-base font-semibold text-primary">
                Area Crime
              </h3>
            </div>
            <SectionCompletenessNotice
              sectionLabel="Area crime"
              completeness={crimeCompleteness}
            />

            {crime ? (
              <>
                <p className="text-xs text-secondary">
                  Within {crime.radiusMiles} mile radius
                </p>

                <StatCard
                  label={`Total incidents (${crime.latestMonth})`}
                  value={crime.totalIncidents.toLocaleString("en-GB")}
                  className="p-3"
                />

                {crime.totalIncidents === 0 ? (
                  <p className="text-sm text-secondary">
                    No incidents were recorded within this radius for the latest available month.
                  </p>
                ) : crime.categories.length > 0 ? (
                  <div className="space-y-2">
                    {/* Show top 3 always, rest behind toggle */}
                    {crime.categories
                      .slice(0, crimeExpanded ? undefined : 3)
                      .map((category) => (
                        <div
                          key={category.category}
                          className="flex items-center justify-between rounded-md border border-border-subtle/60 bg-surface/50 px-3 py-2 transition-colors duration-fast hover:border-border-subtle hover:bg-surface/70"
                        >
                          <span className="text-sm text-primary">
                            {category.category}
                          </span>
                          <span className="text-sm font-medium text-secondary">
                            {category.incidentCount.toLocaleString("en-GB")}
                          </span>
                        </div>
                      ))}

                    {crime.categories.length > 3 ? (
                      <button
                        type="button"
                        className="flex w-full items-center justify-center gap-1 rounded-md border border-border-subtle/40 py-2 text-xs font-medium text-secondary transition-colors hover:bg-surface/80 hover:text-primary"
                        onClick={() => setCrimeExpanded((prev) => !prev)}
                      >
                        {crimeExpanded ? (
                          <>
                            <ChevronUp className="h-3 w-3" aria-hidden />
                            Show less
                          </>
                        ) : (
                          <>
                            <ChevronDown className="h-3 w-3" aria-hidden />
                            Show {crime.categories.length - 3} more categories
                          </>
                        )}
                      </button>
                    ) : null}
                  </div>
                ) : (
                  <MetricUnavailable metricLabel="Crime category breakdown" />
                )}
              </>
            ) : (
              <MetricUnavailable metricLabel="Area crime context" />
            )}
          </Card>
        </div>
      )}
    </section>
  );
}
