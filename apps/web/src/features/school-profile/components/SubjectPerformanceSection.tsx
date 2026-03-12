import { useState } from "react";

import { MetricUnavailable } from "../../../components/data/MetricUnavailable";
import { cn } from "../../../shared/utils/cn";
import type {
  SubjectPerformanceGroupVM,
  SubjectPerformanceVM,
  SubjectSummaryVM,
} from "../types";

/* ------------------------------------------------------------------ */
/* Chart colours (solid hex, per design-system.md)                     */
/* ------------------------------------------------------------------ */

const SEGMENT_COLORS = [
  "#2dd4bf", // teal-400
  "#0d9488", // teal-600
  "#38bdf8", // sky-400
  "#0284c7", // sky-600
  "#a78bfa", // violet-400
  "#fbbf24", // amber-400
  "#fb7185", // rose-400
  "#22c55e", // emerald-500
  "#9ca3af", // gray-400
  "#c084fc", // purple-400
  "#f97316", // orange-400
  "#67e8f9", // cyan-300
];

function segmentColor(index: number): string {
  return SEGMENT_COLORS[index % SEGMENT_COLORS.length];
}

/* ------------------------------------------------------------------ */
/* Helpers                                                             */
/* ------------------------------------------------------------------ */

function fmtPct(value: number | null): string {
  if (value === null) return "—";
  return `${value.toFixed(1)}%`;
}

function keyStageLabel(ks: "ks4" | "16_to_18"): string {
  return ks === "ks4" ? "KS4" : "16–18";
}

function qualFamilyLabel(family: string): string {
  const upper = family.toUpperCase();
  if (upper === "GCSE") return "GCSE";
  if (upper === "VOCATIONAL") return "Vocational";
  if (upper === "A LEVEL" || upper === "A-LEVEL") return "A Level";
  return family.charAt(0).toUpperCase() + family.slice(1);
}

/* ------------------------------------------------------------------ */
/* Subject rank table                                                  */
/* ------------------------------------------------------------------ */

