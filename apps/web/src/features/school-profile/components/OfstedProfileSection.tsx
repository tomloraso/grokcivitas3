import { Calendar, CalendarDays, Clock3 } from "lucide-react";

import { DataStatusBadge } from "../../../components/data/DataStatusBadge";
import { GlossaryTerm } from "../../../components/data/GlossaryTerm";
import { MetricUnavailable } from "../../../components/data/MetricUnavailable";
import { Badge } from "../../../components/ui/Badge";
import { SectionCompletenessNotice } from "./SectionCompletenessNotice";
import type { OfstedVM, OfstedTimelineVM, SectionCompletenessVM } from "../types";

/* ------------------------------------------------------------------ */
/* Props                                                               */
/* ------------------------------------------------------------------ */

interface OfstedProfileSectionProps {
  ofsted: OfstedVM | null;
  timeline: OfstedTimelineVM;
  ofstedCompleteness: SectionCompletenessVM;
  timelineCompleteness: SectionCompletenessVM;
}

/* ------------------------------------------------------------------ */
/* Colour helpers — shared rating palette                              */
/* ------------------------------------------------------------------ */

const OFSTED_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  "1": { bg: "bg-success/10", text: "text-success", border: "border-l-success" },
  "2": { bg: "bg-info/10", text: "text-info", border: "border-l-info" },
  "3": { bg: "bg-warning/10", text: "text-warning", border: "border-l-warning" },
  "4": { bg: "bg-danger/10", text: "text-danger", border: "border-l-danger" },
};

/* ------------------------------------------------------------------ */
/* Sub-judgement cards — colour-coded                                  */
/* ------------------------------------------------------------------ */

interface SubJudgement {
  key: string;
  label: string;
  code: string | null;
  value: string | null;
}

