import { Calendar, FileCheck } from "lucide-react";

import { MetricUnavailable } from "../../../components/data/MetricUnavailable";
import { RatingBadge } from "../../../components/data/RatingBadge";
import { Card } from "../../../components/ui/Card";
import { SectionCompletenessNotice } from "./SectionCompletenessNotice";
import type { OfstedVM, SectionCompletenessVM } from "../types";

interface OfstedHeadlineCardProps {
  ofsted: OfstedVM | null;
  completeness: SectionCompletenessVM;
}

export function OfstedHeadlineCard({ ofsted, completeness }: OfstedHeadlineCardProps): JSX.Element {
  if (!ofsted) {
    return (
      <Card className="space-y-4 p-5 sm:p-6">
        <p className="text-xs font-medium uppercase tracking-[0.08em] text-secondary">Ofsted Rating</p>
        <SectionCompletenessNotice sectionLabel="Ofsted rating" completeness={completeness} />
        <MetricUnavailable metricLabel="Ofsted rating" />
      </Card>
    );
  }

  const isUngraded = !ofsted.isGraded;

  return (
    <Card className="space-y-5 p-5 sm:p-6">
      <SectionCompletenessNotice sectionLabel="Ofsted rating" completeness={completeness} />
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1">
          <p className="text-xs font-medium uppercase tracking-[0.08em] text-secondary">
            Ofsted Rating
          </p>
          <RatingBadge
            ratingCode={ofsted.ratingCode}
            label={ofsted.ratingLabel}
            isUngraded={isUngraded}
            className="text-sm"
          />
        </div>

        {/* Graded / ungraded indicator */}
        <span className="inline-flex items-center gap-1 rounded-md bg-surface/60 px-2 py-1 text-xs text-secondary">
          <FileCheck className="h-3 w-3" aria-hidden />
          {isUngraded ? "Ungraded" : "Graded"}
        </span>
      </div>

      {/* Dates */}
      <div className="flex flex-wrap gap-x-6 gap-y-2 border-t border-border-subtle/50 pt-3 text-sm text-secondary">
        {ofsted.inspectionDate ? (
          <span className="inline-flex items-center gap-1.5">
            <Calendar className="h-3.5 w-3.5 text-disabled" aria-hidden />
            Inspected: {ofsted.inspectionDate}
          </span>
        ) : null}
        {ofsted.publicationDate ? (
          <span className="inline-flex items-center gap-1.5">
            <Calendar className="h-3.5 w-3.5 text-disabled" aria-hidden />
            Published: {ofsted.publicationDate}
          </span>
        ) : null}
      </div>

      {/* Ungraded outcome detail */}
      {isUngraded && ofsted.ungradedOutcome ? (
        <p className="text-sm text-secondary">
          Outcome: <span className="font-medium text-primary">{ofsted.ungradedOutcome}</span>
        </p>
      ) : null}
    </Card>
  );
}
