import { CalendarDays, Clock3 } from "lucide-react";

import { DataStatusBadge } from "../../../components/data/DataStatusBadge";
import { GlossaryTerm } from "../../../components/data/GlossaryTerm";
import { MetricUnavailable } from "../../../components/data/MetricUnavailable";
import { Badge } from "../../../components/ui/Badge";
import { SectionCompletenessNotice } from "./SectionCompletenessNotice";
import type { OfstedTimelineVM, SectionCompletenessVM } from "../types";

interface OfstedTimelineCardProps {
  timeline: OfstedTimelineVM;
  completeness: SectionCompletenessVM;
}

function outcomeLabel(event: OfstedTimelineVM["events"][number]): string {
  if (event.outcomeLabel) {
    return event.outcomeLabel;
  }
  if (event.headlineOutcome) {
    return event.headlineOutcome;
  }
  return "Outcome not published";
}

/** Map raw inspection-type strings to glossary keys */
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

export function OfstedTimelineCard({ timeline, completeness }: OfstedTimelineCardProps): JSX.Element {
  return (
    <section aria-labelledby="inspection-heading" className="panel-surface rounded-lg space-y-5 p-5 sm:p-6">
      <div className="space-y-2">
        <div className="flex items-center justify-between gap-3">
          <h2 id="inspection-heading" className="flex items-center gap-2 text-lg font-semibold text-primary sm:text-xl">
            <span className="inline-block h-5 w-[3px] rounded-full bg-brand" aria-hidden />
            Inspection History
          </h2>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              {timeline.coverage.eventsCount} {timeline.coverage.eventsCount === 1 ? "event" : "events"}
            </Badge>
            <DataStatusBadge status={completeness.status} />
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
      </div>
      <SectionCompletenessNotice sectionLabel="Ofsted timeline" completeness={completeness} />

      {timeline.events.length === 0 ? (
        <MetricUnavailable metricLabel="Ofsted timeline events" />
      ) : (
        <ol className="relative ml-3">
          {/* Vertical connector line */}
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
              <li
                key={event.inspectionNumber}
                className="relative pb-5 pl-7 last:pb-0"
              >
                {/* Timeline node dot */}
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

                    <Badge
                      variant={hasOutcome ? "info" : "outline"}
                      className="text-xs"
                    >
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
    </section>
  );
}
