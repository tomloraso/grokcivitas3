import { useState } from "react";

import { MetricUnavailable } from "../../../components/data/MetricUnavailable";
import { Sparkline } from "../../../components/data/Sparkline";
import { TrendIndicator } from "../../../components/data/TrendIndicator";
import { StatCard } from "../../../components/ui/stat-card";
import { cn } from "../../../shared/utils/cn";
import {
  formatMetricValue,
  getMetricCatalogEntry
} from "../metricCatalog";
import { siteConfig } from "../../../shared/config/site";
import { SectionCompletenessNotice } from "./SectionCompletenessNotice";
import type {
  SchoolDestinationStageLatestVM,
  SchoolDestinationsVM,
  SectionCompletenessVM,
  TrendSeriesVM,
  TrendsVM
} from "../types";

/* ------------------------------------------------------------------ */
/* Types                                                               */
/* ------------------------------------------------------------------ */

interface SchoolDestinationsSectionProps {
  destinations: SchoolDestinationsVM | null;
  trends: TrendsVM | null;
  completeness: SectionCompletenessVM;
  trendsCompleteness: SectionCompletenessVM;
}

interface DestinationSegment {
  key: string;
  label: string;
  value: number;
  color: string;
}

/* ------------------------------------------------------------------ */
/* Chart colour palette (solid hex, per design-system.md)              */
/* ------------------------------------------------------------------ */

const DESTINATION_COLORS = {
  education: "#2dd4bf",      // teal-400
  apprenticeship: "#38bdf8", // sky-400
  employment: "#a78bfa",     // violet-400
  notSustained: "#9ca3af",   // gray-400
  unknown: "#4b5563",        // gray-600
} as const;

const EDUCATION_BREAKDOWN_COLORS = [
  "#2dd4bf", // teal-400
  "#0d9488", // teal-600
  "#38bdf8", // sky-400
  "#0284c7", // sky-600
] as const;

/* ------------------------------------------------------------------ */
/* Metric definitions per stage                                        */
/* ------------------------------------------------------------------ */

interface DestinationMetricDef {
  metricKey: string;
  value: (stage: SchoolDestinationStageLatestVM) => number | null;
  colorKey?: keyof typeof DESTINATION_COLORS;
}

const KS4_BREAKDOWN_METRICS: DestinationMetricDef[] = [
  { metricKey: "ks4_education_pct", value: (s) => s.educationPct, colorKey: "education" },
  { metricKey: "ks4_apprenticeship_pct", value: (s) => s.apprenticeshipPct, colorKey: "apprenticeship" },
  { metricKey: "ks4_employment_pct", value: (s) => s.employmentPct, colorKey: "employment" },
  { metricKey: "ks4_not_sustained_pct", value: (s) => s.notSustainedPct, colorKey: "notSustained" },
  { metricKey: "ks4_activity_unknown_pct", value: (s) => s.activityUnknownPct, colorKey: "unknown" },
];

const STUDY_16_18_BREAKDOWN_METRICS: DestinationMetricDef[] = [
  { metricKey: "study_16_18_education_pct", value: (s) => s.educationPct, colorKey: "education" },
  { metricKey: "study_16_18_apprenticeship_pct", value: (s) => s.apprenticeshipPct, colorKey: "apprenticeship" },
  { metricKey: "study_16_18_employment_pct", value: (s) => s.employmentPct, colorKey: "employment" },
  { metricKey: "study_16_18_not_sustained_pct", value: (s) => s.notSustainedPct, colorKey: "notSustained" },
  { metricKey: "study_16_18_activity_unknown_pct", value: (s) => s.activityUnknownPct, colorKey: "unknown" },
];

interface EducationBreakdownDef {
  metricKey: string;
  value: (stage: SchoolDestinationStageLatestVM) => number | null;
}