function SubjectRankTable({
  title,
  subjects,
  accentColor,
}: {
  title: string;
  subjects: SubjectSummaryVM[];
  accentColor: string;
}): JSX.Element | null {
  if (subjects.length === 0) return null;

  return (
    <div className="space-y-3">
      <h3 className="flex items-center gap-2 text-sm font-semibold text-primary">
        <span
          className="inline-block h-3 w-[3px] rounded-full"
          style={{ backgroundColor: accentColor }}
          aria-hidden
        />
        {title}
      </h3>

      {/* Desktop table */}
      <div className="hidden sm:block overflow-x-auto">
        <table className="w-full table-fixed text-sm">
          <colgroup>
            <col />
            <col className="w-[72px]" />
            <col className="w-[96px]" />
            <col className="w-[72px]" />
          </colgroup>
          <thead>
            <tr className="border-b border-border-subtle/50 text-left text-xs text-disabled">
              <th className="py-2 pr-4 font-medium">Subject</th>
              <th className="py-2 pr-4 font-medium text-right">Entries</th>
              <th className="py-2 pr-4 font-medium text-right">High Grade %</th>
              <th className="py-2 font-medium text-right">Pass %</th>
            </tr>
          </thead>
          <tbody>
            {subjects.map((s) => (
              <tr
                key={`${s.subject}-${s.keyStage}-${s.qualificationFamily}`}
                className="border-b border-border-subtle/30"
              >
                <td className="py-2 pr-4 truncate">
                  <span className="font-medium text-primary">{s.subject}</span>
                  <span className="ml-2 text-xs text-disabled">
                    {keyStageLabel(s.keyStage)} · {qualFamilyLabel(s.qualificationFamily)}
                  </span>
                </td>
                <td className="py-2 pr-4 text-right tabular-nums text-secondary">
                  {s.entriesCountTotal.toLocaleString("en-GB")}
                </td>
                <td className="py-2 pr-4 text-right tabular-nums text-primary font-medium">
                  {fmtPct(s.highGradeSharePct)}
                </td>
                <td className="py-2 text-right tabular-nums text-primary font-medium">
                  {fmtPct(s.passGradeSharePct)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile cards */}
      <div className="space-y-2 sm:hidden">
        {subjects.map((s) => (
          <div
            key={`${s.subject}-${s.keyStage}-${s.qualificationFamily}-m`}
            className="rounded-lg border border-border-subtle/60 bg-surface/50 px-3 py-2.5"
          >
            <div className="flex items-baseline justify-between gap-2">
              <span className="font-medium text-primary">{s.subject}</span>
              <span className="shrink-0 text-xs text-disabled">
                {s.entriesCountTotal.toLocaleString("en-GB")} entries
              </span>
            </div>
            <div className="mt-1.5 flex gap-4 text-xs">
              <span className="text-secondary">
                High grade:{" "}
                <span className="font-medium text-primary tabular-nums">
                  {fmtPct(s.highGradeSharePct)}
                </span>
              </span>
              <span className="text-secondary">
                Pass:{" "}
                <span className="font-medium text-primary tabular-nums">
                  {fmtPct(s.passGradeSharePct)}
                </span>
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Full subject breakdown (stacked bar + expandable table)             */
/* ------------------------------------------------------------------ */

function SubjectBreakdownGroup({
  group,
}: {
  group: SubjectPerformanceGroupVM;
}): JSX.Element {
  const [expanded, setExpanded] = useState(false);
  const sorted = [...group.subjects].sort(
    (a, b) => (b.highGradeSharePct ?? 0) - (a.highGradeSharePct ?? 0)
  );
  const [hoveredKey, setHoveredKey] = useState<string | null>(null);

  const label = `${keyStageLabel(group.keyStage)} ${qualFamilyLabel(group.qualificationFamily)}`;
  const cohortLabel = group.examCohort ? ` · ${group.examCohort}` : "";

  return (
    <div className="space-y-3 rounded-lg border border-border-subtle/50 bg-surface/30 p-4">
      <div className="flex items-baseline justify-between gap-3">
        <h4 className="text-sm font-semibold text-primary">
          {label}
          <span className="ml-2 text-xs font-normal text-disabled">
            {group.academicYear}{cohortLabel} · {sorted.length} subjects
          </span>
        </h4>
        <button
          type="button"
          onClick={() => setExpanded((prev) => !prev)}
          className="text-xs font-medium text-brand transition-colors duration-fast hover:text-brand-hover"
        >
          {expanded ? "Collapse" : "Expand"}
        </button>
      </div>

      {/* Stacked bar showing high-grade % per subject */}
      <div
        className="flex h-3 w-full overflow-hidden rounded-full"
        role="img"
        aria-label={`${label} subject breakdown bar`}
      >
        {sorted.map((s, i) => {
          const pct = s.highGradeSharePct ?? 0;
          // Weight by entries relative to total
          const totalEntries = sorted.reduce((sum, sub) => sum + sub.entriesCountTotal, 0);
          const widthPct = totalEntries > 0 ? (s.entriesCountTotal / totalEntries) * 100 : 0;
          if (widthPct === 0) return null;

          const isHovered = hoveredKey === s.subject;
          const isFaded = hoveredKey !== null && !isHovered;

          return (
            <div
              key={s.subject}
              className="transition-opacity duration-fast"
              title={`${s.subject}: ${fmtPct(pct)} high grade (${s.entriesCountTotal} entries)`}
              style={{
                width: `${widthPct}%`,
                minWidth: widthPct > 0 ? 2 : 0,
                backgroundColor: segmentColor(i),
                opacity: isFaded ? 0.3 : 1,
                borderRight:
                  i < sorted.length - 1
                    ? "1px solid var(--color-bg-surface)"
                    : undefined,
              }}
              onMouseEnter={() => setHoveredKey(s.subject)}
              onMouseLeave={() => setHoveredKey(null)}
            />
          );
        })}
      </div>

      {/* Expanded table */}
      {expanded ? (
        <div className="space-y-1">
          {/* Desktop */}
          <div className="hidden sm:block overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border-subtle/50 text-left text-xs text-disabled">
                  <th className="py-1.5 pr-3 font-medium">Subject</th>
                  <th className="py-1.5 pr-3 font-medium text-right">Entries</th>
                  <th className="py-1.5 pr-3 font-medium text-right">High Grade %</th>
                  <th className="py-1.5 font-medium text-right">Pass %</th>
                </tr>
              </thead>
              <tbody>
                {sorted.map((s, i) => {
                  const isHovered = hoveredKey === s.subject;
                  const isFaded = hoveredKey !== null && !isHovered;
                  return (
                    <tr
                      key={s.subject}
                      className={cn(
                        "border-b border-border-subtle/20 transition-all duration-150",
                        isHovered && "bg-surface/50",
                        isFaded && "opacity-40"
                      )}
                      onMouseEnter={() => setHoveredKey(s.subject)}
                      onMouseLeave={() => setHoveredKey(null)}
                    >
                      <td className="py-1.5 pr-3">
                        <span className="flex items-center gap-2">
                          <span
                            className="inline-block h-2 w-2 shrink-0 rounded-full"
                            style={{ backgroundColor: segmentColor(i) }}
                            aria-hidden
                          />
                          <span className="text-primary">{s.subject}</span>
                        </span>
                      </td>
                      <td className="py-1.5 pr-3 text-right tabular-nums text-secondary">
                        {s.entriesCountTotal.toLocaleString("en-GB")}
                      </td>
                      <td className="py-1.5 pr-3 text-right tabular-nums text-primary font-medium">
                        {fmtPct(s.highGradeSharePct)}
                      </td>
                      <td className="py-1.5 text-right tabular-nums text-primary font-medium">
                        {fmtPct(s.passGradeSharePct)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Mobile */}
          <div className="space-y-1.5 sm:hidden">
            {sorted.map((s, i) => (
              <div
                key={`${s.subject}-m`}
                className="flex items-center gap-2 rounded px-2 py-1.5 text-sm"
              >
                <span
                  className="inline-block h-2 w-2 shrink-0 rounded-full"
                  style={{ backgroundColor: segmentColor(i) }}
                  aria-hidden
                />
                <span className="min-w-0 truncate text-secondary">{s.subject}</span>
                <span className="ml-auto flex shrink-0 gap-3 tabular-nums text-xs">
                  <span className="text-primary font-medium">{fmtPct(s.highGradeSharePct)}</span>
                  <span className="text-disabled">{s.entriesCountTotal}</span>
                </span>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Main component                                                      */
/* ------------------------------------------------------------------ */

export function SubjectPerformanceSection({
  subjectPerformance,
}: {
  subjectPerformance: SubjectPerformanceVM | null;
}): JSX.Element | null {
  if (!subjectPerformance) return null;

  const {
    strongestSubjects,
    weakestSubjects,
    stageBreakdowns,
    latestUpdatedAt,
  } = subjectPerformance;

  const hasContent =
    strongestSubjects.length > 0 ||
    weakestSubjects.length > 0 ||
    stageBreakdowns.length > 0;

  if (!hasContent) return null;

  const academicYear =
    strongestSubjects[0]?.academicYear ??
    weakestSubjects[0]?.academicYear ??
    stageBreakdowns[0]?.academicYear ??
    null;

  return (
    <div className="panel-surface rounded-lg space-y-4 p-4 sm:space-y-5 sm:p-6">
      <div className="flex items-baseline justify-between gap-3">
        <h3 className="flex items-center gap-2 text-lg font-semibold text-primary sm:text-xl">
          <span className="inline-block h-4 w-[3px] rounded-full bg-brand" aria-hidden />
          Subject Results
        </h3>
        <div className="flex items-center gap-2 text-xs text-secondary">
          {academicYear ? <span>{academicYear}</span> : null}
          {latestUpdatedAt ? (
            <span className="text-disabled">
              Updated {new Date(latestUpdatedAt).toLocaleDateString("en-GB", { month: "short", day: "numeric" })}
            </span>
          ) : null}
        </div>
      </div>

      <p className="text-sm text-secondary">
        Per-subject exam results ranked by high-grade share, with full breakdowns by qualification group.
      </p>

      {/* Strongest / Weakest */}
      {strongestSubjects.length > 0 || weakestSubjects.length > 0 ? (
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          <SubjectRankTable
            title="Strongest Subjects"
            subjects={strongestSubjects}
            accentColor="#22c55e"
          />
          <SubjectRankTable
            title="Weakest Subjects"
            subjects={weakestSubjects}
            accentColor="#9ca3af"
          />
        </div>
      ) : null}

      {/* Full breakdowns by qualification group */}
      {stageBreakdowns.length > 0 ? (
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-secondary">All Subjects by Qualification</h4>
          <div className="space-y-3">
            {stageBreakdowns.map((group) => (
              <SubjectBreakdownGroup
                key={`${group.keyStage}-${group.qualificationFamily}`}
                group={group}
              />
            ))}
          </div>
        </div>
      ) : null}

      {!hasContent ? (
        <MetricUnavailable metricLabel="Subject performance" />
      ) : null}
    </div>
  );
}
