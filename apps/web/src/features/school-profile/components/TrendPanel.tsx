import { GlossaryTerm } from "../../../components/data/GlossaryTerm";
import { Sparkline } from "../../../components/data/Sparkline";
import { TrendIndicator } from "../../../components/data/TrendIndicator";
import type { SectionCompletenessVM, TrendsVM } from "../types";
import { SectionCompletenessNotice } from "./SectionCompletenessNotice";

interface TrendPanelProps {
  trends: TrendsVM | null;
  completeness: SectionCompletenessVM;
}

const METRIC_GLOSSARY_KEYS: Record<string, string> = {
  sen_pct: "sen",
  ehcp_pct: "ehcp",
  eal_pct: "eal",
};

function TrendPanelShell({
  completeness,
  children,
}: {
  completeness: SectionCompletenessVM;
  children?: JSX.Element;
}): JSX.Element {
  return (
    <section aria-labelledby="trends-heading" className="panel-surface rounded-lg space-y-5 p-5 sm:p-6">
      <div className="flex items-baseline justify-between gap-3">
        <h2 id="trends-heading" className="flex items-center gap-2 text-lg font-semibold text-primary sm:text-xl">
          <span className="inline-block h-5 w-[3px] rounded-full bg-brand" aria-hidden />
          Trends
        </h2>
      </div>
      <SectionCompletenessNotice sectionLabel="Trends" completeness={completeness} />
      {children}
    </section>
  );
}

export function TrendPanel({ trends, completeness }: TrendPanelProps): JSX.Element {
  if (!trends) {
    return <TrendPanelShell completeness={completeness} />;
  }

  // Directional trends need at least two published years.
  if (trends.yearsCount < 2) {
    return <TrendPanelShell completeness={completeness} />;
  }

  const trendableSeries = trends.series.filter((series) => {
    return series.points.length >= 2 && series.latestDelta !== null;
  });
  if (trendableSeries.length === 0) {
    return <TrendPanelShell completeness={completeness} />;
  }

  return (
    <section aria-labelledby="trends-heading" className="panel-surface rounded-lg space-y-5 p-5 sm:p-6">
      <div className="flex items-baseline justify-between gap-3">
        <h2 id="trends-heading" className="flex items-center gap-2 text-lg font-semibold text-primary sm:text-xl">
          <span className="inline-block h-5 w-[3px] rounded-full bg-brand" aria-hidden />
          Trends
        </h2>
        {trends.yearsAvailable.length > 1 ? (
          <span className="text-xs text-secondary" style={{ opacity: "var(--text-opacity-muted)" }}>
            {trends.yearsAvailable[0]} - {trends.yearsAvailable[trends.yearsAvailable.length - 1]}
          </span>
        ) : null}
      </div>
      <SectionCompletenessNotice sectionLabel="Trends" completeness={completeness} />

      <div className="space-y-2">
        {trendableSeries.map((series) => {
          const sparkData = series.points
            .map((point) => point.value)
            .filter((value): value is number => value !== null);
          const glossaryKey = METRIC_GLOSSARY_KEYS[series.metricKey];
          const label = glossaryKey ? (
            <GlossaryTerm term={glossaryKey}>{series.label}</GlossaryTerm>
          ) : (
            series.label
          );

          return (
            <div
              key={series.metricKey}
              className="flex items-center justify-between gap-3 rounded-lg border border-border-subtle/60 bg-surface/50 px-4 py-3 transition-colors duration-fast hover:border-border-subtle hover:bg-surface/70"
            >
              <span className="text-sm text-primary">{label}</span>
              <div className="flex items-center gap-3">
                {sparkData.length > 1 ? (
                  <Sparkline data={sparkData} width={120} height={36} aria-label={`${series.label} trend line`} />
                ) : null}
                {series.latestDelta !== null ? (
                  <TrendIndicator delta={series.latestDelta} direction={series.latestDirection ?? undefined} />
                ) : null}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
