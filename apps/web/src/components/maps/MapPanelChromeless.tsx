import { lazy, Suspense, useMemo } from "react";

import { LoadingSkeleton } from "../ui/LoadingSkeleton";
import type { MapMarker } from "./MapPanel";
import { MAP_BOUNDS } from "../../shared/maps/map-bounds";

const MapPanelMapLibre = lazy(async () => import("./MapPanelMapLibre"));

interface MapPanelChromelessProps {
  center: { lat: number; lng: number } | null;
  radiusMiles?: number;
  markers: MapMarker[];
  className?: string;
  activeMarkerId?: string | null;
  onMarkerHover?: (id: string | null) => void;
}

/**
 * Chromeless map variant that renders without the panel header bar and
 * fixed-height constraint. Fills its parent container. Intended for use
 * inside MapOverlayLayout as a full-bleed background.
 */
export function MapPanelChromeless({
  center,
  radiusMiles,
  markers,
  className,
  activeMarkerId,
  onMarkerHover
}: MapPanelChromelessProps): JSX.Element {
  const mapCenter = useMemo(() => center ?? {
    lat: MAP_BOUNDS.DEFAULT_CENTER[1],
    lng: MAP_BOUNDS.DEFAULT_CENTER[0]
  }, [center]);

  return (
    <div className={className ?? "h-full w-full"}>
      <Suspense fallback={<LoadingSkeleton lines={5} className="m-4" />}>
        <MapPanelMapLibre 
          center={mapCenter} 
          radiusMiles={radiusMiles}
          markers={markers} 
          activeMarkerId={activeMarkerId}
          onMarkerHover={onMarkerHover}
        />
      </Suspense>
    </div>
  );
}
