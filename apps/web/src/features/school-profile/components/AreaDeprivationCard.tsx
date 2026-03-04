import { GlossaryTerm } from "../../../components/data/GlossaryTerm";
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
    return "This area has higher levels of deprivation (1 is most deprived, 10 is least).";
  }
  if (decile >= 9) {
    return "This area has lower levels of deprivation (1 is most deprived, 10 is least).";
  }
  return "This area has mid-range deprivation levels (1 is most deprived, 10 is least).";
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
            <StatCard
              label={<GlossaryTerm term="imd">IMD Decile</GlossaryTerm>}
              value={`${deprivation.imdDecile}`}
            />
            <StatCard
              label={<GlossaryTerm term="idaci">IDACI Decile</GlossaryTerm>}
              value={`${deprivation.idaciDecile}`}
            />
            <StatCard
              label={<GlossaryTerm term="idaci">IDACI Score</GlossaryTerm>}
              value={deprivation.idaciScore.toFixed(3)}
            />
          </MetricGrid>

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
  );
}
