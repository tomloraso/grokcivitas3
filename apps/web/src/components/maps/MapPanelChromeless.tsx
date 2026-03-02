import { lazy, Suspense, useMemo } from "react";

import { LoadingSkeleton } from "../ui/LoadingSkeleton";
import type { MapMarker } from "./MapPanel";

const MapPanelLeaflet = lazy(async () => import("./MapPanelLeaflet"));

/** Geographic center of England/Wales — used as the landing view */
const UK_DEFAULT_CENTER = { lat: 54.0, lng: -2.5 };

interface MapPanelChromelessProps {
  center: { lat: number; lng: number } | null;
  markers: MapMarker[];
  className?: string;
}

/**
 * Chromeless map variant that renders without the panel header bar and
 * fixed-height constraint. Fills its parent container. Intended for use
 * inside MapOverlayLayout as a full-bleed background.
 */
export function MapPanelChromeless({
  center,
  markers,
  className
}: MapPanelChromelessProps): JSX.Element {
  const mapCenter = useMemo(() => center ?? UK_DEFAULT_CENTER, [center]);

  return (
    <div className={className ?? "h-full w-full"}>
      <Suspense fallback={<LoadingSkeleton lines={5} className="m-4" />}>
        <MapPanelLeaflet center={mapCenter} markers={markers} />
      </Suspense>
    </div>
  );
}
