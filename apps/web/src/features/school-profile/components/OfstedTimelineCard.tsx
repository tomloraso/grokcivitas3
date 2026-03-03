import { CalendarDays, Clock3 } from "lucide-react";

import { MetricUnavailable } from "../../../components/data/MetricUnavailable";
import { Badge } from "../../../components/ui/Badge";
import { Card } from "../../../components/ui/Card";
import type { OfstedTimelineVM } from "../types";

interface OfstedTimelineCardProps {
  timeline: OfstedTimelineVM;
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

export function OfstedTimelineCard({ timeline }: OfstedTimelineCardProps): JSX.Element {
  return (
    <Card className="space-y-5 p-5 sm:p-6">
      <div className="space-y-2">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-lg font-semibold text-primary sm:text-xl">Ofsted Timeline</h2>
          <Badge variant="outline" className="text-xs">
            {timeline.coverage.eventsCount} events
          </Badge>
        </div>

        {timeline.coverage.isPartialHistory ? (
          <p className="text-sm text-secondary">
            Timeline history is partial for this school.
          </p>
        ) : null}

        {timeline.coverage.earliestEventDate ? (
          <p className="text-xs text-secondary">
            Coverage: {timeline.coverage.earliestEventDate}
            {timeline.coverage.latestEventDate
              ? ` - ${timeline.coverage.latestEventDate}`
              : ""}
          </p>
        ) : null}
      </div>

      {timeline.events.length === 0 ? (
        <MetricUnavailable metricLabel="Ofsted timeline events" />
      ) : (
        <ol className="space-y-3">
          {timeline.events.map((event) => (
            <li
              key={event.inspectionNumber}
              className="rounded-lg border border-border-subtle/60 bg-surface/50 p-3"
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="space-y-1">
                  <p className="inline-flex items-center gap-1.5 text-sm font-medium text-primary">
                    <CalendarDays className="h-3.5 w-3.5 text-disabled" aria-hidden />
                    <span>{event.inspectionDate}</span>
                  </p>
                  <p className="text-xs text-secondary">{event.inspectionType}</p>
                </div>

                <Badge variant={event.outcomeLabel ? "info" : "outline"} className="text-xs">
                  {outcomeLabel(event)}
                </Badge>
              </div>

              {event.publicationDate ? (
                <p className="mt-2 inline-flex items-center gap-1.5 text-xs text-secondary">
                  <Clock3 className="h-3.5 w-3.5 text-disabled" aria-hidden />
                  Published: {event.publicationDate}
                </p>
              ) : null}
            </li>
          ))}
        </ol>
      )}
    </Card>
  );
}
