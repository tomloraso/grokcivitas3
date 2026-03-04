import { MetricGrid } from "../../../components/data/MetricGrid";
import { MetricUnavailable } from "../../../components/data/MetricUnavailable";
import { StatCard } from "../../../components/data/StatCard";
import { Card } from "../../../components/ui/Card";
import { SectionCompletenessNotice } from "./SectionCompletenessNotice";
import type { AreaContextVM, SectionCompletenessVM } from "../types";

interface AreaDeprivationCardProps {
  areaContext: AreaContextVM;
  completeness: SectionCompletenessVM;
}

function deprivationContextLabel(decile: number): string {
  if (decile <= 2) {
    return "Higher deprivation context (1 is most deprived).";
  }
  if (decile >= 9) {
    return "Lower deprivation context (10 is least deprived).";
  }
  return "Mid-range deprivation context (1 most deprived, 10 least deprived).";
}

export function AreaDeprivationCard({
  areaContext,
  completeness
}: AreaDeprivationCardProps): JSX.Element {
  const deprivation =
    areaContext.coverage.hasDeprivation && areaContext.deprivation
      ? areaContext.deprivation
      : null;

  return (
    <Card className="space-y-5 p-5 sm:p-6">
      <h2 className="text-lg font-semibold text-primary sm:text-xl">Area Deprivation</h2>
      <SectionCompletenessNotice sectionLabel="Area deprivation" completeness={completeness} />

      {deprivation ? (
        <>
          <MetricGrid columns={3}>
            <StatCard label="IMD Decile" value={`${deprivation.imdDecile}`} />
            <StatCard label="IDACI Decile" value={`${deprivation.idaciDecile}`} />
            <StatCard
              label="IDACI Score"
              value={deprivation.idaciScore.toFixed(3)}
            />
          </MetricGrid>

          <p className="text-sm text-secondary">
            {deprivationContextLabel(deprivation.imdDecile)}
          </p>
          <p className="text-xs text-secondary">
            Source: {deprivation.sourceRelease} ({deprivation.lsoaCode})
          </p>
        </>
      ) : (
        <MetricUnavailable metricLabel="Area deprivation context" />
      )}
    </Card>
  );
}
