import { Building2, GraduationCap, MapPin, Plus, X } from "lucide-react";
import { Link } from "react-router-dom";

import { Badge } from "../../components/ui/Badge";
import { paths } from "../../shared/routing/paths";
import type { CompareSlot } from "./compareSlots";
import type { CompareSchoolColumnVM } from "./types";

/** Must match CompareAccordionContent column widths */
const LABEL_COL_WIDTH = 200;
const SCHOOL_COL_WIDTH = 180;
const TOTAL_SLOTS = 4;

interface CompareSchoolStripProps {
  slots: CompareSlot[];
  onRemoveSchool: (urn: string) => void;
}

export function CompareSchoolStrip({
  slots,
  onRemoveSchool,
}: CompareSchoolStripProps): JSX.Element {
  const totalMinWidth = LABEL_COL_WIDTH + TOTAL_SLOTS * SCHOOL_COL_WIDTH;
  const filledCount = slots.filter(Boolean).length;

  return (
    <>
      {/* Mobile: 2×2 grid */}
      <div className="sm:hidden">
        <p className="mb-2 text-[10px] font-semibold tracking-[0.04em] text-disabled px-1">
          {filledCount} school{filledCount === 1 ? "" : "s"}
        </p>
        <div className="grid grid-cols-2 gap-2">
          {slots.map((slot, index) => (
            <div key={slot?.urn ?? `empty-${index}`}>
              {slot ? (
                <FilledCard school={slot} onRemove={onRemoveSchool} />
              ) : (
                <GhostCard />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Desktop: horizontal strip aligned with table columns */}
      <div className="hidden sm:block overflow-x-auto snap-x snap-mandatory scroll-smooth">
        <div
          className="flex gap-0"
          style={{ minWidth: totalMinWidth }}
        >
          {/* Spacer matching the metric label column */}
          <div
            className="shrink-0 flex items-end px-4 pb-2"
            style={{ width: LABEL_COL_WIDTH, minWidth: LABEL_COL_WIDTH }}
          >
            <p className="text-[10px] font-semibold tracking-[0.04em] text-disabled">
              {filledCount} school{filledCount === 1 ? "" : "s"}
            </p>
          </div>

          {/* Fixed 4 slots */}
          {slots.map((slot, index) => (
            <div
              key={slot?.urn ?? `empty-${index}`}
              className="snap-start shrink-0 px-1.5"
              style={{ width: SCHOOL_COL_WIDTH, minWidth: SCHOOL_COL_WIDTH }}
            >
              {slot ? (
                <FilledCard school={slot} onRemove={onRemoveSchool} />
              ) : (
                <GhostCard />
              )}
            </div>
          ))}
        </div>
      </div>
    </>
  );
}

/* ------------------------------------------------------------------ */
/* Filled school card                                                  */
/* ------------------------------------------------------------------ */

function FilledCard({
  school,
  onRemove,
}: {
  school: CompareSchoolColumnVM;
  onRemove: (urn: string) => void;
}): JSX.Element {
  return (
    <div className="rounded-lg border border-border-subtle/60 bg-surface/80 p-2 space-y-1.5">
      <div className="flex items-start justify-between gap-1">
        <div className="min-w-0">
          <h3 className="text-xs font-semibold leading-snug text-primary truncate">
            <Link
              to={school.profileHref}
              state={school.profileState}
              className="transition-colors hover:text-brand-hover"
            >
              {school.name}
            </Link>
          </h3>
        </div>
        <button
          type="button"
          className="shrink-0 rounded p-1.5 sm:p-0.5 text-disabled transition-colors hover:bg-surface hover:text-secondary"
          aria-label={`Remove ${school.name} from compare`}
          onClick={() => onRemove(school.urn)}
        >
          <X className="h-3 w-3" />
        </button>
      </div>

      <div className="flex flex-wrap gap-1">
        <Badge variant="default" className="gap-0.5 text-[9px] px-1 py-0">
          <GraduationCap className="h-2.5 w-2.5" aria-hidden />
          {school.phase}
        </Badge>
        <Badge variant="outline" className="gap-0.5 text-[9px] px-1 py-0">
          <Building2 className="h-2.5 w-2.5" aria-hidden />
          {school.type}
        </Badge>
        <Badge variant="outline" className="gap-0.5 text-[9px] px-1 py-0">
          <MapPin className="h-2.5 w-2.5" aria-hidden />
          {school.postcode}
        </Badge>
      </div>

      {school.ageRangeLabel || school.distanceLabel ? (
        <p className="text-[9px] text-disabled leading-tight">
          {[school.ageRangeLabel, school.distanceLabel]
            .filter(Boolean)
            .join(" · ")}
        </p>
      ) : null}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Ghost "Add school" card                                             */
/* ------------------------------------------------------------------ */

function GhostCard(): JSX.Element {
  return (
    <Link
      to={paths.home}
      className="flex h-full min-h-[60px] sm:min-h-[72px] items-center justify-center rounded-lg border border-dashed border-border-subtle/40 bg-surface/20 transition-colors hover:border-brand/30 hover:bg-brand/[0.02]"
    >
      <span className="flex items-center gap-1 text-[10px] font-medium text-disabled">
        <Plus className="h-3 w-3" aria-hidden />
        Add school
      </span>
    </Link>
  );
}


