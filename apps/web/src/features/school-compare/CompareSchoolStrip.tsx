import { Building2, GraduationCap, MapPin, X } from "lucide-react";
import { Link } from "react-router-dom";

import { Badge } from "../../components/ui/Badge";
import { StatCard } from "../../components/ui/stat-card";
import type { CompareSchoolColumnVM } from "./types";

interface CompareSchoolStripProps {
  schools: CompareSchoolColumnVM[];
  onRemoveSchool: (urn: string) => void;
}

export function CompareSchoolStrip({
  schools,
  onRemoveSchool,
}: CompareSchoolStripProps): JSX.Element {
  return (
    <div className="overflow-x-auto pb-1 snap-x snap-mandatory scroll-smooth">
      <div
        className="grid gap-3"
        style={{
          gridTemplateColumns: `repeat(${schools.length}, minmax(240px, 1fr))`,
          minWidth: `${schools.length * 240}px`,
        }}
      >
        {schools.map((school) => (
          <div
            key={school.urn}
            className="snap-start panel-surface rounded-xl border border-border-subtle/60 bg-surface/90 p-4 space-y-3"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0 space-y-1">
                <p className="font-mono text-[10px] text-disabled">
                  URN {school.urn}
                </p>
                <h3 className="text-base font-semibold leading-snug text-primary">
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
                className="shrink-0 rounded-md p-1 text-disabled transition-colors hover:bg-surface hover:text-secondary"
                aria-label={`Remove ${school.name} from compare`}
                onClick={() => onRemoveSchool(school.urn)}
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="flex flex-wrap gap-1.5">
              <Badge variant="default" className="gap-1 text-[10px]">
                <GraduationCap className="h-3 w-3" aria-hidden />
                {school.phase}
              </Badge>
              <Badge variant="outline" className="gap-1 text-[10px]">
                <Building2 className="h-3 w-3" aria-hidden />
                {school.type}
              </Badge>
              <Badge variant="outline" className="gap-1 text-[10px]">
                <MapPin className="h-3 w-3" aria-hidden />
                {school.postcode}
              </Badge>
            </div>

            {school.ageRangeLabel || school.distanceLabel ? (
              <div className="grid grid-cols-2 gap-2">
                {school.ageRangeLabel ? (
                  <StatCard
                    variant="mini"
                    size="sm"
                    label="Age Range"
                    value={school.ageRangeLabel}
                    valueClassName="text-sm"
                  />
                ) : null}
                {school.distanceLabel ? (
                  <StatCard
                    variant="mini"
                    size="sm"
                    label="Distance"
                    value={school.distanceLabel}
                    valueClassName="text-sm font-mono"
                  />
                ) : null}
              </div>
            ) : null}
          </div>
        ))}
      </div>
    </div>
  );
}