const KS4_EDUCATION_BREAKDOWN: EducationBreakdownDef[] = [
  { metricKey: "ks4_fe_pct", value: (s) => s.fePct },
  { metricKey: "ks4_other_education_pct", value: (s) => s.otherEducationPct },
  { metricKey: "ks4_school_sixth_form_pct", value: (s) => s.schoolSixthFormPct },
  { metricKey: "ks4_sixth_form_college_pct", value: (s) => s.sixthFormCollegePct },
];

const STUDY_16_18_EDUCATION_BREAKDOWN: EducationBreakdownDef[] = [
  { metricKey: "study_16_18_fe_pct", value: (s) => s.fePct },
  { metricKey: "study_16_18_other_education_pct", value: (s) => s.otherEducationPct },
  { metricKey: "study_16_18_higher_education_pct", value: (s) => s.higherEducationPct },
];

/* ------------------------------------------------------------------ */
/* Helpers                                                             */
/* ------------------------------------------------------------------ */

function buildSegments(
  metrics: DestinationMetricDef[],
  stage: SchoolDestinationStageLatestVM,
): DestinationSegment[] {
  return metrics.flatMap(({ metricKey, value, colorKey }) => {
    const raw = value(stage);
    if (raw === null || raw === 0) return [];
    const catalog = getMetricCatalogEntry(metricKey);
    return [{
      key: metricKey,
      label: catalog?.label ?? metricKey,
      value: raw,
      color: colorKey ? DESTINATION_COLORS[colorKey] : "#9ca3af",
    }];
  });
}

