import { MapPin, GraduationCap, Building2 } from "lucide-react";

import { Badge } from "../../../components/ui/Badge";
import type { SchoolIdentityVM } from "../types";

interface ProfileHeaderProps {
  school: SchoolIdentityVM;
}

export function ProfileHeader({ school }: ProfileHeaderProps): JSX.Element {
  return (
    <header className="space-y-5 border-b border-border-subtle/50 pb-8">
      {/* School name */}
      <div className="space-y-2">
        <p className="eyebrow">
          School Profile
        </p>
        <h1 className="text-3xl font-bold leading-tight tracking-tight text-primary sm:text-4xl lg:text-5xl">
          {school.name}
        </h1>
      </div>

      {/* Meta badges */}
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="default" className="gap-1.5">
          <GraduationCap className="h-3 w-3" aria-hidden />
          {school.phase}
        </Badge>
        <Badge variant="outline" className="gap-1.5">
          <Building2 className="h-3 w-3" aria-hidden />
          {school.type}
        </Badge>
        <Badge variant="outline" className="gap-1.5">
          <MapPin className="h-3 w-3" aria-hidden />
          {school.postcode}
        </Badge>
      </div>

      {/* Status indicator */}
      {school.status !== "Open" && school.status !== "Unknown" ? (
        <p className="text-sm font-medium text-warning">
          Status: {school.status}
        </p>
      ) : null}
    </header>
  );
}
