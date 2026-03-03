import { useMemo } from "react";

import { type MapMarker } from "../../../components/maps/MapPanel";
import { MapPanelChromeless } from "../../../components/maps/MapPanelChromeless";
import type { SchoolsSearchStatus, SchoolSearchListItem } from "../types";

interface SchoolsMapProps {
  status: SchoolsSearchStatus;
  center: { lat: number; lng: number } | null;
  radiusMiles?: number;
  schools: SchoolSearchListItem[];
  activeSchoolId?: string | null;
  onSchoolHover?: (schoolId: string | null) => void;
}

export function SchoolsMap({
  status,
  center,
  radiusMiles,
  schools,
  activeSchoolId,
  onSchoolHover
}: SchoolsMapProps): JSX.Element {
  const markers = useMemo<MapMarker[]>(
    () =>
      schools.map((school) => ({
        id: school.urn,
        lat: school.lat,
        lng: school.lng,
        label: school.name,
        distanceMiles: school.distance_miles,
        phase: school.phase ?? undefined,
        isHovered: activeSchoolId === school.urn
      })),
    [activeSchoolId, schools]
  );

  const mapCenter = status === "idle" ? null : center;

  return (
    <div className="relative h-full w-full">
      <MapPanelChromeless
        center={mapCenter}
        radiusMiles={radiusMiles}
        markers={markers}
        activeMarkerId={activeSchoolId}
        onMarkerHover={onSchoolHover}
      />
      {status === "loading" && (
        <div
          className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center"
          aria-hidden
        >
          <div className="h-16 w-16 animate-ping rounded-full border-2 border-brand/40" />
        </div>
      )}
    </div>
  );
}