function renderTrendFooter(series: TrendSeriesVM | undefined) {
  if (!series || series.latestDelta === null) return null;

  const sparkData = series.points
    .map((p) => p.value)
    .filter((v): v is number => v !== null);
  const period = sparkData.length > 1 ? `${sparkData.length}-yr trend` : undefined;

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
        delta={series.latestDelta}
        direction={series.latestDirection ?? undefined}
        unit="%"
        period={period}
      />
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Stacked Bar + Legend (design-system.md pattern)                      */
/* ------------------------------------------------------------------ */

function DestinationBar({
  segments,
  hoveredKey,
  onHover,
}: {
  segments: DestinationSegment[];
  hoveredKey: string | null;
  onHover: (key: string | null) => void;
}) {
  return (
    <div
      className="flex h-3 w-full overflow-hidden rounded-full"
      role="img"
      aria-label="Destination proportions bar"
    >
      {segments.map((seg, i) => {
        const isHovered = hoveredKey === seg.key;
        const isFaded = hoveredKey !== null && !isHovered;
        return (
          <div
            key={seg.key}
            className="transition-opacity duration-fast"
            style={{
              width: `${seg.value}%`,
              minWidth: seg.value > 0 ? 2 : 0,
              backgroundColor: seg.color,
              opacity: isFaded ? 0.3 : 1,
              borderRight:
                i < segments.length - 1
                  ? "1px solid var(--color-bg-surface)"
                  : undefined,
            }}
            onMouseEnter={() => onHover(seg.key)}
            onMouseLeave={() => onHover(null)}
          />
        );
      })}
    </div>
  );
}

function DestinationLegend({
  segments,
  hoveredKey,
  onHover,
  trendLookup,
}: {
  segments: DestinationSegment[];
  hoveredKey: string | null;
  onHover: (key: string | null) => void;
  trendLookup: Map<string, TrendSeriesVM>;
}) {
  return (
    <div className="grid grid-cols-1 gap-0.5 sm:grid-cols-2">
      {segments.map((seg) => {
        const isHovered = hoveredKey === seg.key;
        const isFaded = hoveredKey !== null && !isHovered;
        const series = trendLookup.get(seg.key);
        const hasTrend = series && series.latestDelta !== null;

        return (
          <div
            key={seg.key}
            className={cn(
              "flex items-center gap-2 rounded px-2 py-1.5 text-sm transition-all duration-150",
              isHovered && "bg-surface/50",
              isFaded && "opacity-40"
            )}
            onMouseEnter={() => onHover(seg.key)}
            onMouseLeave={() => onHover(null)}
          >
            <span
              className="inline-block h-2.5 w-2.5 shrink-0 rounded-full"
              style={{ backgroundColor: seg.color }}
              aria-hidden
            />
            <span className="truncate text-secondary">{seg.label}</span>
            <span className="ml-auto flex shrink-0 items-center gap-2">
              <span className="tabular-nums font-medium text-primary">
                {formatMetricValue(seg.value, "percent") ?? "—"}
              </span>
              {hasTrend ? (
                <TrendIndicator
                  delta={series.latestDelta!}
                  direction={series.latestDirection ?? undefined}
                  unit="%"
                />
              ) : null}
            </span>
          </div>
        );
      })}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Education sub-breakdown (legend-style list)                         */
/* ------------------------------------------------------------------ */

function EducationBreakdownList({
  defs,
  stage,
}: {
  defs: EducationBreakdownDef[];
  stage: SchoolDestinationStageLatestVM;
}) {
  const items = defs.flatMap(({ metricKey, value }) => {
    const raw = value(stage);
    if (raw === null) return [];
    const catalog = getMetricCatalogEntry(metricKey);
    return [{ key: metricKey, label: catalog?.label ?? metricKey, value: raw }];
  });

  if (items.length === 0) return null;

  return (
    <div className="space-y-2">
      <h4 className="text-sm font-medium text-secondary">Education Breakdown</h4>
      <div className="grid grid-cols-1 gap-0.5 sm:grid-cols-2">
        {items.map((item, i) => (
          <div
            key={item.key}
            className="flex items-center gap-2 rounded px-2 py-1.5 text-sm"
          >
            <span
              className="inline-block h-2.5 w-2.5 shrink-0 rounded-full"
              style={{ backgroundColor: EDUCATION_BREAKDOWN_COLORS[i % EDUCATION_BREAKDOWN_COLORS.length] }}
              aria-hidden
            />
            <span className="truncate text-secondary">{item.label}</span>
            <span className="ml-auto shrink-0 tabular-nums font-medium text-primary">
              {formatMetricValue(item.value, "percent") ?? "—"}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Stage block                                                         */
/* ------------------------------------------------------------------ */

function StageBlock({
  title,
  description,
  stage,
  trendLookup,
  overallMetricKey,
  breakdownMetrics,
  educationBreakdownDefs,
}: {
  title: string;
  description: string;
  stage: SchoolDestinationStageLatestVM;
  trendLookup: Map<string, TrendSeriesVM>;
  overallMetricKey: string;
  breakdownMetrics: DestinationMetricDef[];
  educationBreakdownDefs: EducationBreakdownDef[];
}): JSX.Element {
  const [hoveredKey, setHoveredKey] = useState<string | null>(null);
  const segments = buildSegments(breakdownMetrics, stage);
  const overallCatalog = getMetricCatalogEntry(overallMetricKey);
  const cohortLabel = formatMetricValue(stage.cohortCount, "count");
  const qualificationLabel = [stage.qualificationGroup, stage.qualificationLevel]
    .filter((v): v is string => Boolean(v))
    .join(" — ");

  return (
    <div className="space-y-4 rounded-lg border border-border-subtle/50 bg-surface/30 p-4 sm:space-y-5 sm:p-5">
      {/* Stage header */}
      <div className="space-y-1">
        <div className="flex flex-wrap items-baseline justify-between gap-3">
          <h3 className="text-base font-semibold text-primary">{title}</h3>
          <div className="flex flex-wrap items-center gap-2 text-xs text-secondary">
            <span>{stage.academicYear}</span>
            {cohortLabel ? <span>{cohortLabel} pupils</span> : null}
            {qualificationLabel ? <span>{qualificationLabel}</span> : null}
          </div>
        </div>
        <p className="text-sm text-secondary">{description}</p>
      </div>

      {/* Hero: overall sustained % */}
      {stage.overallPct !== null && overallCatalog ? (
        <StatCard
          label={overallCatalog.label}
          description={overallCatalog.description}
          value={formatMetricValue(stage.overallPct, "percent") ?? "n/a"}
          footer={renderTrendFooter(trendLookup.get(overallMetricKey))}
          variant="hero"
        />
      ) : null}

      {/* Stacked proportion bar + legend */}
      {segments.length > 0 ? (
        <div className="space-y-3">
          <DestinationBar
            segments={segments}
            hoveredKey={hoveredKey}
            onHover={setHoveredKey}
          />
          <DestinationLegend
            segments={segments}
            hoveredKey={hoveredKey}
            onHover={setHoveredKey}
            trendLookup={trendLookup}
          />
        </div>
      ) : (
        <MetricUnavailable metricLabel={`${title} breakdown`} />
      )}

      {/* Education sub-breakdown */}
      <EducationBreakdownList defs={educationBreakdownDefs} stage={stage} />
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Main component                                                      */
/* ------------------------------------------------------------------ */

export function SchoolDestinationsSection({
  destinations,
  trends,
  completeness,
  trendsCompleteness
}: SchoolDestinationsSectionProps): JSX.Element {
  const trendLookup = new Map(
    trends?.series.map((series) => [series.metricKey, series] as const) ?? []
  );
  const yearRange =
    trends && trends.yearsAvailable.length > 1
      ? `${trends.yearsAvailable[0]}–${trends.yearsAvailable[trends.yearsAvailable.length - 1]}`
      : destinations?.ks4?.academicYear ?? destinations?.study16To18?.academicYear ?? null;
  const hasVisibleStage = destinations?.ks4 != null || destinations?.study16To18 != null;

  return (
    <section
      aria-labelledby="leaver-destinations-heading"
      className="panel-surface rounded-lg space-y-4 p-4 sm:space-y-5 sm:p-6"
    >
      <div className="flex items-baseline justify-between gap-3">
        <h2
          id="leaver-destinations-heading"
          className="flex items-center gap-2 text-lg font-semibold text-primary sm:text-xl"
        >
          <span className="inline-block h-5 w-[3px] rounded-full bg-brand" aria-hidden />
          Leaver Destinations
        </h2>
        {yearRange ? <span className="text-xs text-secondary">{yearRange}</span> : null}
      </div>

      <p className="text-sm text-secondary">
        Published sustained destinations after pupils leave the school, broken out by stage where available.
      </p>

      <SectionCompletenessNotice
        sectionLabel="Leaver destinations"
        completeness={completeness}
      />
      {trendsCompleteness.status !== "available" ? (
        <SectionCompletenessNotice
          sectionLabel="Leaver destination trends"
          completeness={trendsCompleteness}
        />
      ) : null}

      {!hasVisibleStage ? (
        <MetricUnavailable metricLabel="School leaver destinations" />
      ) : (
        <div className="space-y-4">
          {destinations?.ks4 ? (
            <StageBlock
              title="KS4 Destinations"
              description="Sustained destinations after pupils complete key stage 4 study."
              stage={destinations.ks4}
              trendLookup={trendLookup}
              overallMetricKey="ks4_overall_pct"
              breakdownMetrics={KS4_BREAKDOWN_METRICS}
              educationBreakdownDefs={KS4_EDUCATION_BREAKDOWN}
            />
          ) : null}

          {destinations?.study16To18 ? (
            <StageBlock
              title="16 to 18 Study Destinations"
              description="Sustained destinations after pupils finish 16 to 18 study programmes."
              stage={destinations.study16To18}
              trendLookup={trendLookup}
              overallMetricKey="study_16_18_overall_pct"
              breakdownMetrics={STUDY_16_18_BREAKDOWN_METRICS}
              educationBreakdownDefs={STUDY_16_18_EDUCATION_BREAKDOWN}
            />
          ) : null}
        </div>
      )}

      {completeness.reasonCode === "unsupported_stage" && destinations?.study16To18 === null ? (
        <div className="rounded-lg border border-border-subtle/60 bg-surface/40 px-4 py-3 text-sm text-secondary">
          16 to 18 study destinations are present in the source data for some schools,
          but this stage is not yet shown in {siteConfig.productName}.
        </div>
      ) : null}
    </section>
  );
}
