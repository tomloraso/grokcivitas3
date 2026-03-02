import { lazy, Suspense } from "react";

import { LoadingSkeleton } from "../ui/LoadingSkeleton";
import type { MapMarker } from "./MapPanel";

const MapPanelLeaflet = lazy(async () => import("./MapPanelLeaflet"));

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
  return (
    <div className={className ?? "h-full w-full"}>
      {center ? (
        <Suspense fallback={<LoadingSkeleton lines={5} className="m-4" />}>
          <MapPanelLeaflet center={center} markers={markers} />
        </Suspense>
      ) : (
        <div className="grid h-full place-items-center bg-surface/80 p-6 text-center">
          <p className="max-w-sm text-sm text-secondary">
            Search results will appear here once a postcode is resolved.
          </p>
        </div>
      )}
    </div>
  );
}
