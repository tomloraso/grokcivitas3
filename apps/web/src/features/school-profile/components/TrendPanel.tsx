import { GlossaryTerm } from "../../../components/data/GlossaryTerm";
import { Sparkline } from "../../../components/data/Sparkline";
import { TrendIndicator } from "../../../components/data/TrendIndicator";
import { SectionCompletenessNotice } from "./SectionCompletenessNotice";
import type { SectionCompletenessVM, TrendsVM } from "../types";

interface TrendPanelProps {
  trends: TrendsVM | null;
  completeness: SectionCompletenessVM;
}

/**
 * Glossary keys for trend metric acronyms.
 */
const METRIC_GLOSSARY_KEYS: Record<string, string> = {
  sen_pct: "sen",
  ehcp_pct: "ehcp",
  eal_pct: "eal"
};

/**
 * Trends section showing only directional change (sparkline + delta).
 *
 * Current-year values live in Demographics to avoid duplication.
 * This panel is suppressed entirely when fewer than 2 years of
 * data exist, since trends require at least 2 data points.
 */
export function TrendPanel({ trends, completeness }: TrendPanelProps): JSX.Element {
  // Completely unavailable — show notice
  if (!trends) {
    return (
      <section aria-labelledby="trends-heading">
        <div className="mb-5 flex items-baseline justify-between gap-3">
          <h2 id="trends-heading" className="text-lg font-semibold text-primary sm:text-xl">
            Trends
          </h2>
        </div>
        <SectionCompletenessNotice sectionLabel="Trends" completeness={completeness} />
      </section>
    );
  }

  // Suppress when fewer than 2 years — trends aren't meaningful
  if (trends.yearsCount < 2) {
    return <></>;
  }

  // Filter to series that actually have multi-year data with a delta
  const trendableSeries = trends.series.filter(
    (s) => s.points.length >= 2 && s.latestDelta !== null
  );

  if (trendableSeries.length === 0) {
    return <></>;
  }

  return (
    <section aria-labelledby="trends-heading">
      <div className="mb-5 flex items-baseline justify-between gap-3">
        <h2 id="trends-heading" className="text-lg font-semibold text-primary sm:text-xl">
          Trends
        </h2>
        {trends.yearsAvailable.length > 1 ? (
          <span className="text-xs text-secondary" style={{ opacity: "var(--text-opacity-muted)" }}>
            {trends.yearsAvailable[0]} – {trends.yearsAvailable[trends.yearsAvailable.length - 1]}
          </span>
        ) : null}
      </div>
      <SectionCompletenessNotice sectionLabel="Trends" completeness={completeness} />

      <div className="space-y-2">
        {trendableSeries.map((series) => {
          const sparkData = series.points
            .map((p) => p.value)
            .filter((v): v is number => v !== null);

          const glossaryKey = METRIC_GLOSSARY_KEYS[series.metricKey];
          const label = glossaryKey ? (
            <GlossaryTerm term={glossaryKey}>{series.label}</GlossaryTerm>
          ) : (
            series.label
          );

          return (
            <div
              key={series.metricKey}
              className="flex items-center justify-between gap-3 rounded-lg border border-border-subtle/60 bg-surface/50 px-4 py-3"
            >
              <span className="text-sm text-primary">{label}</span>
              <div className="flex items-center gap-3">
                {sparkData.length > 1 ? (
                  <Sparkline
                    data={sparkData}
                    width={72}
                    height={24}
                    aria-label={`${series.label} trend line`}
                  />
                ) : null}
                {series.latestDelta !== null ? (
                  <TrendIndicator
                    delta={series.latestDelta}
                    direction={series.latestDirection ?? undefined}
                  />
                ) : null}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