function SubJudgementCard({ judgement }: { judgement: SubJudgement }): JSX.Element {
  const colors = judgement.code ? OFSTED_COLORS[judgement.code] : null;

  return (
    <div
      className={`rounded-md border border-border-subtle/70 border-l-[3px] px-3 py-2.5 transition-colors ${
        colors
          ? `${colors.bg} ${colors.border}`
          : "border-l-border-subtle bg-surface/60"
      }`}
    >
      <p className="text-[11px] font-medium uppercase tracking-[0.06em] text-disabled">
        {judgement.label}
      </p>
      <p
        className={`mt-0.5 text-sm font-semibold leading-tight ${
          colors?.text ?? "text-secondary"
        }`}
      >
        {judgement.value ?? "Not published"}
      </p>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Timeline helpers (migrated from OfstedTimelineCard)                 */
/* ------------------------------------------------------------------ */

const INSPECTION_TYPE_GLOSSARY: Record<string, string> = {
  "Section 5": "section_5",
  "Section 8": "section_8",
};

function InspectionTypeLabel({ type }: { type: string }): JSX.Element {
  const glossaryKey = INSPECTION_TYPE_GLOSSARY[type];
  if (glossaryKey) {
    return <GlossaryTerm term={glossaryKey}>{type}</GlossaryTerm>;
  }
  return <>{type}</>;
}

function outcomeLabel(event: OfstedTimelineVM["events"][number]): string {
  if (event.outcomeLabel) return event.outcomeLabel;
  if (event.headlineOutcome) return event.headlineOutcome;
  return "Outcome not published";
}

/* ------------------------------------------------------------------ */
/* Component                                                           */
/* ------------------------------------------------------------------ */

export function OfstedProfileSection({
  ofsted,
  timeline,
  ofstedCompleteness,
  timelineCompleteness,
}: OfstedProfileSectionProps): JSX.Element {
  const subJudgements: SubJudgement[] = ofsted
    ? [
        {
          key: "quality",
          label: "Quality of education",
          code: ofsted.qualityOfEducationCode,
          value: ofsted.qualityOfEducationLabel,
        },
        {
          key: "behaviour",
          label: "Behaviour & attitudes",
          code: ofsted.behaviourAndAttitudesCode,
          value: ofsted.behaviourAndAttitudesLabel,
        },
        {
          key: "personal",
          label: "Personal development",
          code: ofsted.personalDevelopmentCode,
          value: ofsted.personalDevelopmentLabel,
        },
        {
          key: "leadership",
          label: "Leadership & management",
          code: ofsted.leadershipAndManagementCode,
          value: ofsted.leadershipAndManagementLabel,
        },
      ]
    : [];

  const hasSubJudgements = subJudgements.some((j) => j.value !== null);

  return (
    <section
      aria-labelledby="ofsted-heading"
      className="panel-surface rounded-lg space-y-6 p-5 sm:p-6"
    >
      {/* ── Section header ─────────────────────── */}
      <div className="space-y-1">
        <h2
          id="ofsted-heading"
          className="flex items-center gap-2 text-lg font-semibold text-primary sm:text-xl"
        >
          <span className="inline-block h-5 w-[3px] rounded-full bg-brand" aria-hidden />
          <GlossaryTerm term="ofsted">Ofsted Profile</GlossaryTerm>
        </h2>
        <p className="text-sm text-secondary">
          Inspection judgements and history from Ofsted.
        </p>
      </div>

      {/* ── Sub-judgements ─────────────────────── */}
      {hasSubJudgements ? (
        <div className="space-y-2">
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-4">
            {subJudgements.map((j) => (
              <SubJudgementCard key={j.key} judgement={j} />
            ))}
          </div>
          {ofsted?.latestOeifInspectionDate ? (
            <p className="text-[11px] text-disabled">
              Sub-judgements from inspection starting {ofsted.latestOeifInspectionDate}
            </p>
          ) : null}
        </div>
      ) : null}

      {/* Ungraded outcome */}
      {ofsted?.ungradedOutcome ? (
        <p className="text-sm text-secondary">
          Outcome:{" "}
          <span className="font-medium text-primary">{ofsted.ungradedOutcome}</span>
          {ofsted.publicationDate ? (
            <span className="ml-3 inline-flex items-center gap-1 text-xs text-disabled">
              <Calendar className="h-3 w-3" aria-hidden />
              Published {ofsted.publicationDate}
            </span>
          ) : null}
        </p>
      ) : null}

      <SectionCompletenessNotice
        sectionLabel="Ofsted judgements"
        completeness={ofstedCompleteness}
      />

      {/* ── Inspection timeline ────────────────── */}
      <div className="space-y-4 border-t border-border-subtle/50 pt-5">
        <div className="flex items-center justify-between gap-3">
          <h3 className="text-base font-semibold text-primary">
            Inspection History
          </h3>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              {timeline.coverage.eventsCount}{" "}
              {timeline.coverage.eventsCount === 1 ? "event" : "events"}
            </Badge>
            <DataStatusBadge status={timelineCompleteness.status} />
          </div>
        </div>

        {timeline.coverage.isPartialHistory ? (
          <p className="text-sm text-secondary">
            This is a partial inspection history. Earlier inspections may not be shown.
          </p>
        ) : null}

        {timeline.coverage.earliestEventDate ? (
          <p className="text-xs text-disabled">
            Covers: {timeline.coverage.earliestEventDate}
            {timeline.coverage.latestEventDate
              ? ` – ${timeline.coverage.latestEventDate}`
              : ""}
          </p>
        ) : null}

        <SectionCompletenessNotice
          sectionLabel="Ofsted timeline"
          completeness={timelineCompleteness}
        />

        {timeline.events.length === 0 ? (
          <MetricUnavailable metricLabel="Ofsted timeline events" />
        ) : (
          <ol className="relative ml-3">
            {timeline.events.length > 1 ? (
              <div
                className="absolute bottom-4 left-0 top-4 w-px bg-border-subtle/80"
                aria-hidden
              />
            ) : null}

            {timeline.events.map((event, index) => {
              const isLatest = index === 0;
              const hasOutcome = Boolean(event.outcomeLabel);

              return (
                <li key={event.inspectionNumber} className="relative pb-5 pl-7 last:pb-0">
                  <div
                    className={`absolute left-0 top-1.5 -translate-x-1/2 rounded-full border-2 ${
                      isLatest
                        ? "h-3 w-3 border-brand bg-brand"
                        : "h-2.5 w-2.5 border-border bg-surface"
                    }`}
                    aria-hidden
                  />

                  <div
                    className={`rounded-lg border p-3 transition-colors ${
                      isLatest
                        ? "border-brand/20 bg-brand/[0.04]"
                        : "border-border-subtle/60 bg-surface/50"
                    }`}
                  >
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <p className="inline-flex items-center gap-1.5 text-sm font-medium text-primary">
                            <CalendarDays className="h-3.5 w-3.5 text-disabled" aria-hidden />
                            <span>{event.inspectionDate}</span>
                          </p>
                          {isLatest ? (
                            <Badge variant="default" className="text-[10px] px-1.5 py-0">
                              Latest
                            </Badge>
                          ) : null}
                        </div>
                        <p className="text-xs text-secondary">
                          <InspectionTypeLabel type={event.inspectionType} />
                        </p>
                      </div>

                      <Badge variant={hasOutcome ? "info" : "outline"} className="text-xs">
                        {outcomeLabel(event)}
                      </Badge>
                    </div>

                    {event.publicationDate ? (
                      <p className="mt-2 inline-flex items-center gap-1.5 text-xs text-secondary">
                        <Clock3 className="h-3.5 w-3.5 text-disabled" aria-hidden />
                        Published: {event.publicationDate}
                      </p>
                    ) : null}
                  </div>
                </li>
              );
            })}
          </ol>
        )}
      </div>
    </section>
  );
}
