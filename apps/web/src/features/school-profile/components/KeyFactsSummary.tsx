import { GlossaryTerm } from "../../../components/data/GlossaryTerm";
import { RatingBadge } from "../../../components/data/RatingBadge";
import { Card } from "../../../components/ui/Card";
import type { AreaContextVM, DemographicsVM, OfstedVM } from "../types";

interface KeyFactsSummaryProps {
  ofsted: OfstedVM | null;
  demographics: DemographicsVM | null;
  areaContext: AreaContextVM;
}

/**
 * Prominent "Key facts" block shown at the top of the school profile.
 * Surfaces the most important at-a-glance signals so parents
 * don't have to scan the full page for headline information.
 */
export function KeyFactsSummary({
  ofsted,
  demographics,
  areaContext
}: KeyFactsSummaryProps): JSX.Element {
  const disadvantagedMetric = demographics?.metrics.find(
    (m) => m.metricKey === "disadvantaged_pct"
  );

  const facts: { label: React.ReactNode; value: React.ReactNode }[] = [];

  // Ofsted rating
  if (ofsted) {
    facts.push({
      label: <GlossaryTerm term="ofsted">Ofsted</GlossaryTerm>,
      value: (
        <RatingBadge
          ratingCode={ofsted.ratingCode}
          label={ofsted.ratingLabel}
          isUngraded={!ofsted.isGraded}
        />
      )
    });
  }

  // Academic year
  if (demographics) {
    facts.push({
      label: "Data year",
      value: (
        <span className="text-sm font-medium text-primary">
          {demographics.academicYear}
        </span>
      )
    });
  }

  // Headline disadvantaged %
  if (disadvantagedMetric?.value) {
    facts.push({
      label: "Disadvantaged pupils",
      value: (
        <span className="text-sm font-medium text-primary">
          {disadvantagedMetric.value}
        </span>
      )
    });
  }

  // Area deprivation
  if (areaContext.deprivation) {
    facts.push({
      label: <GlossaryTerm term="imd">Deprivation decile</GlossaryTerm>,
      value: (
        <span className="text-sm font-medium text-primary">
          {areaContext.deprivation.imdDecile} of 10
        </span>
      )
    });
  }

  if (facts.length === 0) {
    return <></>;
  }

  return (
    <Card
      className="border-brand/15 bg-brand/[0.03] p-4 sm:p-5"
      role="region"
      aria-label="Key facts"
    >
      <h2 className="mb-3 text-xs font-medium uppercase tracking-[0.08em] text-secondary">
        Key facts
      </h2>
      <div className="flex flex-wrap items-center gap-x-6 gap-y-3">
        {facts.map((fact, i) => (
          <div
            key={i}
            className="flex items-center gap-2 text-sm text-secondary"
          >
            <span className="text-xs text-disabled">{fact.label}</span>
            {fact.value}
          </div>
        ))}
      </div>
    </Card>
  );
}
