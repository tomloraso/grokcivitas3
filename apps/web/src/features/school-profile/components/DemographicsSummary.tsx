import { GlossaryTerm } from "../../../components/data/GlossaryTerm";
import { MetricGrid } from "../../../components/data/MetricGrid";
import { MetricUnavailable } from "../../../components/data/MetricUnavailable";
import { StatCard } from "../../../components/data/StatCard";
import { SectionCompletenessNotice } from "./SectionCompletenessNotice";
import type { DemographicsVM, SectionCompletenessVM } from "../types";

interface DemographicsSummaryProps {
  demographics: DemographicsVM | null;
  completeness: SectionCompletenessVM;
}

/**
 * Map from metric key to glossary term key for acronym tooltips.
 * Only metrics whose labels are acronyms need glossary entries.
 */
const METRIC_GLOSSARY_KEYS: Record<string, string> = {
  fsm_pct: "fsm",
  sen_pct: "sen",
  ehcp_pct: "ehcp",
  eal_pct: "eal"
};

export function DemographicsSummary({
  demographics,
  completeness
}: DemographicsSummaryProps): JSX.Element {
  if (!demographics) {
    return (
      <section aria-labelledby="demographics-heading" className="panel-surface rounded-lg space-y-5 p-5 sm:p-6">
        <div className="flex items-baseline justify-between gap-3">
          <h2
            id="demographics-heading"
            className="flex items-center gap-2 text-lg font-semibold text-primary sm:text-xl"
          >
            <span className="inline-block h-5 w-[3px] rounded-full bg-brand" aria-hidden />
            Demographics
          </h2>
        </div>
        <SectionCompletenessNotice sectionLabel="Demographics" completeness={completeness} />
        <MetricUnavailable metricLabel="Demographics" />
      </section>
    );
  }

  return (
    <section aria-labelledby="demographics-heading" className="panel-surface rounded-lg space-y-5 p-5 sm:p-6">
      <div className="flex items-baseline justify-between gap-3">
        <h2
          id="demographics-heading"
          className="flex items-center gap-2 text-lg font-semibold text-primary sm:text-xl"
        >
          <span className="inline-block h-5 w-[3px] rounded-full bg-brand" aria-hidden />
          Demographics
        </h2>
        <span className="text-xs text-secondary" style={{ opacity: "var(--text-opacity-muted)" }}>
          {demographics.academicYear}
        </span>
      </div>
      <SectionCompletenessNotice sectionLabel="Demographics" completeness={completeness} />

      <MetricGrid columns={3}>
        {demographics.metrics
          .filter((m) => m.value !== null)
          .map((metric) => {
            const glossaryKey = METRIC_GLOSSARY_KEYS[metric.metricKey];
            const label = glossaryKey ? (
              <GlossaryTerm term={glossaryKey}>{metric.label}</GlossaryTerm>
            ) : (
              metric.label
            );

            return (
              <StatCard
                key={metric.metricKey}
                label={label}
                value={metric.value!}
              />
            );
          })}
      </MetricGrid>
    </section>
  );
}
