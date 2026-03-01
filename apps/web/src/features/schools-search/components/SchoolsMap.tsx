import { useMemo } from "react";

import { MapPanel, type MapMarker } from "../../../components/maps/MapPanel";
import type { SchoolsSearchStatus, SchoolSearchListItem } from "../types";

interface SchoolsMapProps {
  status: SchoolsSearchStatus;
  center: { lat: number; lng: number } | null;
  schools: SchoolSearchListItem[];
}

export function SchoolsMap({ status, center, schools }: SchoolsMapProps): JSX.Element {
  const markers = useMemo<MapMarker[]>(
    () =>
      schools.map((school) => ({
        id: school.urn,
        lat: school.lat,
        lng: school.lng,
        label: school.name,
        distanceMiles: school.distance_miles
      })),
    [schools]
  );

  const mapCenter = status === "success" || status === "empty" ? center : null;

  return <MapPanel title="Nearby schools map" center={mapCenter} markers={markers} />;
}
